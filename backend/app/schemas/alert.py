from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    rule_key: str
    severity: str
    title: str
    description: str
    related_device_id: int | None
    related_ip: str | None
    source: str
    status: str


class AlertPatch(BaseModel):
    status: str  # ack | resolved
