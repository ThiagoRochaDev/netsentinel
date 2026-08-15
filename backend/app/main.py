import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.alert_engine.engine import seed_static_advisories
from app.alert_engine.rules import check_discovery_results, check_gateway_exposure
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.api.connections import router as connections_router
from app.api.devices import router as devices_router
from app.api.events import router as events_router
from app.api.scans import router as scans_router
from app.api.stats import router as stats_router
from app.api.ws import router as ws_router
from app.collectors.discovery_arp import discover_hosts, upsert_discovered_hosts
from app.collectors.discovery_mdns import MdnsCollector
from app.collectors.discovery_portscan import GATEWAY_CHECK_PORTS, detect_gateway_ip, scan_ports
from app.collectors.net_utils import detect_current_ssid, resolve_iface_and_cidr
from app.collectors.suricata_tail import SuricataTailer
from app.config import get_settings
from app.db import get_write_session, init_db
from app.models.device import Device
from app.models.user import User
from app.retention import run_retention_sweep
from app.ws_manager import ws_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netsentinel")

_mdns_collector: MdnsCollector | None = None
_discovery_task: asyncio.Task | None = None
_suricata_tailer: SuricataTailer | None = None
_suricata_task: asyncio.Task | None = None
_gateway_check_task: asyncio.Task | None = None
_retention_task: asyncio.Task | None = None

GATEWAY_CHECK_INTERVAL_SECONDS = 24 * 60 * 60


def seed_admin_user() -> None:
    settings = get_settings()
    with get_write_session() as session:
        existing = session.query(User).count()
        if existing == 0:
            session.add(
                User(
                    username=settings.admin_username,
                    password_hash=settings.admin_password_hash,
                )
            )
            logger.info("Seeded initial admin user %r", settings.admin_username)


def _on_mdns_hostname(ip: str, hostname: str) -> None:
    with get_write_session() as session:
        from app.models.sighting import DeviceSighting

        sighting = (
            session.query(DeviceSighting)
            .filter(DeviceSighting.ip_address == ip)
            .order_by(DeviceSighting.seen_at.desc())
            .first()
        )
        if sighting:
            device = session.query(Device).filter(Device.id == sighting.device_id).first()
            if device and not device.hostname:
                device.hostname = hostname


async def _discovery_loop() -> None:
    settings = get_settings()
    loop = asyncio.get_running_loop()
    while True:
        try:
            # Re-resolved every iteration (not once at startup): this host
            # can roam between networks (see scripts/wifi_cycle.sh), so
            # interface/CIDR/SSID must reflect whatever it's on *right now*.
            iface, cidr = resolve_iface_and_cidr(
                settings.netsentinel_iface, settings.netsentinel_lan_cidr
            )
            ssid = detect_current_ssid(iface) if iface else None
            if not cidr:
                logger.warning(
                    "Could not determine LAN CIDR to scan; passive discovery (ARP table) still runs."
                )
            else:
                logger.info("Discovery scan: interface=%s cidr=%s ssid=%s", iface, cidr, ssid)

            hosts = await loop.run_in_executor(None, discover_hosts, cidr)
            with get_write_session() as session:
                result = upsert_discovered_hosts(session, hosts, ssid=ssid)
                new_device_payloads = [
                    {"id": d.id, "mac_address": d.mac_address, "vendor_oui": d.vendor_oui}
                    for d in result.new_devices
                ]
            for payload in new_device_payloads:
                await ws_manager.broadcast("new_device", payload)
            await check_discovery_results(result)
        except Exception:
            logger.exception("Discovery loop iteration failed")
        await asyncio.sleep(settings.discovery_scan_interval_seconds)


async def _gateway_check_loop() -> None:
    loop = asyncio.get_running_loop()
    while True:
        try:
            gateway_ip = await loop.run_in_executor(None, detect_gateway_ip)
            if gateway_ip:
                ports_str = ",".join(str(p) for p in GATEWAY_CHECK_PORTS)
                open_ports = await loop.run_in_executor(None, scan_ports, gateway_ip, ports_str)
                await check_gateway_exposure(gateway_ip, open_ports)
        except Exception:
            logger.exception("Gateway exposure check failed")
        await asyncio.sleep(GATEWAY_CHECK_INTERVAL_SECONDS)


async def _retention_loop() -> None:
    settings = get_settings()
    loop = asyncio.get_running_loop()
    while True:
        try:
            await loop.run_in_executor(
                None,
                run_retention_sweep,
                settings.retention_days_events,
                settings.retention_days_connections,
                settings.retention_days_alerts,
            )
        except Exception:
            logger.exception("Retention sweep failed")
        await asyncio.sleep(settings.retention_sweep_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mdns_collector, _discovery_task, _suricata_tailer, _suricata_task, _gateway_check_task, _retention_task
    settings = get_settings()
    init_db()
    seed_admin_user()
    seed_static_advisories()

    _mdns_collector = MdnsCollector(on_hostname_found=_on_mdns_hostname)
    _mdns_collector.start()
    _discovery_task = asyncio.create_task(_discovery_loop())

    _suricata_tailer = SuricataTailer(
        eve_path=settings.suricata_eve_path,
        high_rate_threshold=settings.high_connection_rate_threshold,
        high_rate_window_s=settings.high_connection_rate_window_seconds,
        alert_severity_threshold=settings.suricata_alert_severity_threshold,
    )
    _suricata_task = _suricata_tailer.start()
    _gateway_check_task = asyncio.create_task(_gateway_check_loop())
    _retention_task = asyncio.create_task(_retention_loop())

    logger.info("NetSentinel backend starting up")
    yield

    if _discovery_task:
        _discovery_task.cancel()
    if _suricata_task:
        _suricata_task.cancel()
    if _gateway_check_task:
        _gateway_check_task.cancel()
    if _retention_task:
        _retention_task.cancel()
    if _suricata_tailer:
        _suricata_tailer.stop()
    if _mdns_collector:
        _mdns_collector.stop()
    logger.info("NetSentinel backend shutting down")


app = FastAPI(title="NetSentinel", lifespan=lifespan)

settings = get_settings()
if settings.netsentinel_env == "development":
    # Only needed when running the Vite dev server separately from the backend.
    # In production, nginx proxies /api and /ws same-origin, so this never applies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(alerts_router)
app.include_router(events_router)
app.include_router(connections_router)
app.include_router(stats_router)
app.include_router(scans_router)
app.include_router(ws_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
