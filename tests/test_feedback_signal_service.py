async def test_feedback_threshold_triggers_alert_and_sms(client):
    farmer_payload = {
        "full_name": "Signal Farmer",
        "phone_number": "+255700000321",
        "preferred_language": "sw",
        "region": "Arusha",
        "district": "Meru",
        "village": "Usa River",
        "latitude": -3.36,
        "longitude": 36.85,
        "crop_type": "Maize",
        "is_active": True,
    }
    farmer = await client.post("/api/v1/farmers", json=farmer_payload)
    assert farmer.status_code == 201

    headers = {"x-webhook-token": "local-webhook-token"}
    first = await client.post(
        "/api/v1/sms/reply",
        headers=headers,
        json={"phone_number": farmer_payload["phone_number"], "body": "Mvua kubwa"},
    )
    second = await client.post(
        "/api/v1/sms/reply",
        headers=headers,
        json={"phone_number": farmer_payload["phone_number"], "body": "Mvuaa kubwa sana"},
    )

    alerts = await client.get(
        "/api/v1/messages/alerts",
        params={"phone_number": farmer_payload["phone_number"]},
    )
    outbound = await client.get(
        "/api/v1/messages/sms",
        params={"phone_number": farmer_payload["phone_number"]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert alerts.status_code == 200
    assert outbound.status_code == 200
    assert len(alerts.json()) >= 1
    assert len(outbound.json()) >= 1
