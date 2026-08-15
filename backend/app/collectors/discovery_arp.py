"""LAN device discovery via ARP.

Two methods, both light and non-disruptive:
  - active_arp: sends standard ARP "who-has" requests to every address in the
    LAN CIDR (scapy). This is exactly what any device does when it wants to
    find another device on the same L2 segment — not a scan that probes
    ports or services, just "are you there".
  - passive_arp: reads the kernel's existing ARP/neighbor table (`ip neigh`),
    picking up devices this host has already talked to without sending
    anything new onto the network.

Deliberately does NOT touch other devices' traffic content — see
docs/PHASE1_SCOPE.md.
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("netsentinel.collectors.discovery_arp")


@dataclass
class DiscoveredHost:
    mac_address: str
    ip_address: str
    method: str


def active_arp_scan(cidr: str, timeout: float = 3.0) -> list[DiscoveredHost]:
    try:
        from scapy.all import ARP, Ether, srp
    except ImportError:
        logger.warning("scapy not available; skipping active ARP scan")
        return []

    try:
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=cidr)
        answered, _ = srp(request, timeout=timeout, verbose=False)
    except PermissionError:
        logger.error(
            "Active ARP scan needs CAP_NET_RAW/CAP_NET_ADMIN. "
            "Check the backend container's cap_add in docker-compose.yml."
        )
        return []
    except Exception:
        logger.exception("Active ARP scan failed")
        return []

    hosts: list[DiscoveredHost] = []
    for _, received in answered:
        hosts.append(
            DiscoveredHost(
                mac_address=received.hwsrc.upper(),
                ip_address=received.psrc,
                method="active_arp",
            )
        )
    return hosts


def passive_arp_table() -> list[DiscoveredHost]:
    try:
        out = subprocess.run(
            ["ip", "neigh", "show"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
    except Exception:
        logger.exception("Failed to read passive ARP/neighbor table")
        return []

    hosts: list[DiscoveredHost] = []
    for line in out.splitlines():
        # Format: "192.168.1.5 dev wlan0 lladdr aa:bb:cc:dd:ee:ff STALE"
        parts = line.split()
        if "lladdr" not in parts:
            continue
        ip = parts[0]
        mac = parts[parts.index("lladdr") + 1].upper()
        hosts.append(DiscoveredHost(mac_address=mac, ip_address=ip, method="passive_arp"))
    return hosts


def discover_hosts(cidr: str | None) -> list[DiscoveredHost]:
    hosts: dict[str, DiscoveredHost] = {}
    for h in passive_arp_table():
        hosts[h.mac_address] = h
    if cidr:
        for h in active_arp_scan(cidr):
            hosts[h.mac_address] = h  # active result wins (more current)
    return list(hosts.values())


@dataclass
class DiscoveryResult:
    new_devices: list  # list[Device]
    ip_changes: list  # list[tuple[Device, str | None, str]]  (device, old_ip, new_ip)


def upsert_discovered_hosts(session, hosts: list[DiscoveredHost], ssid: str | None = None) -> DiscoveryResult:
    """Writes discovered hosts into devices/device_sightings.
    Returns newly-created devices and IP changes for the alert engine."""
    from app.collectors.oui_lookup import lookup_vendor
    from app.models.device import Device
    from app.models.sighting import DeviceSighting

    now = datetime.now(timezone.utc)
    new_devices = []
    ip_changes = []

    for host in hosts:
        device = session.query(Device).filter(Device.mac_address == host.mac_address).first()
        if device is None:
            device = Device(
                mac_address=host.mac_address,
                vendor_oui=lookup_vendor(host.mac_address),
                first_seen=now,
                last_seen=now,
            )
            session.add(device)
            session.flush()  # get device.id
            new_devices.append(device)
        else:
            device.last_seen = now
            last_sighting = (
                session.query(DeviceSighting)
                .filter(DeviceSighting.device_id == device.id)
                .order_by(DeviceSighting.seen_at.desc())
                .first()
            )
            if last_sighting and last_sighting.ip_address != host.ip_address:
                ip_changes.append((device, last_sighting.ip_address, host.ip_address))

        session.add(
            DeviceSighting(
                device_id=device.id,
                ip_address=host.ip_address,
                ssid=ssid,
                method=host.method,
                seen_at=now,
            )
        )

    return DiscoveryResult(new_devices=new_devices, ip_changes=ip_changes)
