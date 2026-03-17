from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertType, DeliveryStatus, PreferredLanguage


class EvaluateAlertsRequest(BaseModel):
    farmer_id: int | None = None
    force_send: bool = True


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_id: int
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    language: PreferredLanguage
    scheduled_for: datetime
    sent_at: datetime | None
    delivery_status: DeliveryStatus
    source_observation_id: int | None
    simulation_event_id: int | None
    created_at: datetime
    updated_at: datetime


class AlertEvaluationResponse(BaseModel):
    checked_farmers: int
    observations_created: int
    alerts_created: int
    sms_sent: int
