from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models.farmer import Farmer
from app.models.enums import AlertType, PreferredLanguage
from app.models.risk_rule import RiskRule
from app.repositories.location_repository import LocationRepository

SAMPLE_FARMERS = [
    {
        "full_name": "Amina Juma",
        "phone_number": "+254700000001",
        "preferred_language": PreferredLanguage.SW,
        "region": "Arusha",
        "district": "Meru",
        "village": "Usa River",
        "latitude": -3.3690,
        "longitude": 36.8569,
        "crop_type": "Maize",
        "is_active": True,
    },
    {
        "full_name": "John Okello",
        "phone_number": "+256700000002",
        "preferred_language": PreferredLanguage.EN,
        "region": "Eastern",
        "district": "Mbale",
        "village": "Busoba",
        "latitude": 1.0820,
        "longitude": 34.1750,
        "crop_type": "Coffee",
        "is_active": True,
    },
    {
        "full_name": "Neema Hassan",
        "phone_number": "+255700000003",
        "preferred_language": PreferredLanguage.SW,
        "region": "Kilimanjaro",
        "district": "Moshi Rural",
        "village": "Mabogini",
        "latitude": -3.3349,
        "longitude": 37.3404,
        "crop_type": "Beans",
        "is_active": True,
    },
]

DEFAULT_RULES = [
    {"name": "heavy-rain-24h", "alert_type": AlertType.RAIN, "config": {"threshold_mm": 35}},
    {"name": "drought-72h", "alert_type": AlertType.DROUGHT, "config": {"threshold_mm": 5}},
    {"name": "heat-stress", "alert_type": AlertType.HEAT, "config": {"threshold_c": 34}},
    {"name": "storm-wind", "alert_type": AlertType.STORM, "config": {"threshold_kph": 45}},
]


async def seed_data() -> None:
    settings = get_settings()
    if not settings.seed_sample_data:
        return
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        farmer_count = await session.scalar(select(func.count()).select_from(Farmer))
        if not farmer_count:
            for farmer_data in SAMPLE_FARMERS:
                farmer = Farmer(**farmer_data)
                session.add(farmer)
                await LocationRepository(session).get_or_create(
                    region=farmer.region,
                    district=farmer.district,
                    village=farmer.village,
                    latitude=farmer.latitude,
                    longitude=farmer.longitude,
                )
        for rule_data in DEFAULT_RULES:
            existing = await session.execute(select(RiskRule).where(RiskRule.name == rule_data["name"]))
            if existing.scalar_one_or_none() is None:
                session.add(
                    RiskRule(
                        name=rule_data["name"],
                        alert_type=rule_data["alert_type"],
                        enabled=True,
                        config=rule_data["config"],
                    )
                )
        await session.commit()


async def main() -> None:
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())
