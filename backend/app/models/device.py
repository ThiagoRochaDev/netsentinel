from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mac_address: Mapped[str] = mapped_column(String(17), unique=True, index=True)
    vendor_oui: Mapped[str | None] = mapped_column(String(128), nullable=True)
    custom_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_known: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    sightings: Mapped[list["DeviceSighting"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    ports: Mapped[list["DevicePort"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class DevicePort(Base):
    __tablename__ = "device_ports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    port: Mapped[int] = mapped_column(Integer)
    proto: Mapped[str] = mapped_column(String(8))
    service_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    device: Mapped["Device"] = relationship(back_populates="ports")
