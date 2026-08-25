"""Passive mDNS listener: picks up device hostnames from the standard
mDNS chatter devices already broadcast on the LAN (_http._tcp, _device-info,
_googlecast, _airplay, etc). Purely passive — we only listen, never probe."""

import logging

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

logger = logging.getLogger("netsentinel.collectors.discovery_mdns")

_COMMON_SERVICE_TYPES = [
    "_http._tcp.local.",
    "_device-info._tcp.local.",
    "_googlecast._tcp.local.",
    "_airplay._tcp.local.",
    "_ipp._tcp.local.",
    "_ssh._tcp.local.",
    "_smb._tcp.local.",
    "_workstation._tcp.local.",
]


class MdnsCollector:
    def __init__(self, on_hostname_found):
        """`on_hostname_found(ip: str, hostname: str)` callback, invoked
        synchronously from zeroconf's background thread."""
        self._on_hostname_found = on_hostname_found
        self._zc: Zeroconf | None = None
        self._browsers: list[ServiceBrowser] = []

    def start(self) -> None:
        try:
            self._zc = Zeroconf()
        except Exception:
            logger.exception("Failed to start mDNS listener")
            return

        def handler(zeroconf, service_type, name, state_change):
            if state_change is not ServiceStateChange.Added:
                return
            try:
                info = zeroconf.get_service_info(service_type, name, timeout=1000)
                if not info:
                    return
                hostname = name.split(".")[0]
                for addr in info.parsed_scoped_addresses():
                    self._on_hostname_found(addr, hostname)
            except Exception:
                logger.debug("mDNS resolve failed for %s", name, exc_info=True)

        self._browsers = [
            ServiceBrowser(self._zc, st, handlers=[handler]) for st in _COMMON_SERVICE_TYPES
        ]
        logger.info("mDNS passive listener started")

    def stop(self) -> None:
        if self._zc:
            self._zc.close()
