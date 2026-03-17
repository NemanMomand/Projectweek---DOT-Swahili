from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import WeatherSource
from app.schemas.weather import ForecastPoint, ForecastResponse, WeatherObservationRead

logger = get_logger(__name__)


@dataclass
class ForecastSummary:
    source: WeatherSource
    latitude: float
    longitude: float
    observed_at: datetime
    rainfall_24h_mm: float
    rainfall_72h_mm: float
    max_temperature_c: float
    avg_humidity_pct: float
    max_wind_speed_kph: float
    soil_moisture_index: float | None
    drought_risk_score: float | None
    raw_payload: dict


class WeatherProvider(Protocol):
    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherObservationRead: ...

    async def get_forecast(self, latitude: float, longitude: float) -> ForecastResponse: ...


class VisualCrossingWeatherProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherObservationRead:
        payload = await self._get_payload(latitude, longitude)
        return self.normalize_current_payload(payload, latitude, longitude)

    async def get_forecast(self, latitude: float, longitude: float) -> ForecastResponse:
        payload = await self._get_payload(latitude, longitude)
        return self.normalize_forecast_payload(payload, latitude, longitude)

    async def _get_payload(self, latitude: float, longitude: float) -> dict:
        if not self.settings.visual_crossing_api_key:
            logger.warning("Visual Crossing API key missing")
            if not self.settings.weather_mock_fallback:
                raise RuntimeError(
                    "Visual Crossing API key ontbreekt. Zet VISUAL_CROSSING_API_KEY (of WEATHER_API_KEY)."
                )
            logger.warning("Using mock weather payload because WEATHER_MOCK_FALLBACK=true")
            return self._mock_payload(latitude, longitude)
        url = f"{self.settings.visual_crossing_base_url}/{latitude},{longitude}"
        params = {
            "unitGroup": "metric",
            "include": "current,hours,days",
            "contentType": "json",
            "key": self.settings.visual_crossing_api_key,
        }
        timeout = httpx.Timeout(self.settings.weather_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, self.settings.weather_retry_attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    logger.warning(
                        "weather_provider_retry",
                        extra={"attempt": attempt, "error": str(exc), "provider": "visual_crossing"},
                    )
                    if attempt == self.settings.weather_retry_attempts:
                        if self.settings.weather_mock_fallback:
                            logger.warning("Weather provider failed; falling back to mock payload")
                            return self._mock_payload(latitude, longitude)
                        raise
                    await asyncio.sleep(self.settings.weather_retry_backoff_seconds * attempt)
        return self._mock_payload(latitude, longitude)

    @staticmethod
    def normalize_current_payload(payload: dict, latitude: float, longitude: float) -> WeatherObservationRead:
        current = payload.get("currentConditions") or {}
        observed_epoch = current.get("datetimeEpoch")
        observed_at = (
            datetime.fromtimestamp(observed_epoch, tz=UTC)
            if observed_epoch is not None
            else datetime.now(UTC)
        )
        return WeatherObservationRead(
            source=WeatherSource.VISUAL_CROSSING if payload.get("queryCost") is not None else WeatherSource.MOCK,
            latitude=round(latitude, 6),
            longitude=round(longitude, 6),
            observed_at=observed_at,
            rainfall_mm=float(current.get("precip", 0.0) or 0.0),
            temperature_c=float(current.get("temp", 0.0) or 0.0),
            humidity_pct=float(current.get("humidity", 0.0) or 0.0),
            wind_speed_kph=float(current.get("windspeed", 0.0) or 0.0),
            soil_moisture_index=None,
            drought_risk_score=None,
            raw_payload=payload,
        )

    @staticmethod
    def normalize_forecast_payload(payload: dict, latitude: float, longitude: float) -> ForecastResponse:
        timeline: list[ForecastPoint] = []
        hourly_items: list[dict] = []
        for day in payload.get("days", []):
            hourly_items.extend(day.get("hours", []))
        if hourly_items:
            for item in hourly_items[:72]:
                timeline.append(
                    ForecastPoint(
                        observed_at=datetime.fromtimestamp(item["datetimeEpoch"], tz=UTC),
                        rainfall_mm=float(item.get("precip", 0.0) or 0.0),
                        temperature_c=float(item.get("temp", 0.0) or 0.0),
                        humidity_pct=float(item.get("humidity", 0.0) or 0.0),
                        wind_speed_kph=float(item.get("windspeed", 0.0) or 0.0),
                    )
                )
        else:
            for day in payload.get("days", [])[:3]:
                timeline.append(
                    ForecastPoint(
                        observed_at=datetime.fromtimestamp(day["datetimeEpoch"], tz=UTC),
                        rainfall_mm=float(day.get("precip", 0.0) or 0.0),
                        temperature_c=float(day.get("tempmax", 0.0) or 0.0),
                        humidity_pct=float(day.get("humidity", 0.0) or 0.0),
                        wind_speed_kph=float(day.get("windspeed", 0.0) or 0.0),
                    )
                )
        return ForecastResponse(
            source=WeatherSource.VISUAL_CROSSING if payload.get("queryCost") is not None else WeatherSource.MOCK,
            latitude=round(latitude, 6),
            longitude=round(longitude, 6),
            timeline=timeline,
            raw_payload=payload,
        )

    def _mock_payload(self, latitude: float, longitude: float) -> dict:
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        hours = []
        for offset in range(72):
            ts = now + timedelta(hours=offset)
            hours.append(
                {
                    "datetimeEpoch": int(ts.timestamp()),
                    "precip": 0.4 if offset < 6 else 3.5 if 8 <= offset <= 12 else 0.0,
                    "temp": 29 + (offset % 6),
                    "humidity": 65 - (offset % 10),
                    "windspeed": 14 + (offset % 5),
                }
            )
        return {
            "latitude": latitude,
            "longitude": longitude,
            "days": [{"hours": hours, "datetimeEpoch": int(now.timestamp()), "precip": 12.5}],
            "currentConditions": hours[0],
        }


class FASTAWeatherProviderStub:
    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherObservationRead:
        return WeatherObservationRead(
            source=WeatherSource.FASTA,
            latitude=latitude,
            longitude=longitude,
            observed_at=datetime.now(UTC),
            rainfall_mm=0.0,
            temperature_c=0.0,
            humidity_pct=0.0,
            wind_speed_kph=0.0,
            soil_moisture_index=None,
            drought_risk_score=None,
            raw_payload={"message": "FASTA adapter stub is available for future storm ingestion"},
        )

    async def get_forecast(self, latitude: float, longitude: float) -> ForecastResponse:
        return ForecastResponse(
            source=WeatherSource.FASTA,
            latitude=latitude,
            longitude=longitude,
            timeline=[],
            raw_payload={"message": "FASTA adapter stub is available for future nowcasting"},
        )


class WeatherService:
    def __init__(self, provider: WeatherProvider | None = None) -> None:
        self.provider = provider or get_weather_provider()

    async def current(self, latitude: float, longitude: float) -> WeatherObservationRead:
        return await self.provider.get_current_weather(latitude, longitude)

    async def forecast(self, latitude: float, longitude: float) -> ForecastResponse:
        return await self.provider.get_forecast(latitude, longitude)

    async def summarize_forecast(self, latitude: float, longitude: float) -> ForecastSummary:
        forecast = await self.forecast(latitude, longitude)
        now = datetime.now(UTC)
        next_24h = [item for item in forecast.timeline if item.observed_at <= now + timedelta(hours=24)]
        next_72h = [item for item in forecast.timeline if item.observed_at <= now + timedelta(hours=72)]
        humidity_values = [item.humidity_pct for item in forecast.timeline] or [0.0]
        total_24h = sum(item.rainfall_mm for item in next_24h)
        total_72h = sum(item.rainfall_mm for item in next_72h)
        max_temp = max((item.temperature_c for item in forecast.timeline), default=0.0)
        max_wind = max((item.wind_speed_kph for item in forecast.timeline), default=0.0)
        drought_score = None
        if next_72h:
            drought_score = round(max(0.0, 1.0 - (total_72h / max(1.0, get_settings().drought_72h_threshold_mm))), 2)
        soil_moisture = round(max(0.0, min(1.0, total_72h / 30.0)), 2) if next_72h else None
        return ForecastSummary(
            source=forecast.source,
            latitude=forecast.latitude,
            longitude=forecast.longitude,
            observed_at=forecast.timeline[0].observed_at if forecast.timeline else now,
            rainfall_24h_mm=round(total_24h, 2),
            rainfall_72h_mm=round(total_72h, 2),
            max_temperature_c=round(max_temp, 2),
            avg_humidity_pct=round(sum(humidity_values) / len(humidity_values), 2),
            max_wind_speed_kph=round(max_wind, 2),
            soil_moisture_index=soil_moisture,
            drought_risk_score=drought_score,
            raw_payload=forecast.raw_payload,
        )


def get_weather_provider() -> WeatherProvider:
    settings = get_settings()
    if settings.weather_provider == "fasta":
        return FASTAWeatherProviderStub()
    return VisualCrossingWeatherProvider()
