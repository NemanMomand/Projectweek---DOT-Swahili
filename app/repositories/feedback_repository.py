from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer_feedback import FarmerFeedback


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, feedback: FarmerFeedback) -> FarmerFeedback:
        self.session.add(feedback)
        await self.session.flush()
        await self.session.refresh(feedback)
        return feedback

    async def list(self) -> list[FarmerFeedback]:
        result = await self.session.execute(
            select(FarmerFeedback).order_by(FarmerFeedback.created_at.desc(), FarmerFeedback.id.desc())
        )
        return list(result.scalars().all())

    async def list_recent_for_farmer(self, farmer_id: int, since: datetime) -> list[FarmerFeedback]:
        result = await self.session.execute(
            select(FarmerFeedback)
            .where(
                FarmerFeedback.farmer_id == farmer_id,
                FarmerFeedback.created_at >= since,
            )
            .order_by(FarmerFeedback.created_at.desc(), FarmerFeedback.id.desc())
        )
        return list(result.scalars().all())

    async def delete_all(self) -> int:
        result = await self.session.execute(delete(FarmerFeedback))
        return result.rowcount or 0
