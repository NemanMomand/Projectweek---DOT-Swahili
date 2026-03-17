from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.sms_repository import SMSRepository
from app.schemas.simulation import (
    SimulationEventCreate,
    SimulationEventRead,
    SimulationResetResponse,
    SimulationTriggerResponse,
)
from app.schemas.sms import SMSMessageRead
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


@router.post("/events", response_model=SimulationEventRead, status_code=status.HTTP_201_CREATED)
async def create_simulation_event(payload: SimulationEventCreate, session: AsyncSession = Depends(get_session)):
    return await SimulationService().create_event(session, payload)


@router.get("/events", response_model=list[SimulationEventRead])
async def list_simulation_events(session: AsyncSession = Depends(get_session)):
    return await SimulationService().list_events(session)


@router.get("/events/{event_id}", response_model=SimulationEventRead)
async def get_simulation_event(event_id: int, session: AsyncSession = Depends(get_session)):
    event = await SimulationService().get_event(session, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation event not found")
    return event


@router.post("/events/{event_id}/trigger", response_model=SimulationTriggerResponse)
async def trigger_simulation_event(event_id: int, session: AsyncSession = Depends(get_session)):
    service = SimulationService()
    event = await service.get_event(session, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation event not found")
    result = await service.trigger_event(session, event)
    await session.refresh(event)
    return SimulationTriggerResponse(
        event_id=event.id,
        status=event.status,
        alerts_created=result["alerts_created"],
        sms_sent=result["sms_sent"],
    )


@router.post("/reset", response_model=SimulationResetResponse)
async def reset_simulation(session: AsyncSession = Depends(get_session)):
    return SimulationResetResponse(**(await SimulationService().reset(session)))


@router.get("/sms-log", response_model=list[SMSMessageRead])
async def get_simulation_sms_log(session: AsyncSession = Depends(get_session)):
    return await SMSRepository(session).list_outbound()
