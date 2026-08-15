from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    rule_key: Mapped[str] = mapped_column(String(64), index=True)
    # low | medium | high | critical
    severity: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    related_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"), nullable=True
    )
    related_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    source: Mapped[str] = mapped_column(String(32))  # discovery | suricata | system
    # new | ack | resolved
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    raw_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
