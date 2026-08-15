from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_username
from app.config import get_settings
from app.db import get_session, get_write_session
from app.models.device import Device, DevicePort
from app.models.sighting import DeviceSighting
from app.schemas.device import DeviceOut, DevicePatch, DevicePortOut, DeviceSightingOut

router = APIRouter(prefix="/api/devices", tags=["devices"], dependencies=[Depends(get_current_username)])


def _online_cutoff() -> datetime:
    # Device.last_seen is stored as a naive UTC datetime (column has no
    # timezone=True), so the cutoff must be naive too or Python's datetime
    # comparison raises TypeError.
    threshold = get_settings().device_online_threshold_minutes
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=threshold)


@router.get("", response_model=list[DeviceOut])
def list_devices(online: bool | None = None):
    cutoff = _online_cutoff()
    with get_session() as session:
        devices = session.query(Device).order_by(Device.last_seen.desc()).all()
        out = []
        for d in devices:
            is_online = d.last_seen >= cutoff
            if online is not None and is_online != online:
                continue
            latest = (
                session.query(DeviceSighting)
                .filter(DeviceSighting.device_id == d.id)
                .order_by(DeviceSighting.seen_at.desc())
                .first()
            )
            item = DeviceOut.model_validate(d)
            item.current_ip = latest.ip_address if latest else None
            item.is_online = is_online
            out.append(item)
        return out


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int):
    with get_session() as session:
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(404, "Device not found")
        latest = (
            session.query(DeviceSighting)
            .filter(DeviceSighting.device_id == device.id)
            .order_by(DeviceSighting.seen_at.desc())
            .first()
        )
        item = DeviceOut.model_validate(device)
        item.current_ip = latest.ip_address if latest else None
        item.is_online = device.last_seen >= _online_cutoff()
        return item


@router.patch("/{device_id}", response_model=DeviceOut)
def patch_device(device_id: int, payload: DevicePatch):
    with get_write_session() as session:
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(404, "Device not found")
        if payload.custom_name is not None:
            device.custom_name = payload.custom_name
        if payload.is_known is not None:
            device.is_known = payload.is_known
        session.flush()
        return DeviceOut.model_validate(device)


@router.get("/{device_id}/sightings", response_model=list[DeviceSightingOut])
def device_sightings(device_id: int, limit: int = 100):
    with get_session() as session:
        rows = (
            session.query(DeviceSighting)
            .filter(DeviceSighting.device_id == device_id)
            .order_by(DeviceSighting.seen_at.desc())
            .limit(limit)
            .all()
        )
        return rows


@router.get("/{device_id}/ports", response_model=list[DevicePortOut])
def device_ports(device_id: int):
    with get_session() as session:
        rows = session.query(DevicePort).filter(DevicePort.device_id == device_id).all()
        return rows
