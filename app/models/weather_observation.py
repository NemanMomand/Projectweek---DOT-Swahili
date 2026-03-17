from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin, json_type
from app.models.enums import WeatherSource


class WeatherObservation(Base, IdMixin, TimestampMixin):
    __tablename__ = "weather_observations"

    source: Mapped[WeatherSource] = mapped_column(Enum(WeatherSource, native_enum=False), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_kph: Mapped[float] = mapped_column(Float, nullable=False)
    soil_moisture_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    drought_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(json_type, nullable=False)

    alerts = relationship("Alert", back_populates="source_observation")
