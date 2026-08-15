"""Small helpers to auto-detect the active network interface and LAN CIDR,
so the user doesn't have to hardcode them in .env."""

import ipaddress
import logging
import subprocess

logger = logging.getLogger("netsentinel.collectors.net_utils")


def detect_default_interface() -> str | None:
    try:
        out = subprocess.run(
            ["ip", "-j", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
        import json

        routes = json.loads(out)
        if routes:
            return routes[0].get("dev")
    except Exception:
        logger.exception("Failed to auto-detect default interface")
    return None


def detect_cidr_for_interface(iface: str) -> str | None:
    try:
        out = subprocess.run(
            ["ip", "-j", "-4", "addr", "show", "dev", iface],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
        import json

        data = json.loads(out)
        for entry in data:
            for addr_info in entry.get("addr_info", []):
                if addr_info.get("family") == "inet":
                    ip = addr_info["local"]
                    prefixlen = addr_info["prefixlen"]
                    network = ipaddress.ip_network(f"{ip}/{prefixlen}", strict=False)
                    return str(network)
    except Exception:
        logger.exception("Failed to auto-detect CIDR for interface %s", iface)
    return None


def detect_current_ssid(iface: str) -> str | None:
    """Wi-Fi SSID the interface is currently associated with, or None on
    Ethernet / if not associated. Used to tag device sightings so the
    dashboard can tell which network (e.g. primary vs secondary band) a device was seen on
    when the host itself roams between networks — see
    scripts/wifi_cycle.sh."""
    try:
        out = subprocess.run(
            ["iw", "dev", iface, "link"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
    except Exception:
        return None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("SSID:"):
            return line.removeprefix("SSID:").strip()
    return None


def resolve_iface_and_cidr(configured_iface: str, configured_cidr: str) -> tuple[str | None, str | None]:
    """Always prefers a fresh, live-detected CIDR over the .env value: this
    host's interface can roam between networks (see scripts/wifi_cycle.sh),
    so a CIDR cached from .env would silently scan the wrong subnet after a
    switch. `configured_cidr` is only a fallback for when live detection
    fails (e.g. interface momentarily down)."""
    iface = configured_iface or detect_default_interface()
    cidr = detect_cidr_for_interface(iface) if iface else None
    if not cidr:
        cidr = configured_cidr
    return iface, cidr
