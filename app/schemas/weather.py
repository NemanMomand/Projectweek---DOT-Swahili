from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import WeatherSource


class WeatherObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    source: WeatherSource
    latitude: float
    longitude: float
    observed_at: datetime
    rainfall_mm: float
    temperature_c: float
    humidity_pct: float
    wind_speed_kph: float
    soil_moisture_index: float | None = None
    drought_risk_score: float | None = None
    raw_payload: dict


class ForecastPoint(BaseModel):
    observed_at: datetime
    rainfall_mm: float
    temperature_c: float
    humidity_pct: float
    wind_speed_kph: float


class ForecastResponse(BaseModel):
    source: WeatherSource
    latitude: float
    longitude: float
    timeline: list[ForecastPoint]
    raw_payload: dict
