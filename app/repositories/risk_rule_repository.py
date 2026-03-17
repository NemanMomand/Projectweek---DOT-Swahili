from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_rule import RiskRule


class RiskRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_enabled(self) -> list[RiskRule]:
        result = await self.session.execute(select(RiskRule).where(RiskRule.enabled.is_(True)).order_by(RiskRule.id))
        return list(result.scalars().all())

    async def list_all(self) -> list[RiskRule]:
        result = await self.session.execute(select(RiskRule).order_by(RiskRule.id))
        return list(result.scalars().all())
