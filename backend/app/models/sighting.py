from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DeviceSighting(Base):
    __tablename__ = "device_sightings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    ip_address: Mapped[str] = mapped_column(String(45))
    ssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # passive_arp | active_arp | mdns | ssdp
    method: Mapped[str] = mapped_column(String(16))
    seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship(back_populates="sightings")
