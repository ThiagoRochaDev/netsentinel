"""Tails Suricata's eve.json and feeds it into the app's data model.

Runs the actual file-tailing (blocking I/O, needs to survive log rotation)
in a background OS thread, and hands parsed JSON events over to the asyncio
event loop via a thread-safe queue so DB writes / alert raising can use the
same async code path as everything else.
"""

import asyncio
import json
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger("netsentinel.collectors.suricata_tail")


def _blocking_tail(path: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue, stop_event: threading.Event):
    """Runs in a dedicated thread. Handles the file not existing yet and
    rotation (Suricata replaces eve.json with a fresh, smaller file — a
    shrink or inode change means "start over from the top")."""
    fh = None
    last_inode = None

    while not stop_event.is_set():
        try:
            if fh is None:
                if not os.path.exists(path):
                    time.sleep(2)
                    continue
                fh = open(path, "r")
                fh.seek(0, os.SEEK_END)
                last_inode = os.fstat(fh.fileno()).st_ino

            try:
                current_inode = os.stat(path).st_ino
            except FileNotFoundError:
                current_inode = None

            if current_inode != last_inode:
                fh.close()
                fh = None
                continue

            line = fh.readline()
            if not line:
                time.sleep(0.5)
                continue

            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            asyncio.run_coroutine_threadsafe(queue.put(event), loop)
        except Exception:
            logger.exception("suricata_tail thread error; retrying in 2s")
            if fh:
                fh.close()
            fh = None
            time.sleep(2)

    if fh:
        fh.close()


def _parse_ts(event: dict) -> datetime:
    raw = event.get("timestamp")
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


