from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import AlertSeverity, AlertType, DeliveryStatus, PreferredLanguage


class Alert(Base, IdMixin, TimestampMixin):
    __tablename__ = "alerts"

    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType, native_enum=False), nullable=False, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, native_enum=False),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[PreferredLanguage] = mapped_column(
        Enum(PreferredLanguage, native_enum=False),
        nullable=False,
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, native_enum=False),
        nullable=False,
        default=DeliveryStatus.PENDING,
    )
    source_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("weather_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    simulation_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("simulation_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    farmer = relationship("Farmer", back_populates="alerts")
    source_observation = relationship("WeatherObservation", back_populates="alerts")
