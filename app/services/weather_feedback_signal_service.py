from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertType, DeliveryStatus, PreferredLanguage
from app.models.farmer import Farmer
from app.repositories.alert_repository import AlertRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.services.sms_service import SMSService
from app.services.translation_service import TranslationService
from app.services.weather_message_classifier import WeatherMessageClassifier


class WeatherFeedbackSignalService:
    def __init__(
        self,
        classifier: WeatherMessageClassifier | None = None,
        sms_service: SMSService | None = None,
        translation_service: TranslationService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.classifier = classifier or WeatherMessageClassifier()
        self.sms_service = sms_service or SMSService()
        self.translation_service = translation_service or TranslationService()

    async def evaluate_and_notify(
        self,
        session: AsyncSession,
        farmer: Farmer | None,
        message_text: str,
        language_hint: PreferredLanguage | None = None,
    ) -> dict:
        if farmer is None or not farmer.is_active:
            return {"triggered": False, "alerts_created": 0, "sms_sent": 0, "labels": []}

        current = self.classifier.classify(message_text)
        if not current.labels:
            return {"triggered": False, "alerts_created": 0, "sms_sent": 0, "labels": []}

        now = datetime.now(UTC)
        since = now - timedelta(hours=self.settings.feedback_signal_window_hours)
        feedback_rows = await FeedbackRepository(session).list_recent_for_farmer(farmer.id, since)

        counts: dict[AlertType, int] = {label: 0 for label in AlertType}
        for entry in feedback_rows:
            historical = self.classifier.classify(entry.free_text)
            for label in historical.labels:
                counts[label] += 1

        threshold = max(1, self.settings.feedback_signal_threshold)
        alerts_created = 0
        sms_sent = 0
        triggered_labels: list[str] = []
        language = language_hint or farmer.preferred_language
        alert_repo = AlertRepository(session)

        for label in current.labels:
            if counts.get(label, 0) < threshold:
                continue

            duplicate = await alert_repo.find_recent_duplicate(
                farmer_id=farmer.id,
                alert_type=label,
                since=now - timedelta(hours=self.settings.alert_cooldown_hours),
            )
            if duplicate is not None:
                continue

            severity = current.severity if label in current.labels else AlertSeverity.WARNING
            custom_message = self._build_signal_message(
                label,
                count=counts.get(label, 0),
                window_hours=self.settings.feedback_signal_window_hours,
                language=language,
            )
            title, message = self.translation_service.render_alert(
                alert_type=label,
                severity=severity,
                language=language,
                custom_message=custom_message,
            )
            alert = Alert(
                farmer_id=farmer.id,
                alert_type=label,
                severity=severity,
                title=title,
                message=message,
                language=language,
                scheduled_for=now,
                delivery_status=DeliveryStatus.PENDING,
                source_observation_id=None,
                simulation_event_id=None,
            )
            await alert_repo.create(alert)
            alerts_created += 1

            sms = await self.sms_service.send_message(session=session, phone_number=farmer.phone_number, body=message)
            alert.sent_at = datetime.now(UTC)
            if sms.status.value != "failed":
                alert.delivery_status = DeliveryStatus.SENT
                sms_sent += 1
            else:
                alert.delivery_status = DeliveryStatus.FAILED
            triggered_labels.append(label.value)

        return {
            "triggered": alerts_created > 0,
            "alerts_created": alerts_created,
            "sms_sent": sms_sent,
            "labels": triggered_labels,
        }

    def _build_signal_message(
        self,
        alert_type: AlertType,
        count: int,
        window_hours: int,
        language: PreferredLanguage,
    ) -> str:
        if language == PreferredLanguage.SW:
            label_text = {
                AlertType.RAIN: "mvua kubwa",
                AlertType.DROUGHT: "ukame",
                AlertType.STORM: "dhoruba",
                AlertType.HEAT: "joto kali",
            }[alert_type]
            return (
                f"Tumepokea taarifa {count} za {label_text} ndani ya saa {window_hours}. "
                "Chukua tahadhari mapema kulinda mazao yako."
            )

        label_text = {
            AlertType.RAIN: "heavy rain",
            AlertType.DROUGHT: "drought",
            AlertType.STORM: "storm conditions",
            AlertType.HEAT: "extreme heat",
        }[alert_type]
        return (
            f"We received {count} reports of {label_text} in the last {window_hours} hours. "
            "Please take preventive action to protect your crops."
        )
