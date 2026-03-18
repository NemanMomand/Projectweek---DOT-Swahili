from __future__ import annotations

from pydantic import BaseModel, Field


class VoiceCallRequest(BaseModel):
    phone_number: str
    message_en: str = Field(default="This is Dot Swahili. Weather warning for your farm area.", min_length=3, max_length=500)
    message_sw: str = Field(default="Hii ni Dot Swahili. Tahadhari ya hali ya hewa kwa eneo lako la shamba.", min_length=3, max_length=500)


class VoiceCallThenSMSRequest(VoiceCallRequest):
    sms_body: str = Field(
        default="DOT Swahili alert: please check the latest weather warning message.",
        min_length=3,
        max_length=320,
    )
    delay_seconds: int = Field(default=20, ge=0, le=120)


class VoiceCallResponse(BaseModel):
    call_sid: str
    status: str
    to: str
    from_number: str


class VoiceCallThenSMSResponse(BaseModel):
    call_sid: str
    call_status: str
    sms_provider_message_id: str
    sms_status: str
    to: str
