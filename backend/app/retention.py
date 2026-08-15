"""Prunes old rows so the SQLite file doesn't grow without bound — matters
most on a Raspberry Pi's SD card. Alerts are kept much longer than raw
events/connections since they're the summarized, human-relevant record."""

import logging
from datetime import datetime, timedelta, timezone

from app.db import get_write_session
from app.models.connection import Connection
from app.models.suricata_event import SuricataEvent
from app.models.alert import Alert

logger = logging.getLogger("netsentinel.retention")


def run_retention_sweep(
    retention_days_events: int,
    retention_days_connections: int,
    retention_days_alerts: int,
) -> None:
    now = datetime.now(timezone.utc)

    with get_write_session() as session:
        events_cutoff = now - timedelta(days=retention_days_events)
        deleted_events = (
            session.query(SuricataEvent).filter(SuricataEvent.ts < events_cutoff).delete()
        )

        connections_cutoff = now - timedelta(days=retention_days_connections)
        deleted_connections = (
            session.query(Connection).filter(Connection.ts < connections_cutoff).delete()
        )

        alerts_cutoff = now - timedelta(days=retention_days_alerts)
        deleted_alerts = (
            session.query(Alert)
            .filter(Alert.ts < alerts_cutoff, Alert.status == "resolved")
            .delete()
        )

    if deleted_events or deleted_connections or deleted_alerts:
        logger.info(
            "Retention sweep: removed %d events, %d connections, %d resolved alerts",
            deleted_events,
            deleted_connections,
            deleted_alerts,
        )
