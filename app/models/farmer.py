from __future__ import annotations

from sqlalchemy import Boolean, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import PreferredLanguage


class Farmer(Base, IdMixin, TimestampMixin):
    __tablename__ = "farmers"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    preferred_language: Mapped[PreferredLanguage] = mapped_column(
        Enum(PreferredLanguage, native_enum=False),
        nullable=False,
        default=PreferredLanguage.SW,
    )
    region: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    village: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    crop_type: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    alerts = relationship("Alert", back_populates="farmer", cascade="all, delete-orphan")
    feedback_entries = relationship("FarmerFeedback", back_populates="farmer")
    simulation_events = relationship("SimulationEvent", back_populates="target_farmer")
