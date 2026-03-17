from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import AlertSeverity, PreferredLanguage, SimulationEventType, SimulationStatus


class SimulationEvent(Base, IdMixin, TimestampMixin):
    __tablename__ = "simulation_events"

    event_type: Mapped[SimulationEventType] = mapped_column(
        Enum(SimulationEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, native_enum=False),
        nullable=False,
    )
    target_region: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    target_farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    language: Mapped[PreferredLanguage] = mapped_column(
        Enum(PreferredLanguage, native_enum=False),
        nullable=False,
        default=PreferredLanguage.EN,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    trigger_after_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sms_delay_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    custom_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SimulationStatus] = mapped_column(
        Enum(SimulationStatus, native_enum=False),
        nullable=False,
        default=SimulationStatus.PENDING,
        index=True,
    )

    target_farmer = relationship("Farmer", back_populates="simulation_events")
