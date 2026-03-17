from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, resolve_coordinates
from app.models.enums import WeatherSource
from app.repositories.farmer_repository import FarmerRepository
from app.services.weather_provider import WeatherService

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


class LiveFarmerWeatherPoint(BaseModel):
    farmer_id: int
    farmer_name: str
    phone_number: str
    region: str
    district: str
    village: str
    latitude: float
    longitude: float
    observed_at: str
    rainfall_mm: float
    temperature_c: float
    humidity_pct: float
    wind_speed_kph: float
    source: str
    station_id: str | None = None
    station_name: str | None = None


class WeeklyForecastPoint(BaseModel):
    date: str
    temp_c: float
    precip_mm: float
    humidity_pct: float | None = None
    wind_speed_kph: float | None = None
    precip_probability_pct: float | None = None
    conditions: str | None = None
    source: str


@router.get("/current")
async def get_current_weather(coordinates: tuple[float, float] = Depends(resolve_coordinates)):
    latitude, longitude = coordinates
    return await WeatherService().current(latitude, longitude)


@router.get("/forecast")
async def get_forecast_weather(coordinates: tuple[float, float] = Depends(resolve_coordinates)):
    latitude, longitude = coordinates
    return await WeatherService().forecast(latitude, longitude)


@router.get("/live/farmers", response_model=list[LiveFarmerWeatherPoint])
async def get_live_farmer_weather(
    session: AsyncSession = Depends(get_session),
    region: str | None = Query(default=None),
    district: str | None = Query(default=None),
    village: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
):
    farmers = await FarmerRepository(session).list_active()

    def _match(value: str, filter_value: str | None) -> bool:
        if not filter_value:
            return True
        return value.strip().lower() == filter_value.strip().lower()

    filtered = [
        farmer
        for farmer in farmers
        if _match(farmer.region, region)
        and _match(farmer.district, district)
        and _match(farmer.village, village)
    ][:limit]

    weather_service = WeatherService()
    rows: list[LiveFarmerWeatherPoint] = []
    for farmer in filtered:
        current = await weather_service.current(farmer.latitude, farmer.longitude)
        if current.source != WeatherSource.VISUAL_CROSSING:
            continue
        raw_payload = current.raw_payload or {}
        current_conditions = raw_payload.get("currentConditions") or {}
        station_ids = current_conditions.get("stations") or []
        station_id = station_ids[0] if station_ids else None
        station_name = None
        if station_id:
            stations_map = raw_payload.get("stations") or {}
            station_meta = stations_map.get(station_id) or {}
            station_name = station_meta.get("name")
        rows.append(
            LiveFarmerWeatherPoint(
                farmer_id=farmer.id,
                farmer_name=farmer.full_name,
                phone_number=farmer.phone_number,
                region=farmer.region,
                district=farmer.district,
                village=farmer.village,
                latitude=farmer.latitude,
                longitude=farmer.longitude,
                observed_at=current.observed_at.isoformat(),
                rainfall_mm=current.rainfall_mm,
                temperature_c=current.temperature_c,
                humidity_pct=current.humidity_pct,
                wind_speed_kph=current.wind_speed_kph,
                source=current.source.value,
                station_id=station_id,
                station_name=station_name,
            )
        )

    if filtered and not rows:
        raise HTTPException(
            status_code=503,
            detail="No real weather API data available. Set VISUAL_CROSSING_API_KEY and WEATHER_MOCK_FALLBACK=false.",
        )

    return rows


@router.get("/live/weekly", response_model=list[WeeklyForecastPoint])
async def get_live_weekly_forecast(
    session: AsyncSession = Depends(get_session),
    region: str | None = Query(default=None),
    district: str | None = Query(default=None),
    village: str | None = Query(default=None),
):
    farmers = await FarmerRepository(session).list_active()

    def _match(value: str, filter_value: str | None) -> bool:
        if not filter_value:
            return True
        return value.strip().lower() == filter_value.strip().lower()

    filtered = [
        farmer
        for farmer in farmers
        if _match(farmer.region, region)
        and _match(farmer.district, district)
        and _match(farmer.village, village)
    ]
    if not filtered:
        return []

    target = filtered[0]
    forecast = await WeatherService().forecast(target.latitude, target.longitude)
    if forecast.source != WeatherSource.VISUAL_CROSSING:
        raise HTTPException(
            status_code=503,
            detail="No real weather API forecast available. Set VISUAL_CROSSING_API_KEY and WEATHER_MOCK_FALLBACK=false.",
        )

    raw_payload = forecast.raw_payload or {}
    days = raw_payload.get("days") or []
    points: list[WeeklyForecastPoint] = []
    for day in days[:7]:
        date_value = day.get("datetime")
        if not date_value:
            epoch = day.get("datetimeEpoch")
            if epoch is None:
                continue
            date_value = str(epoch)
        points.append(
            WeeklyForecastPoint(
                date=str(date_value),
                temp_c=float(day.get("temp", 0.0) or 0.0),
                precip_mm=float(day.get("precip", 0.0) or 0.0),
                humidity_pct=float(day.get("humidity", 0.0) or 0.0) if day.get("humidity") is not None else None,
                wind_speed_kph=float(day.get("windspeed", 0.0) or 0.0) if day.get("windspeed") is not None else None,
                precip_probability_pct=float(day.get("precipprob", 0.0) or 0.0) if day.get("precipprob") is not None else None,
                conditions=day.get("conditions"),
                source=forecast.source.value,
            )
        )

    return points
