from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FeedbackType, PreferredLanguage


class ParseFeedbackRequest(BaseModel):
    body: str
    language_hint: PreferredLanguage | None = None


class ParsedFeedback(BaseModel):
    feedback_type: FeedbackType
    intensity: int | None = None
    parsed_language: PreferredLanguage | None = None
    normalized_text: str


class FarmerFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_id: int | None
    sms_message_id: int
    feedback_type: FeedbackType
    intensity: int | None
    free_text: str
    parsed_language: PreferredLanguage | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
