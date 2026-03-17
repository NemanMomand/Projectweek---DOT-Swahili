from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.models.enums import PreferredLanguage
from app.services.daily_forecast_delivery_service import DailyForecastDeliveryService

router = APIRouter(prefix="/api/v1/forecast-delivery", tags=["forecast-delivery"])
service = DailyForecastDeliveryService()


class ForecastDeliverySettingsResponse(BaseModel):
    enabled: bool
    last_sent_date_utc: str | None = None


class ForecastDeliverySettingsUpdate(BaseModel):
    enabled: bool


class ForecastDeliveryDispatchResponse(BaseModel):
    status: str
    sent: int
    skipped: int
    last_sent_date_utc: str | None = None


@router.get("/settings", response_model=ForecastDeliverySettingsResponse)
async def get_forecast_delivery_settings() -> ForecastDeliverySettingsResponse:
    settings = service.get_settings()
    return ForecastDeliverySettingsResponse(
        enabled=settings.enabled,
        last_sent_date_utc=settings.last_sent_date_utc,
    )


@router.put("/settings", response_model=ForecastDeliverySettingsResponse)
async def update_forecast_delivery_settings(payload: ForecastDeliverySettingsUpdate) -> ForecastDeliverySettingsResponse:
    settings = service.set_enabled(payload.enabled)
    return ForecastDeliverySettingsResponse(
        enabled=settings.enabled,
        last_sent_date_utc=settings.last_sent_date_utc,
    )


@router.post("/dispatch-now", response_model=ForecastDeliveryDispatchResponse)
async def dispatch_forecast_delivery_now(
    session: AsyncSession = Depends(get_session),
    force: bool = Query(default=False),
    phone_number: str | None = Query(default=None),
    language: PreferredLanguage = Query(default=PreferredLanguage.EN),
) -> ForecastDeliveryDispatchResponse:
    if phone_number:
        result = await service.send_tomorrow_forecast_to_phone(
            session=session,
            phone_number=phone_number,
            language=language,
        )
    else:
        result = await service.send_tomorrow_forecast_if_due(session, force=force)
    return ForecastDeliveryDispatchResponse(**result)
