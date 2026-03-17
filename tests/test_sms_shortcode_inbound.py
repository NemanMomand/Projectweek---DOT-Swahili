from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_twilio_inbound_resolves_phone_when_from_is_shortcode(client):
    farmer_payload = {
        "full_name": "Shortcode Farmer",
        "phone_number": "+255700999555",
        "preferred_language": "sw",
        "region": "Arusha",
        "district": "Meru",
        "village": "Usa River",
        "latitude": -3.369,
        "longitude": 36.8569,
        "crop_type": "Maize",
        "is_active": True,
    }
    created = await client.post("/api/v1/farmers", json=farmer_payload)
    assert created.status_code == 201

    inbound = await client.post(
        "/api/v1/sms/twilio/inbound",
        data={
            "MessageSid": "SM-shortcode-1",
            "From": "8128",
            "To": farmer_payload["phone_number"],
            "Body": "Mvua kubwa",
        },
    )
    assert inbound.status_code == 200

    replies = await client.get(
        "/api/v1/messages/replies",
        params={"phone_number": farmer_payload["phone_number"]},
    )
    assert replies.status_code == 200
    assert len(replies.json()) >= 1
