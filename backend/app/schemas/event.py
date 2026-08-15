from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SuricataEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    event_type: str
    severity: int | None
    signature: str | None
    category: str | None
    src_ip: str | None
    src_port: int | None
    dst_ip: str | None
    dst_port: int | None
    proto: str | None


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    src_ip: str
    src_port: int | None
    dst_ip: str
    dst_port: int | None
    proto: str
    app_proto: str | None
    bytes_in: int
    bytes_out: int
    packets: int
    duration_ms: int
