from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SMSDirection
from app.models.sms_message import SMSMessage


class SMSRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, message: SMSMessage) -> SMSMessage:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_by_provider_message_id(self, provider_message_id: str) -> SMSMessage | None:
        result = await self.session.execute(
            select(SMSMessage).where(SMSMessage.provider_message_id == provider_message_id)
        )
        return result.scalar_one_or_none()

    async def list_outbound(self) -> list[SMSMessage]:
        result = await self.session.execute(
            select(SMSMessage)
            .where(SMSMessage.direction == SMSDirection.OUTBOUND)
            .order_by(SMSMessage.created_at.desc(), SMSMessage.id.desc())
        )
        return list(result.scalars().all())

    def _apply_real_only_filter(self, query, real_only: bool):
        if not real_only:
            return query
        return query.where(
            SMSMessage.provider_message_id.is_not(None),
            ~SMSMessage.provider_message_id.like("mock-%"),
            ~SMSMessage.provider_message_id.like("app-%"),
            ~SMSMessage.provider_message_id.like("SMlocaltest%"),
        )

    async def list_outbound_for_phone(self, phone_number: str, real_only: bool = False) -> list[SMSMessage]:
        query = (
            select(SMSMessage)
            .where(SMSMessage.direction == SMSDirection.OUTBOUND, SMSMessage.phone_number == phone_number)
        )
        query = self._apply_real_only_filter(query, real_only)
        result = await self.session.execute(query.order_by(SMSMessage.created_at.desc(), SMSMessage.id.desc()))
        return list(result.scalars().all())

    async def list_outbound_recent(self, limit: int = 100, real_only: bool = False) -> list[SMSMessage]:
        query = select(SMSMessage).where(SMSMessage.direction == SMSDirection.OUTBOUND)
        query = self._apply_real_only_filter(query, real_only)
        result = await self.session.execute(
            query.order_by(SMSMessage.created_at.desc(), SMSMessage.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_inbound_for_phone(self, phone_number: str, real_only: bool = False) -> list[SMSMessage]:
        query = (
            select(SMSMessage)
            .where(SMSMessage.direction == SMSDirection.INBOUND, SMSMessage.phone_number == phone_number)
        )
        query = self._apply_real_only_filter(query, real_only)
        result = await self.session.execute(query.order_by(SMSMessage.created_at.desc(), SMSMessage.id.desc()))
        return list(result.scalars().all())

    async def list_inbound_recent(self, limit: int = 100, real_only: bool = False) -> list[SMSMessage]:
        query = select(SMSMessage).where(SMSMessage.direction == SMSDirection.INBOUND)
        query = self._apply_real_only_filter(query, real_only)
        result = await self.session.execute(
            query.order_by(SMSMessage.created_at.desc(), SMSMessage.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, message: SMSMessage, status) -> SMSMessage:
        message.status = status
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def delete_all(self) -> int:
        result = await self.session.execute(delete(SMSMessage))
        return result.rowcount or 0
