from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer


class FarmerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, farmer: Farmer) -> Farmer:
        self.session.add(farmer)
        await self.session.flush()
        await self.session.refresh(farmer)
        return farmer

    async def list(self) -> list[Farmer]:
        result = await self.session.execute(select(Farmer).order_by(Farmer.id))
        return list(result.scalars().all())

    async def list_active(self) -> list[Farmer]:
        result = await self.session.execute(select(Farmer).where(Farmer.is_active.is_(True)).order_by(Farmer.id))
        return list(result.scalars().all())

    async def get(self, farmer_id: int) -> Farmer | None:
        return await self.session.get(Farmer, farmer_id)

    async def get_by_phone(self, phone_number: str) -> Farmer | None:
        result = await self.session.execute(select(Farmer).where(Farmer.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def update(self, farmer: Farmer, values: dict) -> Farmer:
        for key, value in values.items():
            setattr(farmer, key, value)
        await self.session.flush()
        await self.session.refresh(farmer)
        return farmer

    async def delete(self, farmer: Farmer) -> None:
        await self.session.delete(farmer)
