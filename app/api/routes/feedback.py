from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FarmerFeedbackRead, ParseFeedbackRequest, ParsedFeedback
from app.services.feedback_parser import FeedbackParser

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.get("", response_model=list[FarmerFeedbackRead])
async def list_feedback(session: AsyncSession = Depends(get_session)):
    return await FeedbackRepository(session).list()


@router.post("/parse", response_model=ParsedFeedback)
async def parse_feedback(payload: ParseFeedbackRequest):
    return FeedbackParser().parse(payload.body, payload.language_hint)
