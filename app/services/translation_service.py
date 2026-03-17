from __future__ import annotations

from app.models.enums import AlertSeverity, AlertType, PreferredLanguage

TEMPLATES: dict[PreferredLanguage, dict[AlertType, dict[str, str]]] = {
    PreferredLanguage.EN: {
        AlertType.RAIN: {
            "title": "Heavy rain warning",
            "message": "Warning: Heavy rain expected in your area within 24 hours. Consider delaying harvest.",
        },
        AlertType.DROUGHT: {
            "title": "Drought warning",
            "message": "Warning: Dry conditions may continue. Save water and protect young crops.",
        },
        AlertType.HEAT: {
            "title": "Heat warning",
            "message": "Warning: High heat expected today. Water crops early and limit field work at noon.",
        },
        AlertType.STORM: {
            "title": "Storm warning",
            "message": "Warning: Strong storm risk soon. Secure tools and avoid open fields.",
        },
    },
    PreferredLanguage.SW: {
        AlertType.RAIN: {
            "title": "Tahadhari ya mvua kubwa",
            "message": "Tahadhari: Mvua kubwa inatarajiwa ndani ya saa 24. Fikiria kuchelewesha mavuno.",
        },
        AlertType.DROUGHT: {
            "title": "Tahadhari ya ukame",
            "message": "Tahadhari: Ukavu unaweza kuendelea. Hifadhi maji na linda mazao machanga.",
        },
        AlertType.HEAT: {
            "title": "Tahadhari ya joto kali",
            "message": "Tahadhari: Joto kali linatarajiwa leo. Mwagilia mapema na punguza kazi shambani mchana.",
        },
        AlertType.STORM: {
            "title": "Tahadhari ya dhoruba",
            "message": "Tahadhari: Hatari ya dhoruba kali ipo karibuni. Funga vifaa na epuka mashamba ya wazi.",
        },
    },
}


class TranslationService:
    def render_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        language: PreferredLanguage,
        custom_message: str | None = None,
    ) -> tuple[str, str]:
        template = TEMPLATES[language][alert_type]
        title = template["title"]
        message = custom_message or template["message"]
        if severity == AlertSeverity.CRITICAL and language == PreferredLanguage.EN:
            title = f"Critical {title.lower()}"
        elif severity == AlertSeverity.CRITICAL and language == PreferredLanguage.SW:
            title = f"Tahadhari kali: {title.lower()}"
        return title, message
