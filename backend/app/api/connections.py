from datetime import datetime

from fastapi import APIRouter, Depends

from app.auth.deps import get_current_username
from app.db import get_session
from app.models.connection import Connection
from app.schemas.event import ConnectionOut

router = APIRouter(prefix="/api/connections", tags=["connections"], dependencies=[Depends(get_current_username)])


@router.get("", response_model=list[ConnectionOut])
def list_connections(
    src_ip: str | None = None,
    dst_ip: str | None = None,
    proto: str | None = None,
    since: datetime | None = None,
    limit: int = 200,
):
    with get_session() as session:
        query = session.query(Connection)
        if src_ip:
            query = query.filter(Connection.src_ip == src_ip)
        if dst_ip:
            query = query.filter(Connection.dst_ip == dst_ip)
        if proto:
            query = query.filter(Connection.proto == proto)
        if since:
            query = query.filter(Connection.ts >= since)
        return query.order_by(Connection.ts.desc()).limit(min(limit, 1000)).all()


@router.get("/stats")
def connection_stats():
    with get_session() as session:
        rows = session.query(Connection).order_by(Connection.ts.desc()).limit(2000).all()
    top_talkers: dict[str, int] = {}
    protocols: dict[str, int] = {}
    total_bytes = 0
    for c in rows:
        top_talkers[c.dst_ip] = top_talkers.get(c.dst_ip, 0) + c.bytes_in + c.bytes_out
        protocols[c.proto] = protocols.get(c.proto, 0) + 1
        total_bytes += c.bytes_in + c.bytes_out
    top = sorted(top_talkers.items(), key=lambda kv: kv[1], reverse=True)[:10]
    return {
        "total_bytes": total_bytes,
        "top_talkers": [{"ip": ip, "bytes": b} for ip, b in top],
        "protocols": protocols,
    }
