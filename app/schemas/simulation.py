from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AlertSeverity, PreferredLanguage, SimulationEventType, SimulationStatus


class SimulationEventCreate(BaseModel):
    event_type: SimulationEventType
    severity: AlertSeverity
    target_region: str | None = None
    target_farmer_id: int | None = None
    starts_in_minutes: int = Field(default=0, ge=0)
    starts_at: datetime | None = None
    sms_delay_seconds: int = Field(default=0, ge=0)
    language: PreferredLanguage = PreferredLanguage.EN
    custom_message: str | None = Field(default=None, max_length=320)


class SimulationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: SimulationEventType
    severity: AlertSeverity
    target_region: str | None
    target_farmer_id: int | None
    language: PreferredLanguage
    starts_at: datetime
    trigger_after_minutes: int
    sms_delay_seconds: int
    custom_message: str | None
    status: SimulationStatus
    created_at: datetime
    updated_at: datetime


class SimulationTriggerResponse(BaseModel):
    event_id: int
    status: SimulationStatus
    alerts_created: int
    sms_sent: int


class SimulationResetResponse(BaseModel):
    deleted_events: int
    deleted_alerts: int
    deleted_sms: int
    deleted_feedback: int
    deleted_observations: int