class SuricataTailer:
    def __init__(self, eve_path: str, high_rate_threshold: int, high_rate_window_s: int, alert_severity_threshold: int):
        self.eve_path = eve_path
        self.high_rate_threshold = high_rate_threshold
        self.high_rate_window_s = high_rate_window_s
        self.alert_severity_threshold = alert_severity_threshold
        self._queue: asyncio.Queue = asyncio.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._recent_flow_timestamps: deque[float] = deque()
        self._rate_alert_cooldown_until: float = 0.0
        self._dns_nxdomain_window: deque[float] = deque()
        self._dns_alert_cooldown_until: float = 0.0
        self._alert_dedup_seen: dict[tuple, float] = {}
        self._alert_dedup_window_s: float = 300.0

    def start(self) -> asyncio.Task:
        loop = asyncio.get_running_loop()
        self._thread = threading.Thread(
            target=_blocking_tail,
            args=(self.eve_path, loop, self._queue, self._stop_event),
            daemon=True,
        )
        self._thread.start()
        return asyncio.create_task(self._consume_loop())

    def stop(self) -> None:
        self._stop_event.set()

    async def _consume_loop(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                await self._handle_event(event)
            except Exception:
                logger.exception("Failed to handle suricata event")

    async def _handle_event(self, event: dict) -> None:
        from app.db import get_write_session
        from app.models.connection import Connection
        from app.models.suricata_event import SuricataEvent

        event_type = event.get("event_type")
        ts = _parse_ts(event)

        from app.ws_manager import ws_manager

        if event_type == "flow":
            flow = event.get("flow", {})
            bytes_in = flow.get("bytes_toclient", 0)
            bytes_out = flow.get("bytes_toserver", 0)
            with get_write_session() as session:
                session.add(
                    Connection(
                        ts=ts,
                        src_ip=event.get("src_ip", ""),
                        src_port=event.get("src_port"),
                        dst_ip=event.get("dest_ip", ""),
                        dst_port=event.get("dest_port"),
                        proto=event.get("proto", ""),
                        app_proto=event.get("app_proto"),
                        bytes_in=bytes_in,
                        bytes_out=bytes_out,
                        packets=flow.get("pkts_toserver", 0) + flow.get("pkts_toclient", 0),
                        duration_ms=int(
                            (
                                _parse_ts({"timestamp": flow.get("end")}) - _parse_ts({"timestamp": flow.get("start")})
                            ).total_seconds()
                            * 1000
                        )
                        if flow.get("start") and flow.get("end")
                        else 0,
                    )
                )
            await ws_manager.broadcast(
                "flow_tick",
                {
                    "src_ip": event.get("src_ip"),
                    "dst_ip": event.get("dest_ip"),
                    "proto": event.get("proto"),
                    "app_proto": event.get("app_proto"),
                    "bytes": bytes_in + bytes_out,
                },
            )
            await self._check_connection_rate()
            return

        if event_type in ("alert", "dns", "http", "tls", "ssh"):
            alert = event.get("alert", {})
            with get_write_session() as session:
                session.add(
                    SuricataEvent(
                        ts=ts,
                        event_type=event_type,
                        severity=alert.get("severity"),
                        signature=alert.get("signature"),
                        category=alert.get("category"),
                        src_ip=event.get("src_ip"),
                        src_port=event.get("src_port"),
                        dst_ip=event.get("dest_ip"),
                        dst_port=event.get("dest_port"),
                        proto=event.get("proto"),
                        raw_json=json.dumps(event),
                    )
                )
            await ws_manager.broadcast(
                "suricata_event",
                {
                    "event_type": event_type,
                    "signature": alert.get("signature"),
                    "src_ip": event.get("src_ip"),
                    "dst_ip": event.get("dest_ip"),
                },
            )

            if event_type == "alert":
                await self._maybe_raise_passthrough(event, alert)
            elif event_type == "dns":
                await self._check_dns_burst(event)

    async def _check_connection_rate(self) -> None:
        from app.alert_engine.engine import raise_alert

        now = time.monotonic()
        self._recent_flow_timestamps.append(now)
        window_start = now - self.high_rate_window_s
        while self._recent_flow_timestamps and self._recent_flow_timestamps[0] < window_start:
            self._recent_flow_timestamps.popleft()

        if len(self._recent_flow_timestamps) < self.high_rate_threshold:
            return
        if now < self._rate_alert_cooldown_until:
            return

        self._rate_alert_cooldown_until = now + self.high_rate_window_s
        await raise_alert(
            rule_key="high_connection_rate_from_host",
            severity="medium",
            title="Volume alto de conexões saindo desta máquina",
            description=(
                f"Mais de {self.high_rate_threshold} conexões em "
                f"{self.high_rate_window_s}s. Pode ser uso normal (streaming, "
                "downloads), mas também pode indicar malware/exfiltração — vale conferir."
            ),
            source="suricata",
        )

    async def _check_dns_burst(self, event: dict) -> None:
        from app.alert_engine.engine import raise_alert

        dns = event.get("dns", {})
        rcode = dns.get("rcode") or dns.get("answers", [{}])[0].get("rcode") if dns.get("answers") else dns.get("rcode")
        if rcode != "NXDOMAIN":
            return

        now = time.monotonic()
        self._dns_nxdomain_window.append(now)
        window_start = now - 60
        while self._dns_nxdomain_window and self._dns_nxdomain_window[0] < window_start:
            self._dns_nxdomain_window.popleft()

        if len(self._dns_nxdomain_window) < 20:
            return
        if now < self._dns_alert_cooldown_until:
            return

        self._dns_alert_cooldown_until = now + 60
        await raise_alert(
            rule_key="suspicious_dns_burst",
            severity="medium",
            title="Rajada de consultas DNS sem resposta (NXDOMAIN)",
            description=(
                "Muitas consultas DNS falhando em pouco tempo nesta máquina. "
                "Pode indicar malware tentando contatar um servidor de comando "
                "e controle, ou só um app com bug — vale investigar."
            ),
            source="suricata",
        )

    def _is_engine_noise(self, alert: dict) -> bool:
        """Suricata's own decoder/stream-anomaly signatures (category
        "Generic Protocol Command Decode") report internal engine quirks —
        e.g. "QUIC failed decrypt" fires on nearly every modern HTTPS/QUIC
        connection because Suricata has no TLS keys, and "STREAM pkt seen
        on wrong thread" is a load-balancing artifact — neither indicates
        an actual threat. Promoting these to platform alerts is what
        flooded the dashboard with ~9k near-duplicate alerts in practice."""
        return alert.get("category") == "Generic Protocol Command Decode"

    def _is_alert_rate_limited(self, alert: dict, event: dict) -> bool:
        """Defense in depth beyond the noise filter above: caps any single
        signature+source pair to one platform alert per cooldown window, so
        a new chatty signature we haven't explicitly blocklisted can't
        repeat-flood the dashboard/WebSocket the same way."""
        key = (alert.get("signature"), event.get("src_ip"))
        now = time.monotonic()
        last = self._alert_dedup_seen.get(key)
        self._alert_dedup_seen[key] = now

        if len(self._alert_dedup_seen) > 5000:
            cutoff = now - self._alert_dedup_window_s
            self._alert_dedup_seen = {
                k: v for k, v in self._alert_dedup_seen.items() if v >= cutoff
            }

        return last is not None and (now - last) < self._alert_dedup_window_s

    async def _maybe_raise_passthrough(self, event: dict, alert: dict) -> None:
        from app.alert_engine.engine import raise_alert

        severity_num = alert.get("severity", 3)
        if severity_num > self.alert_severity_threshold:
            return
        if self._is_engine_noise(alert):
            return
        if self._is_alert_rate_limited(alert, event):
            return

        severity_label = {1: "critical", 2: "high", 3: "medium"}.get(severity_num, "low")
        await raise_alert(
            rule_key="suricata_alert_passthrough",
            severity=severity_label,
            title=alert.get("signature", "Alerta do Suricata"),
            description=(
                f"Categoria: {alert.get('category', 'desconhecida')}. "
                f"{event.get('src_ip', '?')}:{event.get('src_port', '?')} -> "
                f"{event.get('dest_ip', '?')}:{event.get('dest_port', '?')} ({event.get('proto', '?')})"
            ),
            source="suricata",
            related_ip=event.get("src_ip"),
            raw_ref=json.dumps(event),
        )
