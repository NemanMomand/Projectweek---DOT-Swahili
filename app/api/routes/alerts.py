from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertEvaluationResponse, AlertRead, EvaluateAlertsRequest
from app.services.alert_engine import AlertEngine

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post("/evaluate", response_model=AlertEvaluationResponse)
async def evaluate_alerts(payload: EvaluateAlertsRequest, session: AsyncSession = Depends(get_session)):
    result = await AlertEngine().evaluate_all(
        session,
        farmer_id=payload.farmer_id,
        dispatch_sms=payload.force_send,
    )
    return AlertEvaluationResponse(**result)


@router.get("", response_model=list[AlertRead])
async def list_alerts(session: AsyncSession = Depends(get_session)):
    return await AlertRepository(session).list()
