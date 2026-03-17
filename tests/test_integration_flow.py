from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_farmer_creation_and_alert_generation_flow(client):
    farmer_payload = {
        "full_name": "API Farmer",
        "phone_number": "+255700111114",
        "preferred_language": "sw",
        "region": "Arusha",
        "district": "Meru",
        "village": "Usa River",
        "latitude": -3.369,
        "longitude": 36.8569,
        "crop_type": "Maize",
        "is_active": True,
    }

    farmer_response = await client.post("/api/v1/farmers", json=farmer_payload)
    assert farmer_response.status_code == 201
    farmer = farmer_response.json()

    evaluate_response = await client.post(
        "/api/v1/alerts/evaluate",
        json={"farmer_id": farmer["id"], "force_send": True},
    )
    assert evaluate_response.status_code == 200
    evaluation = evaluate_response.json()
    assert evaluation["alerts_created"] >= 1
    assert evaluation["sms_sent"] >= 1

    alerts_response = await client.get("/api/v1/alerts")
    sms_log_response = await client.get("/api/v1/simulation/sms-log")

    assert alerts_response.status_code == 200
    assert sms_log_response.status_code == 200
    assert len(alerts_response.json()) >= 1
    assert len(sms_log_response.json()) >= 1
