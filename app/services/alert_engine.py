from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.enums import (
    AlertSeverity,
    AlertType,
    DeliveryStatus,
    SimulationEventType,
    SimulationStatus,
    WeatherSource,
)
from app.models.farmer import Farmer
from app.models.simulation_event import SimulationEvent
from app.models.weather_observation import WeatherObservation
from app.repositories.alert_repository import AlertRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.risk_rule_repository import RiskRuleRepository
from app.repositories.weather_repository import WeatherRepository
from app.services.sms_service import SMSService
from app.services.translation_service import TranslationService
from app.services.weather_provider import ForecastSummary, WeatherService

logger = get_logger(__name__)


@dataclass
class AlertDecision:
    alert_type: AlertType
    severity: AlertSeverity


class AlertEngine:
    def __init__(
        self,
        weather_service: WeatherService | None = None,
        translation_service: TranslationService | None = None,
        sms_service: SMSService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.weather_service = weather_service or WeatherService()
        self.translation_service = translation_service or TranslationService()
        self.sms_service = sms_service or SMSService()

    async def evaluate_all(
        self,
        session: AsyncSession,
        farmer_id: int | None = None,
        dispatch_sms: bool = True,
    ) -> dict[str, int]:
        farmer_repo = FarmerRepository(session)
        farmers = []
        if farmer_id is not None:
            farmer = await farmer_repo.get(farmer_id)
            if farmer and farmer.is_active:
                farmers = [farmer]
        else:
            farmers = await farmer_repo.list_active()
        rule_config = await self._load_rule_config(session)
        alerts_created = 0
        observations_created = 0
        for farmer in farmers:
            summary = await self.weather_service.summarize_forecast(farmer.latitude, farmer.longitude)
            observation = WeatherObservation(
                source=summary.source,
                latitude=farmer.latitude,
                longitude=farmer.longitude,
                observed_at=summary.observed_at,
                rainfall_mm=summary.rainfall_24h_mm,
                temperature_c=summary.max_temperature_c,
                humidity_pct=summary.avg_humidity_pct,
                wind_speed_kph=summary.max_wind_speed_kph,
                soil_moisture_index=summary.soil_moisture_index,
                drought_risk_score=summary.drought_risk_score,
                raw_payload=summary.raw_payload,
            )
            await WeatherRepository(session).create(observation)
            observations_created += 1
            alerts_created += await self._create_alerts_for_observation(
                session=session,
                farmer=farmer,
                observation=observation,
                rule_config=rule_config,
            )
        await session.commit()
        sms_sent = await self.dispatch_pending_alerts(session) if dispatch_sms else 0
        return {
            "checked_farmers": len(farmers),
            "observations_created": observations_created,
            "alerts_created": alerts_created,
            "sms_sent": sms_sent,
        }

    async def process_simulation_event(self, session: AsyncSession, event: SimulationEvent) -> dict[str, int]:
        farmer_repo = FarmerRepository(session)
        rule_config = await self._load_rule_config(session)
        farmers = await farmer_repo.list_active()
        if event.target_farmer_id is not None:
            farmers = [farmer for farmer in farmers if farmer.id == event.target_farmer_id]
        elif event.target_region:
            farmers = [farmer for farmer in farmers if farmer.region.lower() == event.target_region.lower()]
        if not farmers:
            event.status = SimulationStatus.CANCELLED
            await session.commit()
            return {"alerts_created": 0, "sms_sent": 0}
        event.status = SimulationStatus.DETECTED
        scheduled_for = max(
            datetime.now(UTC),
            event.starts_at - timedelta(minutes=self.settings.alert_lead_minutes),
        )
        alerts_created = 0
        for farmer in farmers:
            observation = self._build_simulation_observation(farmer, event)
            await WeatherRepository(session).create(observation)
            alerts_created += await self._create_alerts_for_observation(
                session=session,
                farmer=farmer,
                observation=observation,
                rule_config=rule_config,
                forced_decision=self._map_simulation_event_to_alert(event),
                custom_message=event.custom_message,
                simulation_event_id=event.id,
                sms_delay_seconds=event.sms_delay_seconds,
                language_override=event.language,
                scheduled_for_override=scheduled_for,
            )
        if alerts_created == 0:
            event.status = SimulationStatus.SKIPPED_DUPLICATE
        else:
            event.status = SimulationStatus.ALERT_CREATED
        await session.commit()
        sms_sent = 0
        if alerts_created and scheduled_for <= datetime.now(UTC):
            sms_sent = await self.dispatch_pending_alerts(session, simulation_event_id=event.id)
        return {"alerts_created": alerts_created, "sms_sent": sms_sent}

    async def dispatch_pending_alerts(self, session: AsyncSession, simulation_event_id: int | None = None) -> int:
        now = datetime.now(UTC)
        query = select(Alert).where(Alert.sent_at.is_(None), Alert.scheduled_for <= now).order_by(Alert.id)
        if simulation_event_id is not None:
            query = query.where(Alert.simulation_event_id == simulation_event_id)
        result = await session.execute(query)
        alerts = list(result.scalars().all())
        sent_count = 0
        for alert in alerts:
            farmer = await FarmerRepository(session).get(alert.farmer_id)
            if farmer is None:
                continue
            sms_message = await self.sms_service.send_message(
                session=session,
                phone_number=farmer.phone_number,
                body=alert.message,
                simulation_event_id=alert.simulation_event_id,
            )
            alert.sent_at = datetime.now(UTC)
            alert.delivery_status = (
                DeliveryStatus.SENT if sms_message.status.value != "failed" else DeliveryStatus.FAILED
            )
            if alert.simulation_event_id is not None:
                event = await session.get(SimulationEvent, alert.simulation_event_id)
                if event is not None:
                    event.status = SimulationStatus.SMS_SENT
            sent_count += 1 if sms_message.status.value != "failed" else 0
        await session.commit()
        return sent_count

    async def _create_alerts_for_observation(
        self,
        session: AsyncSession,
        farmer: Farmer,
        observation: WeatherObservation,
        rule_config: dict[AlertType, dict],
        forced_decision: AlertDecision | None = None,
        custom_message: str | None = None,
        simulation_event_id: int | None = None,
        sms_delay_seconds: int = 0,
        language_override=None,
        scheduled_for_override: datetime | None = None,
    ) -> int:
        decisions = [forced_decision] if forced_decision else self._evaluate_rules(observation, rule_config)
        created = 0
        alert_repo = AlertRepository(session)
        cooldown_since = datetime.now(UTC) - timedelta(hours=self.settings.alert_cooldown_hours)
        for decision in [decision for decision in decisions if decision is not None]:
            duplicate = await alert_repo.find_recent_duplicate(farmer.id, decision.alert_type, cooldown_since)
            if duplicate is not None:
                logger.info(
                    "duplicate_alert_suppressed",
                    extra={"farmer_id": farmer.id, "alert_type": decision.alert_type.value},
                )
                continue
            language = language_override or farmer.preferred_language
            title, message = self.translation_service.render_alert(
                alert_type=decision.alert_type,
                severity=decision.severity,
                language=language,
                custom_message=custom_message,
            )
            alert = Alert(
                farmer_id=farmer.id,
                alert_type=decision.alert_type,
                severity=decision.severity,
                title=title,
                message=message,
                language=language,
                scheduled_for=(
                    scheduled_for_override
                    if scheduled_for_override is not None
                    else datetime.now(UTC) + timedelta(seconds=sms_delay_seconds)
                ),
                delivery_status=DeliveryStatus.PENDING,
                source_observation_id=observation.id,
                simulation_event_id=simulation_event_id,
            )
            await alert_repo.create(alert)
            created += 1
        return created

    async def _load_rule_config(self, session: AsyncSession) -> dict[AlertType, dict]:
        rules = await RiskRuleRepository(session).list_enabled()
        config: dict[AlertType, dict] = {
            AlertType.RAIN: {"threshold_mm": self.settings.rain_24h_threshold_mm},
            AlertType.DROUGHT: {"threshold_mm": self.settings.drought_72h_threshold_mm},
            AlertType.HEAT: {"threshold_c": self.settings.heat_threshold_c},
            AlertType.STORM: {"threshold_kph": self.settings.storm_wind_threshold_kph},
        }
        for rule in rules:
            config[rule.alert_type] = {**config.get(rule.alert_type, {}), **rule.config}
        return config

    def _evaluate_rules(
        self, observation: WeatherObservation, rule_config: dict[AlertType, dict]
    ) -> list[AlertDecision]:
        decisions: list[AlertDecision] = []
        rain_threshold = float(rule_config[AlertType.RAIN].get("threshold_mm", self.settings.rain_24h_threshold_mm))
        drought_threshold = float(
            rule_config[AlertType.DROUGHT].get("threshold_mm", self.settings.drought_72h_threshold_mm)
        )
        heat_threshold = float(rule_config[AlertType.HEAT].get("threshold_c", self.settings.heat_threshold_c))
        storm_threshold = float(
            rule_config[AlertType.STORM].get("threshold_kph", self.settings.storm_wind_threshold_kph)
        )
        if observation.rainfall_mm >= rain_threshold:
            severity = AlertSeverity.CRITICAL if observation.rainfall_mm >= rain_threshold * 1.5 else AlertSeverity.WARNING
            decisions.append(AlertDecision(AlertType.RAIN, severity))
        if observation.temperature_c >= heat_threshold:
            severity = AlertSeverity.CRITICAL if observation.temperature_c >= heat_threshold + 3 else AlertSeverity.WARNING
            decisions.append(AlertDecision(AlertType.HEAT, severity))
        if observation.wind_speed_kph >= storm_threshold:
            severity = AlertSeverity.CRITICAL if observation.wind_speed_kph >= storm_threshold + 15 else AlertSeverity.WARNING
            decisions.append(AlertDecision(AlertType.STORM, severity))
        drought_score = observation.drought_risk_score or 0.0
        if drought_score >= 0.8 or observation.rainfall_mm <= drought_threshold:
            severity = AlertSeverity.CRITICAL if drought_score >= 0.95 else AlertSeverity.WARNING
            decisions.append(AlertDecision(AlertType.DROUGHT, severity))
        return decisions

    def _build_simulation_observation(self, farmer: Farmer, event: SimulationEvent) -> WeatherObservation:
        payload = {
            "simulation": True,
            "event_id": event.id,
            "event_type": event.event_type.value,
            "severity": event.severity.value,
        }
        rainfall = 0.0
        temperature = 29.0
        humidity = 60.0
        wind = 12.0
        drought_score = 0.1
        if event.event_type == SimulationEventType.HEAVY_RAIN:
            rainfall = max(self.settings.rain_24h_threshold_mm + 10, 50.0)
            humidity = 92.0
        elif event.event_type == SimulationEventType.DROUGHT:
            rainfall = 0.0
            temperature = 33.0
            drought_score = 0.98
        elif event.event_type == SimulationEventType.HEAT:
            temperature = max(self.settings.heat_threshold_c + 3, 38.0)
            humidity = 38.0
        elif event.event_type == SimulationEventType.STORM:
            wind = max(self.settings.storm_wind_threshold_kph + 20, 65.0)
            rainfall = 18.0
            humidity = 88.0
        return WeatherObservation(
            source=WeatherSource.SIMULATION,
            latitude=farmer.latitude,
            longitude=farmer.longitude,
            observed_at=datetime.now(UTC),
            rainfall_mm=rainfall,
            temperature_c=temperature,
            humidity_pct=humidity,
            wind_speed_kph=wind,
            soil_moisture_index=0.2 if event.event_type == SimulationEventType.DROUGHT else 0.7,
            drought_risk_score=drought_score,
            raw_payload=payload,
        )

    def _map_simulation_event_to_alert(self, event: SimulationEvent) -> AlertDecision:
        mapping = {
            SimulationEventType.HEAVY_RAIN: AlertType.RAIN,
            SimulationEventType.DROUGHT: AlertType.DROUGHT,
            SimulationEventType.HEAT: AlertType.HEAT,
            SimulationEventType.STORM: AlertType.STORM,
        }
        return AlertDecision(mapping[event.event_type], event.severity)
