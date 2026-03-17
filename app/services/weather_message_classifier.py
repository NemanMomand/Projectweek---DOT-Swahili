from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models.enums import AlertSeverity, AlertType

KEYWORDS: dict[AlertType, set[str]] = {
    AlertType.RAIN: {
        "rain",
        "raining",
        "mvua",
        "manyunyu",
        "flood",
        "flooding",
        "mafuriko",
        "wet",
        "maji",
    },
    AlertType.DROUGHT: {
        "dry",
        "drought",
        "ukame",
        "kavu",
        "thirsty",
        "hakunamvua",
        "no",
    },
    AlertType.STORM: {
        "storm",
        "dhoruba",
        "wind",
        "upepo",
        "thunder",
        "lightning",
        "kimbunga",
    },
    AlertType.HEAT: {
        "heat",
        "hot",
        "joto",
        "sun",
        "sunny",
        "kiangazi",
        "temperatures",
    },
}

INTENSITY_KEYWORDS = {
    "kali",
    "kubwa",
    "heavy",
    "severe",
    "extreme",
    "sana",
    "critical",
}


@dataclass
class ClassificationResult:
    labels: list[AlertType]
    scores: dict[AlertType, float]
    severity: AlertSeverity


class WeatherMessageClassifier:
    def classify(self, text: str) -> ClassificationResult:
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        tokens = re.findall(r"[a-zA-Z]+", normalized)
        scores: dict[AlertType, float] = {label: 0.0 for label in KEYWORDS}

        for token in tokens:
            for alert_type, keywords in KEYWORDS.items():
                if token in keywords:
                    scores[alert_type] += 1.0
                    continue
                matched = self._fuzzy_match(token, keywords)
                if matched:
                    scores[alert_type] += 0.65

        labels = [label for label, score in scores.items() if score >= 1.0]
        if not labels:
            labels = [label for label, score in scores.items() if score >= 0.65]

        severity = AlertSeverity.WARNING
        if any(token in INTENSITY_KEYWORDS for token in tokens):
            severity = AlertSeverity.CRITICAL

        if labels and max(scores.values()) >= 2.0:
            severity = AlertSeverity.CRITICAL

        return ClassificationResult(
            labels=labels,
            scores={k: round(v, 2) for k, v in scores.items() if v > 0},
            severity=severity,
        )

    def _fuzzy_match(self, token: str, keywords: set[str]) -> bool:
        if len(token) < 4:
            return False
        for keyword in keywords:
            if abs(len(token) - len(keyword)) > 2:
                continue
            if SequenceMatcher(None, token, keyword).ratio() >= 0.84:
                return True
        return False
