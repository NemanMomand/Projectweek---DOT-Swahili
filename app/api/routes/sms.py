from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.security import verify_webhook_token
from app.models.farmer_feedback import FarmerFeedback
from app.models.enums import SMSStatus
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.sms import (
    InboundSMSWebhook,
    MobileReplyRequest,
    SendSMSRequest,
    SendSMSResponse,
    SMSMessageRead,
    SMSStatusWebhook,
)
from app.services.feedback_parser import FeedbackParser
from app.services.weather_feedback_signal_service import WeatherFeedbackSignalService
from app.services.sms_service import SMSService

router = APIRouter(prefix="/api/v1/sms", tags=["sms"])


def _map_twilio_status(status_value: str | None):
    normalized = (status_value or "").strip().lower()
    if normalized in {"queued", "accepted", "sending", "sent"}:
        return "sent"
    if normalized in {"delivered", "read"}:
        return "delivered"
    if normalized in {"received", "receiving"}:
        return "received"
    if normalized in {"failed", "undelivered", "canceled"}:
        return "failed"
    return "sent"


async def _store_inbound_message(
    session: AsyncSession,
    provider_message_id: str,
    phone_number: str,
    body: str,
    raw_payload: dict,
):
    sms_service = SMSService()
    parser = FeedbackParser()
    message, duplicate = await sms_service.record_inbound(
        session=session,
        provider_message_id=provider_message_id,
        phone_number=phone_number,
        body=body,
        raw_payload=raw_payload,
        received_at=None,
    )
    farmer = await FarmerRepository(session).get_by_phone(phone_number)
    if not duplicate:
        parsed = parser.parse(body)
        feedback = FarmerFeedback(
            farmer_id=farmer.id if farmer else None,
            sms_message_id=message.id,
            feedback_type=parsed.feedback_type,
            intensity=parsed.intensity,
            free_text=body,
            parsed_language=parsed.parsed_language,
            latitude=farmer.latitude if farmer else None,
            longitude=farmer.longitude if farmer else None,
        )
        await FeedbackRepository(session).create(feedback)
        await WeatherFeedbackSignalService().evaluate_and_notify(
            session=session,
            farmer=farmer,
            message_text=body,
            language_hint=parsed.parsed_language,
        )
        await session.commit()
    return {"status": "accepted", "duplicate": duplicate, "message_id": message.id}


@router.post("/send", response_model=SendSMSResponse)
async def send_sms(payload: SendSMSRequest, session: AsyncSession = Depends(get_session)):
    message = await SMSService().send_message(session, payload.phone_number, payload.body)
    return SendSMSResponse(provider_message_id=message.provider_message_id or "", status=message.status)


@router.post("/webhooks/inbound")
async def receive_inbound_sms(
    payload: InboundSMSWebhook,
    session: AsyncSession = Depends(get_session),
    _verified: None = Depends(verify_webhook_token),
):
    return await _store_inbound_message(
        session=session,
        provider_message_id=payload.provider_message_id,
        phone_number=payload.phone_number,
        body=payload.body,
        raw_payload=payload.raw_payload,
    )


@router.post("/webhooks/status", response_model=SMSMessageRead)
async def receive_sms_status(
    payload: SMSStatusWebhook,
    session: AsyncSession = Depends(get_session),
    _verified: None = Depends(verify_webhook_token),
):
    message = await SMSService().update_status(session, payload.provider_message_id, payload.status, payload.raw_payload)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS message not found")
    return message


@router.post("/twilio/inbound")
async def receive_twilio_inbound_sms(
    session: AsyncSession = Depends(get_session),
    MessageSid: str | None = Form(default=None),
    SmsSid: str | None = Form(default=None),
    From: str = Form(...),
    Body: str = Form(...),
    To: str | None = Form(default=None),
    AccountSid: str | None = Form(default=None),
    NumMedia: str | None = Form(default=None),
):
    payload = {
        "MessageSid": MessageSid,
        "SmsSid": SmsSid,
        "From": From,
        "To": To,
        "Body": Body,
        "AccountSid": AccountSid,
        "NumMedia": NumMedia,
        "provider": "twilio",
    }
    await _store_inbound_message(
        session=session,
        provider_message_id=MessageSid or SmsSid or f"twilio-in-{uuid4().hex[:16]}",
        phone_number=From,
        body=Body,
        raw_payload=payload,
    )
    return Response(content="<Response></Response>", media_type="application/xml")


@router.post("/twilio/status")
async def receive_twilio_status(
    session: AsyncSession = Depends(get_session),
    MessageSid: str | None = Form(default=None),
    SmsSid: str | None = Form(default=None),
    MessageStatus: str | None = Form(default=None),
    SmsStatus: str | None = Form(default=None),
    ErrorCode: str | None = Form(default=None),
    ErrorMessage: str | None = Form(default=None),
    To: str | None = Form(default=None),
    From: str | None = Form(default=None),
):
    provider_message_id = MessageSid or SmsSid
    if provider_message_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing provider message id")
    mapped_status = SMSStatus(_map_twilio_status(MessageStatus or SmsStatus))
    message = await SMSService().update_status(
        session,
        provider_message_id,
        mapped_status,
        {
            "provider": "twilio",
            "MessageSid": MessageSid,
            "SmsSid": SmsSid,
            "MessageStatus": MessageStatus,
            "SmsStatus": SmsStatus,
            "ErrorCode": ErrorCode,
            "ErrorMessage": ErrorMessage,
            "To": To,
            "From": From,
        },
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS message not found")
    return {"status": "accepted", "message_id": message.id, "message_status": mapped_status.value}


@router.post("/reply")
async def submit_mobile_reply(
    payload: MobileReplyRequest,
    session: AsyncSession = Depends(get_session),
    _verified: None = Depends(verify_webhook_token),
):
    provider_message_id = payload.provider_message_id or f"app-{uuid4().hex[:16]}"
    return await _store_inbound_message(
        session=session,
        provider_message_id=provider_message_id,
        phone_number=payload.phone_number,
        body=payload.body,
        raw_payload=payload.raw_payload,
    )
