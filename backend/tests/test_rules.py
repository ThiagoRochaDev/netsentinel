import pytest

from app.alert_engine.rules import (
    NEW_DEVICE_SPIKE_THRESHOLD,
    check_discovery_results,
    check_gateway_exposure,
    check_new_port,
)
from app.collectors.discovery_arp import DiscoveryResult
from app.db import get_session, get_write_session
from app.models.alert import Alert
from app.models.device import Device


def _make_device(mac: str) -> Device:
    with get_write_session() as session:
        device = Device(mac_address=mac, vendor_oui="Acme Corp")
        session.add(device)
        session.flush()
        session.refresh(device)
        session.expunge(device)
    return device


def _alert_count(rule_key: str) -> int:
    with get_session() as session:
        return session.query(Alert).filter(Alert.rule_key == rule_key).count()


@pytest.mark.asyncio
async def test_new_device_raises_alert():
    device = _make_device("AA:BB:CC:DD:EE:01")
    result = DiscoveryResult(new_devices=[device], ip_changes=[])

    await check_discovery_results(result)

    assert _alert_count("new_device_on_network") == 1
    assert _alert_count("new_device_spike") == 0  # só 1 dispositivo, abaixo do threshold


@pytest.mark.asyncio
async def test_new_device_spike_raises_extra_alert():
    devices = [_make_device(f"AA:BB:CC:DD:EE:{i:02d}") for i in range(NEW_DEVICE_SPIKE_THRESHOLD)]
    result = DiscoveryResult(new_devices=devices, ip_changes=[])

    await check_discovery_results(result)

    assert _alert_count("new_device_on_network") == NEW_DEVICE_SPIKE_THRESHOLD
    assert _alert_count("new_device_spike") == 1


@pytest.mark.asyncio
async def test_ip_change_raises_low_severity_alert():
    device = _make_device("AA:BB:CC:DD:EE:02")
    result = DiscoveryResult(new_devices=[], ip_changes=[(device, "192.168.1.5", "192.168.1.9")])

    await check_discovery_results(result)

    with get_session() as session:
        alert = session.query(Alert).filter(Alert.rule_key == "device_ip_changed").first()
    assert alert is not None
    assert alert.severity == "low"
    assert "192.168.1.5" in alert.description
    assert "192.168.1.9" in alert.description


@pytest.mark.asyncio
async def test_high_risk_port_raises_high_severity():
    device = _make_device("AA:BB:CC:DD:EE:03")

    await check_new_port(device, port=23, proto="tcp", service_guess="telnet")

    with get_session() as session:
        alert = session.query(Alert).filter(Alert.rule_key == "device_port_newly_opened").first()
    assert alert is not None
    assert alert.severity == "high"
    assert "Telnet" in alert.title


@pytest.mark.asyncio
async def test_low_risk_port_raises_info_severity():
    device = _make_device("AA:BB:CC:DD:EE:04")

    await check_new_port(device, port=8080, proto="tcp", service_guess="http-alt")

    with get_session() as session:
        alert = session.query(Alert).filter(Alert.rule_key == "device_port_newly_opened").first()
    assert alert is not None
    assert alert.severity == "info"


@pytest.mark.asyncio
async def test_gateway_exposure_ignores_safe_ports():
    await check_gateway_exposure("192.168.1.1", [{"port": 80, "proto": "tcp", "service_guess": "http"}])
    assert _alert_count("gateway_admin_interface_exposed") == 0


@pytest.mark.asyncio
async def test_gateway_exposure_flags_risky_port():
    await check_gateway_exposure(
        "192.168.1.1", [{"port": 23, "proto": "tcp", "service_guess": "telnet"}]
    )
    assert _alert_count("gateway_admin_interface_exposed") == 1
