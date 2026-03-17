from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.alert_repository import AlertRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.sms_repository import SMSRepository
from app.schemas.alert import AlertRead
from app.schemas.sms import SMSMessageRead

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


@router.get("/alerts", response_model=list[AlertRead])
async def list_alert_messages(
    session: AsyncSession = Depends(get_session),
    farmer_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    real_only: bool = Query(default=False),
):
    if farmer_id is not None:
        return await AlertRepository(session).list_for_farmer(farmer_id, real_only=real_only)
    if phone_number is not None:
        farmer = await FarmerRepository(session).get_by_phone(phone_number)
        if farmer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
        return await AlertRepository(session).list_for_farmer(farmer.id, real_only=real_only)
    return await AlertRepository(session).list(real_only=real_only)


@router.get("/sms", response_model=list[SMSMessageRead])
async def list_sms_messages(
    session: AsyncSession = Depends(get_session),
    phone_number: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    real_only: bool = Query(default=False),
):
    if phone_number:
        return await SMSRepository(session).list_outbound_for_phone(phone_number, real_only=real_only)
    return await SMSRepository(session).list_outbound_recent(limit=limit, real_only=real_only)


@router.get("/replies", response_model=list[SMSMessageRead])
async def list_sms_replies(
    session: AsyncSession = Depends(get_session),
    phone_number: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    real_only: bool = Query(default=False),
):
    if phone_number:
        return await SMSRepository(session).list_inbound_for_phone(phone_number, real_only=real_only)
    return await SMSRepository(session).list_inbound_recent(limit=limit, real_only=real_only)
