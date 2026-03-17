from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.alert import Alert
from app.models.farmer_feedback import FarmerFeedback
from app.models.simulation_event import SimulationEvent
from app.models.sms_message import SMSMessage
from app.models.weather_observation import WeatherObservation
from app.repositories.simulation_repository import SimulationRepository
from app.services.alert_engine import AlertEngine
from app.schemas.simulation import SimulationEventCreate


class SimulationService:
    def __init__(self, alert_engine: AlertEngine | None = None) -> None:
        self.alert_engine = alert_engine or AlertEngine()
        self.settings = get_settings()

    async def create_event(self, session: AsyncSession, payload: SimulationEventCreate) -> SimulationEvent:
        starts_at = payload.starts_at or (datetime.now(UTC) + timedelta(minutes=payload.starts_in_minutes))
        event = SimulationEvent(
            event_type=payload.event_type,
            severity=payload.severity,
            target_region=payload.target_region,
            target_farmer_id=payload.target_farmer_id,
            language=payload.language,
            starts_at=starts_at,
            trigger_after_minutes=payload.starts_in_minutes,
            sms_delay_seconds=payload.sms_delay_seconds,
            custom_message=payload.custom_message,
        )
        await SimulationRepository(session).create(event)
        await session.commit()
        await session.refresh(event)
        return event

    async def list_events(self, session: AsyncSession) -> list[SimulationEvent]:
        return await SimulationRepository(session).list()

    async def get_event(self, session: AsyncSession, event_id: int) -> SimulationEvent | None:
        return await SimulationRepository(session).get(event_id)

    async def trigger_event(self, session: AsyncSession, event: SimulationEvent) -> dict[str, int]:
        event.starts_at = datetime.now(UTC)
        return await self.alert_engine.process_simulation_event(session, event)

    async def process_due_events(self, session: AsyncSession) -> list[dict[str, int | str]]:
        trigger_time = datetime.now(UTC) + timedelta(minutes=self.settings.alert_lead_minutes)
        due_events = await SimulationRepository(session).list_due(trigger_time)
        results: list[dict[str, int | str]] = []
        for event in due_events:
            result = await self.alert_engine.process_simulation_event(session, event)
            results.append({"event_id": event.id, **result, "status": event.status.value})
        return results

    async def reset(self, session: AsyncSession) -> dict[str, int]:
        deleted_feedback = (await session.execute(delete(FarmerFeedback))).rowcount or 0
        deleted_sms = (await session.execute(delete(SMSMessage))).rowcount or 0
        deleted_alerts = (await session.execute(delete(Alert))).rowcount or 0
        deleted_observations = (await session.execute(delete(WeatherObservation))).rowcount or 0
        deleted_events = (await session.execute(delete(SimulationEvent))).rowcount or 0
        await session.commit()
        return {
            "deleted_events": deleted_events,
            "deleted_alerts": deleted_alerts,
            "deleted_sms": deleted_sms,
            "deleted_feedback": deleted_feedback,
            "deleted_observations": deleted_observations,
        }
