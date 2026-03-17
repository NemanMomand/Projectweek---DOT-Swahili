from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.config import get_settings
from app.core.security import check_phone_rate_limit, verify_webhook_token
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


def _looks_like_short_code(value: str | None) -> bool:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return 3 <= len(digits) <= 6


def _looks_like_msisdn(value: str | None) -> bool:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return len(digits) >= 8


def _resolve_inbound_sender(from_value: str | None, to_value: str | None) -> str:
    from_clean = (from_value or "").strip()
    to_clean = (to_value or "").strip()

    # Some gateways can send shortcode in From and handset in To.
    if _looks_like_short_code(from_clean) and _looks_like_msisdn(to_clean):
        return to_clean

    if from_clean:
        return from_clean
    if to_clean:
        return to_clean
    return ""


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
    *,
    require_registered: bool = False,
):
    # Threat 1: optionally reject messages from unregistered numbers
    farmer = await FarmerRepository(session).get_by_phone(phone_number)
    if require_registered and (farmer is None or not farmer.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone number not registered as an active farmer",
        )

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


def _verify_twilio_signature(request: Request, settings) -> bool:
    """Threat 2: Validate that the request genuinely came from Twilio.
    Requires TWILIO_AUTH_TOKEN to be set. Skipped in development if token not configured."""
    try:
        from twilio.request_validator import RequestValidator  # type: ignore
    except ImportError:
        return True  # twilio library not installed — skip in development

    auth_token = settings.twilio_auth_token
    if not auth_token:
        return True  # not configured — skip (development mode)

    signature = request.headers.get("X-Twilio-Signature", "")
    # Build the full URL as Twilio would see it
    url = str(request.url)
    validator = RequestValidator(auth_token)
    return validator.validate(url, {}, signature)


@router.post("/twilio/inbound")
async def receive_twilio_inbound_sms(
    request: Request,
    session: AsyncSession = Depends(get_session),
    MessageSid: str | None = Form(default=None),
    SmsSid: str | None = Form(default=None),
    From: str = Form(...),
    Body: str = Form(...),
    To: str | None = Form(default=None),
    AccountSid: str | None = Form(default=None),
    NumMedia: str | None = Form(default=None),
):
    settings = get_settings()

    # Threat 2: Verify the request signature (proves it came from Twilio, not a spoofer)
    if not _verify_twilio_signature(request, settings):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")

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
    sender_phone = _resolve_inbound_sender(From, To)
    if not sender_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing sender phone number")

    # Threat 2: Rate limit per phone number (max 10 messages per 10 minutes)
    check_phone_rate_limit(sender_phone)

    await _store_inbound_message(
        session=session,
        provider_message_id=MessageSid or SmsSid or f"twilio-in-{uuid4().hex[:16]}",
        phone_number=sender_phone,
        body=Body,
        raw_payload={**payload, "resolved_phone_number": sender_phone},
        require_registered=False,  # Set True to enforce Threat 1 on live Twilio endpoint
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
