from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather_observation import WeatherObservation


class WeatherRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, observation: WeatherObservation) -> WeatherObservation:
        self.session.add(observation)
        await self.session.flush()
        await self.session.refresh(observation)
        return observation

    async def latest_for_coordinates(self, latitude: float, longitude: float) -> WeatherObservation | None:
        result = await self.session.execute(
            select(WeatherObservation)
            .where(WeatherObservation.latitude == latitude, WeatherObservation.longitude == longitude)
            .order_by(WeatherObservation.observed_at.desc())
        )
        return result.scalar_one_or_none()
