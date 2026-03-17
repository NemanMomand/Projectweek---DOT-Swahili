from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PreferredLanguage, WeatherSource
from app.repositories.farmer_repository import FarmerRepository
from app.services.sms_service import SMSService
from app.services.weather_provider import WeatherService


@dataclass
class ForecastDeliverySettings:
    enabled: bool
    last_sent_date_utc: str | None = None


class DailyForecastDeliveryService:
    def __init__(self) -> None:
        self._file_path = Path(__file__).resolve().parents[2] / "data" / "forecast_delivery_settings.json"
        self.weather_service = WeatherService()
        self.sms_service = SMSService()

    def _read_settings(self) -> ForecastDeliverySettings:
        if not self._file_path.exists():
            return ForecastDeliverySettings(enabled=False, last_sent_date_utc=None)
        try:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ForecastDeliverySettings(enabled=False, last_sent_date_utc=None)
        return ForecastDeliverySettings(
            enabled=bool(payload.get("enabled", False)),
            last_sent_date_utc=payload.get("last_sent_date_utc"),
        )

    def _write_settings(self, settings: ForecastDeliverySettings) -> ForecastDeliverySettings:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path.write_text(
            json.dumps(
                {
                    "enabled": settings.enabled,
                    "last_sent_date_utc": settings.last_sent_date_utc,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return settings

    def get_settings(self) -> ForecastDeliverySettings:
        return self._read_settings()

    def set_enabled(self, enabled: bool) -> ForecastDeliverySettings:
        current = self._read_settings()
        current.enabled = enabled
        return self._write_settings(current)

    def mark_sent_today(self) -> ForecastDeliverySettings:
        current = self._read_settings()
        current.last_sent_date_utc = datetime.now(UTC).date().isoformat()
        return self._write_settings(current)

    async def send_tomorrow_forecast_if_due(self, session: AsyncSession, force: bool = False) -> dict:
        settings = self._read_settings()
        today = datetime.now(UTC).date().isoformat()

        if not settings.enabled and not force:
            return {"status": "disabled", "sent": 0, "skipped": 0, "last_sent_date_utc": settings.last_sent_date_utc}

        if settings.last_sent_date_utc == today and not force:
            return {"status": "already_sent_today", "sent": 0, "skipped": 0, "last_sent_date_utc": settings.last_sent_date_utc}

        farmers = await FarmerRepository(session).list_active()
        sent = 0
        skipped = 0

        for farmer in farmers:
            try:
                forecast = await self.weather_service.forecast(farmer.latitude, farmer.longitude)
                if forecast.source != WeatherSource.VISUAL_CROSSING:
                    skipped += 1
                    continue
                days = (forecast.raw_payload or {}).get("days") or []
                if not days:
                    skipped += 1
                    continue
                tomorrow = days[1] if len(days) > 1 else days[0]
                message = self._build_message(
                    language=farmer.preferred_language,
                    precip_mm=float(tomorrow.get("precip", 0.0) or 0.0),
                    conditions=str(tomorrow.get("conditions") or "Unknown"),
                    cloud_cover=tomorrow.get("cloudcover"),
                    forecast_date=str(tomorrow.get("datetime") or "tomorrow"),
                )
                await self.sms_service.send_message(
                    session=session,
                    phone_number=farmer.phone_number,
                    body=message,
                )
                sent += 1
            except Exception:
                skipped += 1

        if sent > 0:
            settings.last_sent_date_utc = today
            self._write_settings(settings)

        return {
            "status": ("forced_sent" if force else "sent") if sent > 0 else ("forced_no_messages_sent" if force else "no_messages_sent"),
            "sent": sent,
            "skipped": skipped,
            "last_sent_date_utc": settings.last_sent_date_utc,
        }

    async def send_tomorrow_forecast_to_phone(
        self,
        session: AsyncSession,
        phone_number: str,
        language: PreferredLanguage = PreferredLanguage.EN,
    ) -> dict:
        farmers = await FarmerRepository(session).list_active()
        if not farmers:
            return {
                "status": "no_active_farmers_for_forecast",
                "sent": 0,
                "skipped": 1,
                "last_sent_date_utc": self._read_settings().last_sent_date_utc,
            }

        source_farmer = farmers[0]
        try:
            forecast = await self.weather_service.forecast(source_farmer.latitude, source_farmer.longitude)
            if forecast.source != WeatherSource.VISUAL_CROSSING:
                return {
                    "status": "forecast_not_real",
                    "sent": 0,
                    "skipped": 1,
                    "last_sent_date_utc": self._read_settings().last_sent_date_utc,
                }
            days = (forecast.raw_payload or {}).get("days") or []
            if not days:
                return {
                    "status": "forecast_missing_days",
                    "sent": 0,
                    "skipped": 1,
                    "last_sent_date_utc": self._read_settings().last_sent_date_utc,
                }
            tomorrow = days[1] if len(days) > 1 else days[0]
            message = self._build_message(
                language=language,
                precip_mm=float(tomorrow.get("precip", 0.0) or 0.0),
                conditions=str(tomorrow.get("conditions") or "Unknown"),
                cloud_cover=tomorrow.get("cloudcover"),
                forecast_date=str(tomorrow.get("datetime") or "tomorrow"),
            )
            await self.sms_service.send_message(session=session, phone_number=phone_number, body=message)
            return {
                "status": "forced_sent_to_phone",
                "sent": 1,
                "skipped": 0,
                "last_sent_date_utc": self._read_settings().last_sent_date_utc,
            }
        except Exception:
            return {
                "status": "forced_send_to_phone_failed",
                "sent": 0,
                "skipped": 1,
                "last_sent_date_utc": self._read_settings().last_sent_date_utc,
            }

    def _build_message(
        self,
        language: PreferredLanguage,
        precip_mm: float,
        conditions: str,
        cloud_cover: float | int | None,
        forecast_date: str,
    ) -> str:
        sunny_pct: int | None = None
        if cloud_cover is not None:
            try:
                sunny_pct = max(0, min(100, int(round(100 - float(cloud_cover)))))
            except (TypeError, ValueError):
                sunny_pct = None

        if language == PreferredLanguage.SW:
            if sunny_pct is None:
                return (
                    f"Utabiri wa kesho ({forecast_date}): mvua takriban {precip_mm:.1f} mm. "
                    f"Hali: {conditions}."
                )
            return (
                f"Utabiri wa kesho ({forecast_date}): mvua takriban {precip_mm:.1f} mm, "
                f"mwangaza wa jua karibu {sunny_pct}%. Hali: {conditions}."
            )

        if sunny_pct is None:
            return (
                f"Tomorrow forecast ({forecast_date}): around {precip_mm:.1f} mm rain. "
                f"Conditions: {conditions}."
            )
        return (
            f"Tomorrow forecast ({forecast_date}): around {precip_mm:.1f} mm rain, "
            f"about {sunny_pct}% sunny. Conditions: {conditions}."
        )
