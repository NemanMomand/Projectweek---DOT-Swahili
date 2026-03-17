from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Location]:
        result = await self.session.execute(select(Location).order_by(Location.region, Location.district, Location.village))
        return list(result.scalars().all())

    async def get_or_create(self, region: str, district: str, village: str, latitude: float, longitude: float) -> Location:
        result = await self.session.execute(
            select(Location).where(
                Location.region == region,
                Location.district == district,
                Location.village == village,
            )
        )
        location = result.scalar_one_or_none()
        if location is None:
            location = Location(
                region=region,
                district=district,
                village=village,
                latitude=latitude,
                longitude=longitude,
            )
            self.session.add(location)
            await self.session.flush()
            await self.session.refresh(location)
        return location
