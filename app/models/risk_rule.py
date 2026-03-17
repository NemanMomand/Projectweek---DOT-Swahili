from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, json_type
from app.models.enums import AlertType


class RiskRule(Base, IdMixin, TimestampMixin):
    __tablename__ = "risk_rules"

    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType, native_enum=False), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(json_type, nullable=False)
