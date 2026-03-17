from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.farmer_repository import FarmerRepository


async def get_session() -> AsyncSession:
    async for session in get_db_session():
        yield session


async def resolve_coordinates(
    session: AsyncSession = Depends(get_session),
    farmer_id: int | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
) -> tuple[float, float]:
    if farmer_id is not None:
        farmer = await FarmerRepository(session).get(farmer_id)
        if farmer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
        return farmer.latitude, farmer.longitude
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide farmer_id or latitude and longitude",
        )
    return latitude, longitude
