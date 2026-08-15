"""Opt-in, manually-triggered port scanning. Never runs automatically against
arbitrary devices — only the gateway gets a light, scheduled check (a handful
of ports, once a day) since that's the single device every packet on the LAN
already has to trust. See docs/PHASE1_SCOPE.md: this is still "my own
equipment", scanned lightly and deliberately, not a sweep of the whole LAN.
"""

import logging
import subprocess

logger = logging.getLogger("netsentinel.collectors.discovery_portscan")

TOP_PORTS = "1-1024,1900,3389,5900,7547,8080,8443"
GATEWAY_CHECK_PORTS = [21, 23, 80, 443, 1900, 7547, 8080]

_KNOWN_SERVICE_NAMES = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    443: "https",
    445: "smb",
    1900: "upnp",
    3389: "rdp",
    5900: "vnc",
    7547: "tr-069 (cwmp)",
    8080: "http-alt",
    8443: "https-alt",
}


def scan_ports(ip: str, ports: str = TOP_PORTS, timing: str = "-T2") -> list[dict]:
    """Blocking. Call via loop.run_in_executor. Requires the `nmap` binary
    and CAP_NET_RAW (see docker-compose.yml cap_add for the backend service)."""
    try:
        import nmap
    except ImportError:
        logger.warning("python-nmap not available; skipping port scan")
        return []

    scanner = nmap.PortScanner()
    try:
        scanner.scan(hosts=ip, ports=ports, arguments=f"{timing} -sT --max-retries 1")
    except Exception:
        logger.exception("Port scan of %s failed", ip)
        return []

    results = []
    if ip not in scanner.all_hosts():
        return results

    for proto in scanner[ip].all_protocols():
        for port, info in scanner[ip][proto].items():
            if info.get("state") == "open":
                results.append(
                    {
                        "port": port,
                        "proto": proto,
                        "service_guess": info.get("name") or _KNOWN_SERVICE_NAMES.get(port),
                    }
                )
    return results


def detect_gateway_ip() -> str | None:
    try:
        out = subprocess.run(
            ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5, check=True
        ).stdout
        parts = out.split()
        if "via" in parts:
            return parts[parts.index("via") + 1]
    except Exception:
        logger.exception("Failed to detect gateway IP")
    return None
