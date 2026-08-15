"""One-off script to populate the DB with fictional demo data for
screenshots/documentation. Not part of the app, never imported at runtime.

    docker compose exec backend python -m app.seed_demo
"""

import random
from datetime import datetime, timedelta, timezone

from app.db import get_write_session
from app.models.alert import Alert
from app.models.connection import Connection
from app.models.device import Device, DevicePort
from app.models.sighting import DeviceSighting

now = datetime.now(timezone.utc)

DEVICES = [
    ("aa:11:22:33:44:01", "Apple, Inc.", "Living-Room-TV", "192.168.50.10", True, [(8009, "tcp", "chromecast")]),
    ("aa:11:22:33:44:02", "Espressif Inc.", "Kitchen-Smart-Plug", "192.168.50.14", True, [(80, "tcp", "http")]),
    ("aa:11:22:33:44:03", "Samsung Electronics", "Guest-Phone", "192.168.50.22", False, []),
    ("aa:11:22:33:44:04", "TP-Link Corporation", "Office-Printer", "192.168.50.30", True, [(9100, "tcp", "jetdirect"), (631, "tcp", "ipp")]),
    ("aa:11:22:33:44:05", "Raspberry Pi Foundation", "netsentinel-pi", "192.168.50.2", True, [(22, "tcp", "ssh"), (80, "tcp", "http")]),
    ("aa:11:22:33:44:06", "Amazon Technologies", "Echo-Dot-Bedroom", "192.168.50.41", True, [(443, "tcp", "https")]),
    ("aa:11:22:33:44:07", "Unknown", "unknown-device", "192.168.50.87", False, [(23, "tcp", "telnet")]),
    ("aa:11:22:33:44:08", "Dell Inc.", "Home-Office-Notebook", "192.168.50.15", True, [(22, "tcp", "ssh")]),
]

ALERTS = [
    ("new_device_on_network", "medium", "Novo dispositivo na rede: aa:11:22:33:44:07",
     "Um dispositivo com MAC aa:11:22:33:44:07 (vendor: Unknown) apareceu pela primeira vez na LAN.",
     "192.168.50.87", "discovery"),
    ("device_port_newly_opened", "high", "Porta Telnet (23) aberta em unknown-device",
     "O dispositivo 192.168.50.87 passou a expor a porta 23/tcp (telnet), historicamente associada a firmwares IoT vulneráveis.",
     "192.168.50.87", "discovery"),
    ("gateway_admin_interface_exposed", "medium", "Interface administrativa do gateway exposta na LAN",
     "A interface de administração do roteador está acessível via HTTP simples na rede local.",
     "192.168.50.1", "discovery"),
    ("new_device_spike", "low", "Pico de novos dispositivos na rede",
     "3 dispositivos novos foram descobertos em menos de 10 minutos — pode ser normal (visitas) ou merecer atenção.",
     None, "discovery"),
    ("device_ip_changed", "low", "IP do Home-Office-Notebook mudou",
     "O dispositivo aa:11:22:33:44:08 estava em 192.168.50.16 e passou a responder em 192.168.50.15.",
     "192.168.50.15", "discovery"),
]

with get_write_session() as session:
    device_ids = {}
    for mac, vendor, hostname, ip, known, ports in DEVICES:
        first_seen = now - timedelta(days=random.randint(1, 45))
        d = Device(
            mac_address=mac,
            vendor_oui=vendor,
            hostname=hostname,
            is_known=known,
            first_seen=first_seen,
            last_seen=now - timedelta(minutes=random.randint(0, 120)),
        )
        session.add(d)
        session.flush()
        device_ids[mac] = d.id

        session.add(DeviceSighting(
            device_id=d.id, ip_address=ip, ssid=None,
            method=random.choice(["passive_arp", "active_arp", "mdns"]),
            seen_at=now - timedelta(minutes=random.randint(0, 60)),
        ))
        for port, proto, guess in ports:
            session.add(DevicePort(
                device_id=d.id, port=port, proto=proto, service_guess=guess,
                first_seen=first_seen, last_seen=now,
            ))

    for rule_key, severity, title, desc, ip, source in ALERTS:
        session.add(Alert(
            ts=now - timedelta(minutes=random.randint(1, 600)),
            rule_key=rule_key, severity=severity, title=title, description=desc,
            related_ip=ip, source=source, status="new",
        ))

    dsts = ["142.250.65.14", "104.16.132.229", "13.107.42.14", "151.101.65.69"]
    for _ in range(60):
        session.add(Connection(
            ts=now - timedelta(minutes=random.randint(0, 720)),
            src_ip="192.168.50.2", src_port=random.randint(30000, 60000),
            dst_ip=random.choice(dsts), dst_port=random.choice([443, 443, 443, 80]),
            proto="tcp", app_proto=random.choice(["tls", "http", "quic"]),
            bytes_in=random.randint(2_000, 900_000),
            bytes_out=random.randint(500, 60_000),
            packets=random.randint(5, 400),
            duration_ms=random.randint(20, 15_000),
        ))

print(f"Seeded {len(DEVICES)} devices, {len(ALERTS)} alerts, 60 connections.")
