from datetime import datetime

from fastapi import APIRouter, Depends

from app.auth.deps import get_current_username
from app.db import get_session
from app.models.suricata_event import SuricataEvent
from app.schemas.event import SuricataEventOut

router = APIRouter(prefix="/api/events", tags=["events"], dependencies=[Depends(get_current_username)])


@router.get("", response_model=list[SuricataEventOut])
def list_events(
    event_type: str | None = None,
    severity: int | None = None,
    search: str | None = None,
    since: datetime | None = None,
    limit: int = 200,
):
    with get_session() as session:
        query = session.query(SuricataEvent)
        if event_type:
            query = query.filter(SuricataEvent.event_type == event_type)
        if severity is not None:
            query = query.filter(SuricataEvent.severity <= severity)
        if since:
            query = query.filter(SuricataEvent.ts >= since)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (SuricataEvent.signature.like(like))
                | (SuricataEvent.src_ip.like(like))
                | (SuricataEvent.dst_ip.like(like))
            )
        return query.order_by(SuricataEvent.ts.desc()).limit(min(limit, 1000)).all()
