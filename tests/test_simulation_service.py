from __future__ import annotations

import pytest

from app.models.enums import AlertSeverity, PreferredLanguage, SimulationStatus, SimulationEventType
from app.models.farmer import Farmer
from app.repositories.alert_repository import AlertRepository
from app.repositories.sms_repository import SMSRepository
from app.schemas.simulation import SimulationEventCreate
from app.services.simulation_service import SimulationService


@pytest.mark.asyncio
async def test_simulation_event_processing_creates_alert_and_sms(session):
    farmer = Farmer(
        full_name="Simulation Farmer",
        phone_number="+255700111113",
        preferred_language=PreferredLanguage.EN,
        region="Kilimanjaro",
        district="Moshi Rural",
        village="Mabogini",
        latitude=-3.3349,
        longitude=37.3404,
        crop_type="Coffee",
        is_active=True,
    )
    session.add(farmer)
    await session.commit()

    service = SimulationService()
    event = await service.create_event(
        session,
        SimulationEventCreate(
            event_type=SimulationEventType.STORM,
            severity=AlertSeverity.CRITICAL,
            target_farmer_id=farmer.id,
            starts_in_minutes=0,
            sms_delay_seconds=0,
            language=PreferredLanguage.EN,
        ),
    )
    result = await service.trigger_event(session, event)
    alerts = await AlertRepository(session).list()
    sms_log = await SMSRepository(session).list_outbound()
    refreshed = await service.get_event(session, event.id)

    assert result["alerts_created"] == 1
    assert result["sms_sent"] == 1
    assert len(alerts) == 1
    assert len(sms_log) == 1
    assert refreshed is not None
    assert refreshed.status == SimulationStatus.SMS_SENT
