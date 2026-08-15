from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_username
from app.db import get_session, get_write_session
from app.models.alert import Alert
from app.schemas.alert import AlertOut, AlertPatch

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(get_current_username)])


@router.get("", response_model=list[AlertOut])
def list_alerts(status: str | None = None, severity: str | None = None, limit: int = 200):
    with get_session() as session:
        query = session.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            values = [v for v in severity.split(",") if v]
            query = query.filter(Alert.severity.in_(values)) if len(values) > 1 else query.filter(Alert.severity == values[0])
        return query.order_by(Alert.ts.desc()).limit(limit).all()


@router.get("/stats")
def alert_stats():
    with get_session() as session:
        alerts = session.query(Alert).all()
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for a in alerts:
        by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        by_status[a.status] = by_status.get(a.status, 0) + 1
    return {"total": len(alerts), "by_severity": by_severity, "by_status": by_status}


@router.patch("/{alert_id}", response_model=AlertOut)
def patch_alert(alert_id: int, payload: AlertPatch):
    if payload.status not in ("new", "ack", "resolved"):
        raise HTTPException(400, "Invalid status")
    with get_write_session() as session:
        alert = session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(404, "Alert not found")
        alert.status = payload.status
        session.flush()
        return AlertOut.model_validate(alert)
