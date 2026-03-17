from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.config import get_settings
from app.models.farmer import Farmer
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.location_repository import LocationRepository
from app.schemas.intake import IntakeSubmissionRequest, IntakeSubmissionResponse
from app.schemas.simulation import SimulationEventCreate
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])


@router.post("/submit", response_model=IntakeSubmissionResponse)
async def submit_user_data(payload: IntakeSubmissionRequest, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    farmer_repo = FarmerRepository(session)

    farmer = await farmer_repo.get_by_phone(payload.phone_number)
    values = {
        "full_name": payload.full_name,
        "phone_number": payload.phone_number,
        "preferred_language": payload.preferred_language,
        "region": payload.region,
        "district": payload.district,
        "village": payload.village,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "crop_type": payload.crop_type,
        "is_active": True,
    }

    if farmer is None:
        farmer = Farmer(**values)
        await farmer_repo.create(farmer)
    else:
        await farmer_repo.update(farmer, values)

    await LocationRepository(session).get_or_create(
        region=payload.region,
        district=payload.district,
        village=payload.village,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    await session.commit()
    await session.refresh(farmer)

    event = await SimulationService().create_event(
        session,
        SimulationEventCreate(
            event_type=payload.event_type,
            severity=payload.severity,
            target_farmer_id=farmer.id,
            starts_at=payload.event_starts_at,
            starts_in_minutes=0,
            sms_delay_seconds=0,
            language=payload.preferred_language,
            custom_message=payload.custom_message,
        ),
    )

    return IntakeSubmissionResponse(
        farmer_id=farmer.id,
        simulation_event_id=event.id,
        scheduled_alert_for=event.starts_at - timedelta(minutes=settings.alert_lead_minutes),
        lead_minutes=settings.alert_lead_minutes,
    )
