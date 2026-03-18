from __future__ import annotations

import asyncio
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import SMSStatus
from app.services.sms_service import SMSService


def _normalize_phone(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("+"):
        return "+" + "".join(ch for ch in value if ch.isdigit())
    return "".join(ch for ch in value if ch.isdigit())


def _is_allowed_number(phone_number: str) -> bool:
    settings = get_settings()
    raw_allowlist = (settings.sms_allowed_numbers or "").strip()
    if not raw_allowlist:
        return True
    requested = _normalize_phone(phone_number)
    allowed = {
        _normalize_phone(item)
        for item in raw_allowlist.split(",")
        if item and item.strip()
    }
    return requested in allowed


@dataclass
class VoiceCallResult:
    call_sid: str
    status: str
    to: str
    from_number: str


class TwilioVoiceService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _require_configured(self) -> None:
        if not self.settings.voice_enabled:
            raise ValueError("Voice is disabled (VOICE_ENABLED=false).")
        if not self.settings.twilio_account_sid or not self.settings.twilio_auth_token:
            raise ValueError("Twilio credentials missing for voice calls.")
        if not self.settings.twilio_voice_from_number:
            raise ValueError("TWILIO_VOICE_FROM_NUMBER is not configured.")

    async def create_call(self, phone_number: str, message_en: str, message_sw: str) -> VoiceCallResult:
        self._require_configured()
        if not _is_allowed_number(phone_number):
            raise ValueError("Voice call blocked: phone number is not in SMS_ALLOWED_NUMBERS.")

        account_sid = self.settings.twilio_account_sid or ""
        auth_token = self.settings.twilio_auth_token or ""

        twiml_url = (
            f"{self.settings.twilio_voice_twiml_url}"
            f"?message_en={quote_plus(message_en)}&message_sw={quote_plus(message_sw)}"
        )
        data = {
            "To": phone_number,
            "From": self.settings.twilio_voice_from_number,
            "Url": twiml_url,
            "Method": "POST",
            "StatusCallback": self.settings.twilio_voice_status_callback_url,
            "StatusCallbackMethod": "POST",
            "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
        }
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            response = await client.post(url, data=data, auth=(account_sid, auth_token))
            response.raise_for_status()
            payload = response.json()

        return VoiceCallResult(
            call_sid=payload["sid"],
            status=str(payload.get("status") or "queued"),
            to=str(payload.get("to") or phone_number),
            from_number=str(payload.get("from") or self.settings.twilio_voice_from_number),
        )


async def call_then_sms(
    session: AsyncSession,
    phone_number: str,
    message_en: str,
    message_sw: str,
    sms_body: str,
    delay_seconds: int,
) -> tuple[VoiceCallResult, str, SMSStatus]:
    voice = TwilioVoiceService()
    sms = SMSService()

    call_result = await voice.create_call(
        phone_number=phone_number,
        message_en=message_en,
        message_sw=message_sw,
    )

    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    sms_message = await sms.send_message(session=session, phone_number=phone_number, body=sms_body)
    return call_result, sms_message.provider_message_id or "", sms_message.status
