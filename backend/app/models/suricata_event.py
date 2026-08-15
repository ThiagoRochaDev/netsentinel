from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SuricataEvent(Base):
    __tablename__ = "suricata_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proto: Mapped[str | None] = mapped_column(String(8), nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)
