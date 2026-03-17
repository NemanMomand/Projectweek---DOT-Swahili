from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, PreferredLanguage, SimulationEventType


class IntakeSubmissionRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    phone_number: str
    preferred_language: PreferredLanguage = PreferredLanguage.SW
    region: str = Field(min_length=2, max_length=120)
    district: str = Field(min_length=2, max_length=120)
    village: str = Field(min_length=2, max_length=120)
    latitude: float
    longitude: float
    crop_type: str = Field(min_length=2, max_length=120)
    event_type: SimulationEventType = SimulationEventType.STORM
    severity: AlertSeverity = AlertSeverity.WARNING
    event_starts_at: datetime
    custom_message: str | None = Field(default=None, max_length=320)


class IntakeSubmissionResponse(BaseModel):
    farmer_id: int
    simulation_event_id: int
    scheduled_alert_for: datetime
    lead_minutes: int
