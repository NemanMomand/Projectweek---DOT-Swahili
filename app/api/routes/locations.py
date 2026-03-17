from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.location_repository import LocationRepository
from app.schemas.location import LocationRead

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationRead])
async def list_locations(session: AsyncSession = Depends(get_session)):
    return await LocationRepository(session).list()
