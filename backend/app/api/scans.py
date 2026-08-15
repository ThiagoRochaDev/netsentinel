import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.alert_engine.rules import check_discovery_results, check_new_port
from app.auth.deps import get_current_username
from app.collectors.discovery_arp import discover_hosts, upsert_discovered_hosts
from app.collectors.discovery_portscan import scan_ports
from app.collectors.net_utils import detect_current_ssid, resolve_iface_and_cidr
from app.config import get_settings
from app.db import get_session, get_write_session
from app.models.device import Device, DevicePort

logger = logging.getLogger("netsentinel.api.scans")

router = APIRouter(prefix="/api/scans", tags=["scans"], dependencies=[Depends(get_current_username)])

PORTSCAN_COOLDOWN_SECONDS = 300
_last_portscan_at: dict[int, float] = {}
_last_discovery_at: float | None = None


@router.post("/discovery")
async def trigger_discovery():
    global _last_discovery_at
    settings = get_settings()
    iface, cidr = resolve_iface_and_cidr(settings.netsentinel_iface, settings.netsentinel_lan_cidr)
    ssid = detect_current_ssid(iface) if iface else None

    loop = asyncio.get_running_loop()
    hosts = await loop.run_in_executor(None, discover_hosts, cidr)
    with get_write_session() as session:
        result = upsert_discovered_hosts(session, hosts, ssid=ssid)
    await check_discovery_results(result)
    _last_discovery_at = time.monotonic()
    return {"discovered": len(hosts), "new_devices": len(result.new_devices)}


@router.post("/portscan/{device_id}")
async def trigger_portscan(device_id: int):
    now = time.monotonic()
    last = _last_portscan_at.get(device_id)
    if last and (now - last) < PORTSCAN_COOLDOWN_SECONDS:
        remaining = int(PORTSCAN_COOLDOWN_SECONDS - (now - last))
        raise HTTPException(429, f"Aguarde {remaining}s antes de escanear este dispositivo de novo.")

    with get_session() as session:
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(404, "Device not found")
        from app.models.sighting import DeviceSighting

        latest = (
            session.query(DeviceSighting)
            .filter(DeviceSighting.device_id == device_id)
            .order_by(DeviceSighting.seen_at.desc())
            .first()
        )
        if not latest:
            raise HTTPException(400, "No known IP for this device yet")
        ip = latest.ip_address

    _last_portscan_at[device_id] = now
    loop = asyncio.get_running_loop()
    found = await loop.run_in_executor(None, scan_ports, ip)

    new_ports = []
    with get_write_session() as session:
        existing = {
            (p.port, p.proto) for p in session.query(DevicePort).filter(DevicePort.device_id == device_id)
        }
        for item in found:
            key = (item["port"], item["proto"])
            if key not in existing:
                session.add(
                    DevicePort(
                        device_id=device_id,
                        port=item["port"],
                        proto=item["proto"],
                        service_guess=item.get("service_guess"),
                    )
                )
                new_ports.append(item)

    device_for_alert = device
    for item in new_ports:
        await check_new_port(device_for_alert, item["port"], item["proto"], item.get("service_guess"))

    return {"device_id": device_id, "open_ports": found, "newly_opened": new_ports}


@router.get("/status")
def scan_status():
    return {
        "last_discovery_seconds_ago": (time.monotonic() - _last_discovery_at) if _last_discovery_at else None,
        "portscan_cooldown_seconds": PORTSCAN_COOLDOWN_SECONDS,
        "devices_recently_scanned": len(_last_portscan_at),
    }
