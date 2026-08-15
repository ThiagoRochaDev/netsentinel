from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mac_address: str
    vendor_oui: str | None
    custom_name: str | None
    hostname: str | None
    is_known: bool
    first_seen: datetime
    last_seen: datetime
    current_ip: str | None = None
    is_online: bool = False


class DevicePatch(BaseModel):
    custom_name: str | None = None
    is_known: bool | None = None


class DeviceSightingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str
    ssid: str | None
    method: str
    seen_at: datetime


class DevicePortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    port: int
    proto: str
    service_guess: str | None
    first_seen: datetime
    last_seen: datetime
