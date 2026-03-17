from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.models.farmer import Farmer
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.location_repository import LocationRepository
from app.schemas.farmer import FarmerCreate, FarmerRead, FarmerUpdate

router = APIRouter(prefix="/api/v1/farmers", tags=["farmers"])


@router.post("", response_model=FarmerRead, status_code=status.HTTP_201_CREATED)
async def create_farmer(payload: FarmerCreate, session: AsyncSession = Depends(get_session)) -> Farmer:
    farmer = Farmer(**payload.model_dump())
    repository = FarmerRepository(session)
    try:
        created = await repository.create(farmer)
        await LocationRepository(session).get_or_create(
            region=payload.region,
            district=payload.district,
            village=payload.village,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        await session.commit()
        await session.refresh(created)
        return created
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Farmer phone number already exists") from exc


@router.get("", response_model=list[FarmerRead])
async def list_farmers(session: AsyncSession = Depends(get_session)) -> list[Farmer]:
    return await FarmerRepository(session).list()


@router.get("/{farmer_id}", response_model=FarmerRead)
async def get_farmer(farmer_id: int, session: AsyncSession = Depends(get_session)) -> Farmer:
    farmer = await FarmerRepository(session).get(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.patch("/{farmer_id}", response_model=FarmerRead)
async def update_farmer(
    farmer_id: int,
    payload: FarmerUpdate,
    session: AsyncSession = Depends(get_session),
) -> Farmer:
    repository = FarmerRepository(session)
    farmer = await repository.get(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    values = payload.model_dump(exclude_unset=True)
    try:
        updated = await repository.update(farmer, values)
        if {"region", "district", "village", "latitude", "longitude"}.intersection(values):
            await LocationRepository(session).get_or_create(
                region=updated.region,
                district=updated.district,
                village=updated.village,
                latitude=updated.latitude,
                longitude=updated.longitude,
            )
        await session.commit()
        return updated
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Farmer phone number already exists") from exc


@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_farmer(farmer_id: int, session: AsyncSession = Depends(get_session)) -> Response:
    repository = FarmerRepository(session)
    farmer = await repository.get(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    await repository.delete(farmer)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
