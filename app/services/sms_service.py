from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import SMSDirection, SMSStatus, SimulationStatus
from app.models.simulation_event import SimulationEvent
from app.models.sms_message import SMSMessage
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.sms_repository import SMSRepository

logger = get_logger(__name__)


@dataclass
class SMSProviderResult:
    provider_message_id: str
    status: SMSStatus
    raw_payload: dict


class SMSProvider(Protocol):
    async def send(self, phone_number: str, body: str) -> SMSProviderResult: ...


class MockSMSProvider:
    async def send(self, phone_number: str, body: str) -> SMSProviderResult:
        message_id = f"mock-{uuid4().hex[:16]}"
        return SMSProviderResult(
            provider_message_id=message_id,
            status=SMSStatus.SENT,
            raw_payload={"provider": "mock", "phone_number": phone_number, "body": body},
        )


class TwilioSMSProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send(self, phone_number: str, body: str) -> SMSProviderResult:
        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/{self.settings.twilio_account_sid}/Messages.json"
        )
        data = {
            "To": phone_number,
            "Body": body,
            "MessagingServiceSid": self.settings.twilio_messaging_service_sid,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.post(
                url,
                data=data,
                auth=(self.settings.twilio_account_sid or "", self.settings.twilio_auth_token or ""),
            )
            response.raise_for_status()
            payload = response.json()
        return SMSProviderResult(
            provider_message_id=payload["sid"],
            status=SMSStatus.SENT,
            raw_payload=payload,
        )


class SMSService:
    def __init__(self, provider: SMSProvider | None = None) -> None:
        self.provider = provider or get_sms_provider()

    async def send_message(
        self,
        session: AsyncSession,
        phone_number: str,
        body: str,
        simulation_event_id: int | None = None,
    ) -> SMSMessage:
        repository = SMSRepository(session)
        try:
            result = await self.provider.send(phone_number=phone_number, body=body)
            message = SMSMessage(
                provider_message_id=result.provider_message_id,
                direction=SMSDirection.OUTBOUND,
                phone_number=phone_number,
                body=body,
                status=result.status,
                sent_at=datetime.now(UTC),
                raw_payload=result.raw_payload,
            )
            await repository.create(message)
            if simulation_event_id is not None:
                simulation_event = await SimulationRepository(session).get(simulation_event_id)
                if simulation_event is not None:
                    simulation_event.status = SimulationStatus.SMS_SENT
            await session.commit()
            return message
        except httpx.HTTPError as exc:
            logger.exception("sms_send_failed", extra={"phone_number": phone_number, "error": str(exc)})
            message = SMSMessage(
                provider_message_id=f"failed-{uuid4().hex[:16]}",
                direction=SMSDirection.OUTBOUND,
                phone_number=phone_number,
                body=body,
                status=SMSStatus.FAILED,
                sent_at=datetime.now(UTC),
                raw_payload={"error": str(exc)},
            )
            await repository.create(message)
            await session.commit()
            return message

    async def record_inbound(
        self,
        session: AsyncSession,
        provider_message_id: str,
        phone_number: str,
        body: str,
        raw_payload: dict,
        received_at: datetime | None = None,
    ) -> tuple[SMSMessage, bool]:
        repository = SMSRepository(session)
        existing = await repository.get_by_provider_message_id(provider_message_id)
        if existing is not None:
            return existing, True
        message = SMSMessage(
            provider_message_id=provider_message_id,
            direction=SMSDirection.INBOUND,
            phone_number=phone_number,
            body=body,
            status=SMSStatus.RECEIVED,
            received_at=received_at or datetime.now(UTC),
            raw_payload=raw_payload,
        )
        await repository.create(message)
        await session.commit()
        return message, False

    async def update_status(self, session: AsyncSession, provider_message_id: str, status: SMSStatus, raw_payload: dict) -> SMSMessage | None:
        repository = SMSRepository(session)
        message = await repository.get_by_provider_message_id(provider_message_id)
        if message is None:
            return None
        message.status = status
        message.raw_payload = {**message.raw_payload, **raw_payload}
        await session.commit()
        await session.refresh(message)
        return message


def get_sms_provider() -> SMSProvider:
    settings = get_settings()
    if (
        settings.sms_provider == "twilio"
        and settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_messaging_service_sid
    ):
        return TwilioSMSProvider()
    return MockSMSProvider()
