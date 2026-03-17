from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.enums import AlertType, PreferredLanguage, WeatherSource
from app.models.farmer import Farmer
from app.repositories.alert_repository import AlertRepository
from app.services.alert_engine import AlertEngine
from app.services.weather_provider import ForecastSummary


class RainHeatWeatherService:
    async def summarize_forecast(self, latitude: float, longitude: float) -> ForecastSummary:
        return ForecastSummary(
            source=WeatherSource.MOCK,
            latitude=latitude,
            longitude=longitude,
            observed_at=datetime.now(UTC),
            rainfall_24h_mm=48.0,
            rainfall_72h_mm=12.0,
            max_temperature_c=36.0,
            avg_humidity_pct=72.0,
            max_wind_speed_kph=20.0,
            soil_moisture_index=0.7,
            drought_risk_score=0.1,
            raw_payload={"stub": True},
        )


@pytest.mark.asyncio
async def test_alert_rule_evaluation_creates_rain_and_heat_alerts(session):
    farmer = Farmer(
        full_name="Test Farmer",
        phone_number="+255700111111",
        preferred_language=PreferredLanguage.EN,
        region="Arusha",
        district="Meru",
        village="Usa River",
        latitude=-3.369,
        longitude=36.8569,
        crop_type="Maize",
        is_active=True,
    )
    session.add(farmer)
    await session.commit()

    engine = AlertEngine(weather_service=RainHeatWeatherService())
    result = await engine.evaluate_all(session)
    alerts = await AlertRepository(session).list()

    assert result["alerts_created"] == 2
    assert result["sms_sent"] == 2
    assert {alert.alert_type for alert in alerts} == {AlertType.RAIN, AlertType.HEAT}


@pytest.mark.asyncio
async def test_duplicate_alert_suppression(session):
    farmer = Farmer(
        full_name="Repeat Farmer",
        phone_number="+255700111112",
        preferred_language=PreferredLanguage.SW,
        region="Arusha",
        district="Meru",
        village="Usa River",
        latitude=-3.369,
        longitude=36.8569,
        crop_type="Beans",
        is_active=True,
    )
    session.add(farmer)
    await session.commit()

    engine = AlertEngine(weather_service=RainHeatWeatherService())
    first_run = await engine.evaluate_all(session)
    second_run = await engine.evaluate_all(session)

    assert first_run["alerts_created"] == 2
    assert second_run["alerts_created"] == 0
