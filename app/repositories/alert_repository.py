from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.enums import AlertType
from app.models.enums import WeatherSource
from app.models.weather_observation import WeatherObservation


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, alert: Alert) -> Alert:
        self.session.add(alert)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    async def list(self, real_only: bool = False) -> list[Alert]:
        query = select(Alert)
        if real_only:
            query = query.join(
                WeatherObservation,
                Alert.source_observation_id == WeatherObservation.id,
            ).where(
                Alert.simulation_event_id.is_(None),
                WeatherObservation.source == WeatherSource.VISUAL_CROSSING,
            )
        result = await self.session.execute(query.order_by(Alert.created_at.desc(), Alert.id.desc()))
        return list(result.scalars().all())

    async def list_for_farmer(self, farmer_id: int, real_only: bool = False) -> list[Alert]:
        query = select(Alert).where(Alert.farmer_id == farmer_id)
        if real_only:
            query = query.join(
                WeatherObservation,
                Alert.source_observation_id == WeatherObservation.id,
            ).where(
                Alert.simulation_event_id.is_(None),
                WeatherObservation.source == WeatherSource.VISUAL_CROSSING,
            )
        result = await self.session.execute(query.order_by(Alert.created_at.desc(), Alert.id.desc()))
        return list(result.scalars().all())

    async def find_recent_duplicate(
        self,
        farmer_id: int,
        alert_type: AlertType,
        since: datetime,
    ) -> Alert | None:
        result = await self.session.execute(
            select(Alert)
            .where(Alert.farmer_id == farmer_id, Alert.alert_type == alert_type, Alert.created_at >= since)
            .order_by(Alert.created_at.desc())
        )
        return result.scalar_one_or_none()
