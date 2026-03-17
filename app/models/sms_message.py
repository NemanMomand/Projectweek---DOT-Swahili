from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin, json_type
from app.models.enums import SMSDirection, SMSStatus


class SMSMessage(Base, IdMixin, TimestampMixin):
    __tablename__ = "sms_messages"

    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    direction: Mapped[SMSDirection] = mapped_column(Enum(SMSDirection, native_enum=False), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SMSStatus] = mapped_column(Enum(SMSStatus, native_enum=False), nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(json_type, nullable=False)

    feedback_entries = relationship("FarmerFeedback", back_populates="sms_message")
