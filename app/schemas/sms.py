from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SMSDirection, SMSStatus


class SendSMSRequest(BaseModel):
    phone_number: str
    body: str = Field(min_length=3, max_length=320)


class SendSMSResponse(BaseModel):
    provider_message_id: str
    status: SMSStatus


class InboundSMSWebhook(BaseModel):
    provider_message_id: str
    phone_number: str
    body: str
    received_at: datetime | None = None
    raw_payload: dict = Field(default_factory=dict)


class MobileReplyRequest(BaseModel):
    phone_number: str
    body: str = Field(min_length=3, max_length=320)
    provider_message_id: str | None = None
    raw_payload: dict = Field(default_factory=dict)


class SMSStatusWebhook(BaseModel):
    provider_message_id: str
    status: SMSStatus
    raw_payload: dict = Field(default_factory=dict)


class SMSMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_message_id: str | None
    direction: SMSDirection
    phone_number: str
    body: str
    status: SMSStatus
    received_at: datetime | None
    sent_at: datetime | None
    raw_payload: dict
    created_at: datetime
