"""Phase 1 alert rules. Each function inspects freshly-collected data and
raises alerts via app.alert_engine.engine.raise_alert. See docs plan section
'Regras de alerta' for the full list; rules land here incrementally as their
data sources (discovery, Suricata) come online."""

import logging

from app.alert_engine.engine import raise_alert
from app.collectors.discovery_arp import DiscoveryResult

logger = logging.getLogger("netsentinel.alert_engine.rules")

# Ports that warrant a higher-severity alert when newly opened.
_HIGH_RISK_PORTS = {21: "FTP", 23: "Telnet", 3389: "RDP", 445: "SMB", 5900: "VNC"}

NEW_DEVICE_SPIKE_THRESHOLD = 4


async def check_discovery_results(result: DiscoveryResult) -> None:
    for device in result.new_devices:
        await raise_alert(
            rule_key="new_device_on_network",
            severity="medium",
            title=f"Novo dispositivo na rede: {device.mac_address}",
            description=(
                f"MAC {device.mac_address}"
                + (f" ({device.vendor_oui})" if device.vendor_oui else "")
                + " apareceu pela primeira vez na rede."
            ),
            source="discovery",
            related_device_id=device.id,
        )

    if len(result.new_devices) >= NEW_DEVICE_SPIKE_THRESHOLD:
        await raise_alert(
            rule_key="new_device_spike",
            severity="medium",
            title=f"{len(result.new_devices)} dispositivos novos de uma vez",
            description=(
                "Vários dispositivos desconhecidos apareceram na mesma varredura. "
                "Pode ser só gente comprando aparelho novo, mas vale conferir — "
                "também pode indicar um AP falso ou alguém tentando entrar na rede."
            ),
            source="discovery",
        )

    for device, old_ip, new_ip in result.ip_changes:
        await raise_alert(
            rule_key="device_ip_changed",
            severity="low",
            title=f"{device.custom_name or device.mac_address} mudou de IP",
            description=f"IP anterior {old_ip} -> novo IP {new_ip}.",
            source="discovery",
            related_device_id=device.id,
            related_ip=new_ip,
        )


async def check_gateway_exposure(gateway_ip: str, open_ports: list[dict]) -> None:
    risky = [p for p in open_ports if p["port"] in (23, 7547, 1900, 21)]
    if not risky:
        return
    labels = ", ".join(f"{p['port']}/{p['proto']} ({p.get('service_guess') or '?'})" for p in risky)
    await raise_alert(
        rule_key="gateway_admin_interface_exposed",
        severity="high",
        title="Roteador expõe serviços de risco na rede local",
        description=(
            f"O gateway ({gateway_ip}) tem portas potencialmente arriscadas abertas "
            f"para a rede local: {labels}. Vale conferir no painel do roteador se "
            "isso é esperado (ex.: UPnP ligado por um app específico) ou se dá pra desligar."
        ),
        source="discovery",
        related_ip=gateway_ip,
    )


async def check_new_port(device, port: int, proto: str, service_guess: str | None) -> None:
    high_risk = _HIGH_RISK_PORTS.get(port)
    severity = "high" if high_risk else "info"
    label = f"{high_risk} ({port}/{proto})" if high_risk else f"{port}/{proto}"
    await raise_alert(
        rule_key="device_port_newly_opened",
        severity=severity,
        title=f"Nova porta aberta em {device.custom_name or device.mac_address}: {label}",
        description=(
            f"Porta {port}/{proto}"
            + (f" ({service_guess})" if service_guess else "")
            + f" apareceu aberta no dispositivo {device.mac_address}."
        ),
        source="discovery",
        related_device_id=device.id,
    )
