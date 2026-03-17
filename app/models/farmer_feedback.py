from __future__ import annotations

from sqlalchemy import Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import FeedbackType, PreferredLanguage


class FarmerFeedback(Base, IdMixin, TimestampMixin):
    __tablename__ = "farmer_feedback"

    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"), nullable=True)
    sms_message_id: Mapped[int] = mapped_column(
        ForeignKey("sms_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType, native_enum=False),
        nullable=False,
        default=FeedbackType.UNKNOWN,
    )
    intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    free_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_language: Mapped[PreferredLanguage | None] = mapped_column(
        Enum(PreferredLanguage, native_enum=False),
        nullable=True,
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    farmer = relationship("Farmer", back_populates="feedback_entries")
    sms_message = relationship("SMSMessage", back_populates="feedback_entries")
