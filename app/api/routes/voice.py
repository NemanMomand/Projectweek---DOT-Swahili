from __future__ import annotations

from html import escape

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.schemas.voice import (
    VoiceCallRequest,
    VoiceCallResponse,
    VoiceCallThenSMSRequest,
    VoiceCallThenSMSResponse,
)
from app.services.voice_service import TwilioVoiceService, call_then_sms

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/call", response_model=VoiceCallResponse)
async def create_voice_call(payload: VoiceCallRequest) -> VoiceCallResponse:
    try:
        result = await TwilioVoiceService().create_call(
            phone_number=payload.phone_number,
            message_en=payload.message_en,
            message_sw=payload.message_sw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = "Twilio rejected the voice call request."
        try:
            payload = exc.response.json()
            twilio_message = payload.get("message")
            if twilio_message:
                detail = f"{detail} {twilio_message}"
        except ValueError:
            pass
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice provider request failed. Check Twilio connectivity and credentials.",
        ) from exc
    return VoiceCallResponse(
        call_sid=result.call_sid,
        status=result.status,
        to=result.to,
        from_number=result.from_number,
    )


@router.post("/call-then-sms", response_model=VoiceCallThenSMSResponse)
async def create_voice_call_then_sms(
    payload: VoiceCallThenSMSRequest,
    session: AsyncSession = Depends(get_session),
) -> VoiceCallThenSMSResponse:
    try:
        call_result, sms_provider_message_id, sms_status = await call_then_sms(
            session=session,
            phone_number=payload.phone_number,
            message_en=payload.message_en,
            message_sw=payload.message_sw,
            sms_body=payload.sms_body,
            delay_seconds=payload.delay_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = "Twilio rejected the call-then-sms request."
        try:
            payload = exc.response.json()
            twilio_message = payload.get("message")
            if twilio_message:
                detail = f"{detail} {twilio_message}"
        except ValueError:
            pass
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice provider request failed. Check Twilio connectivity and credentials.",
        ) from exc
    return VoiceCallThenSMSResponse(
        call_sid=call_result.call_sid,
        call_status=call_result.status,
        sms_provider_message_id=sms_provider_message_id,
        sms_status=sms_status.value,
        to=call_result.to,
    )


@router.post("/twiml")
async def voice_twiml(
    message_en: str = Form(default="This is Dot Swahili. Weather warning for your farm area."),
    message_sw: str = Form(default="Hii ni Dot Swahili. Tahadhari ya hali ya hewa kwa eneo lako la shamba."),
) -> Response:
    safe_en = escape(message_en)
    safe_sw = escape(message_sw)
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"<Say voice=\"alice\" language=\"en-US\">{safe_en}</Say>"
        "<Pause length=\"1\"/>"
        f"<Say voice=\"alice\" language=\"en-US\">{safe_sw}</Say>"
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def voice_status(
    CallSid: str | None = Form(default=None),
    CallStatus: str | None = Form(default=None),
    To: str | None = Form(default=None),
    From: str | None = Form(default=None),
    Direction: str | None = Form(default=None),
):
    return {
        "status": "accepted",
        "call_sid": CallSid,
        "call_status": CallStatus,
        "to": To,
        "from": From,
        "direction": Direction,
    }
