from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Connection(Base):
    """A flow record for THIS host's own traffic, sourced from Suricata flow events."""

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    src_ip: Mapped[str] = mapped_column(String(45), index=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str] = mapped_column(String(45), index=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proto: Mapped[str] = mapped_column(String(8))
    app_proto: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bytes_in: Mapped[int] = mapped_column(Integer, default=0)
    bytes_out: Mapped[int] = mapped_column(Integer, default=0)
    packets: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
