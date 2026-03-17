from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SimulationStatus
from app.models.simulation_event import SimulationEvent


class SimulationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, event: SimulationEvent) -> SimulationEvent:
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list(self) -> list[SimulationEvent]:
        result = await self.session.execute(
            select(SimulationEvent).order_by(SimulationEvent.created_at.desc(), SimulationEvent.id.desc())
        )
        return list(result.scalars().all())

    async def get(self, event_id: int) -> SimulationEvent | None:
        return await self.session.get(SimulationEvent, event_id)

    async def list_due(self, now: datetime) -> list[SimulationEvent]:
        result = await self.session.execute(
            select(SimulationEvent).where(
                SimulationEvent.starts_at <= now,
                or_(
                    SimulationEvent.status == SimulationStatus.PENDING,
                    SimulationEvent.status == SimulationStatus.DETECTED,
                ),
            )
        )
        return list(result.scalars().all())

    async def delete_all(self) -> int:
        result = await self.session.execute(delete(SimulationEvent))
        return result.rowcount or 0
