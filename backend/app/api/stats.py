from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.auth.deps import get_current_username
from app.config import get_settings
from app.db import get_session
from app.models.alert import Alert
from app.models.connection import Connection
from app.models.device import Device
from app.models.sighting import DeviceSighting
from app.models.suricata_event import SuricataEvent

router = APIRouter(prefix="/api/stats", tags=["stats"], dependencies=[Depends(get_current_username)])

_METRIC_TABLES = {
    "connections": (Connection, Connection.ts),
    "suricata_events": (SuricataEvent, SuricataEvent.ts),
    "alerts": (Alert, Alert.ts),
    "device_sightings": (DeviceSighting, DeviceSighting.seen_at),
}


@router.get("/overview")
def overview():
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    with get_session() as session:
        total_devices = session.query(Device).count()
        online_devices = (
            session.query(Device)
            .filter(Device.last_seen >= now - timedelta(minutes=get_settings().device_online_threshold_minutes))
            .count()
        )
        new_alerts = session.query(Alert).filter(Alert.status == "new").count()
        high_severity_alerts = (
            session.query(Alert)
            .filter(Alert.status == "new", Alert.severity.in_(("high", "critical")))
            .count()
        )
        events_24h = session.query(SuricataEvent).filter(SuricataEvent.ts >= last_24h).count()
        connections_24h = session.query(Connection).filter(Connection.ts >= last_24h).count()

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "new_alerts": new_alerts,
        "high_severity_alerts": high_severity_alerts,
        "events_24h": events_24h,
        "connections_24h": connections_24h,
    }


@router.get("/timeseries")
def timeseries(metric: str = "connections", interval: str = "hour", range: str = "24h"):
    if metric not in _METRIC_TABLES:
        return {"error": f"unknown metric {metric!r}", "available": list(_METRIC_TABLES)}

    model, ts_col = _METRIC_TABLES[metric]
    range_hours = {"1h": 1, "24h": 24, "7d": 24 * 7, "30d": 24 * 30}.get(range, 24)
    since = datetime.now(timezone.utc) - timedelta(hours=range_hours)

    # SQLite bucketing via strftime; 'hour' or 'day' granularity.
    fmt = "%Y-%m-%d %H:00:00" if interval == "hour" else "%Y-%m-%d"
    bucket_expr = func.strftime(fmt, ts_col)

    with get_session() as session:
        rows = (
            session.query(bucket_expr.label("bucket"), func.count().label("count"))
            .filter(ts_col >= since)
            .group_by("bucket")
            .order_by("bucket")
            .all()
        )

    return {"metric": metric, "interval": interval, "points": [{"t": r.bucket, "v": r.count} for r in rows]}
