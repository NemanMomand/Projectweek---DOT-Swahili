from __future__ import annotations

import re

from app.models.enums import FeedbackType, PreferredLanguage
from app.schemas.feedback import ParsedFeedback

KEYWORDS = {
    FeedbackType.RAIN_SEEN: {"rain", "raining", "mvua", "manyunyu"},
    FeedbackType.DRY_SOIL: {"dry", "drought", "kavu", "ukame"},
    FeedbackType.FLOOD: {"flood", "flooding", "mafuriko"},
    FeedbackType.STORM: {"storm", "wind", "dhoruba", "upepo"},
    FeedbackType.PEST: {"pest", "locust", "wadudu", "nzige"},
}

SWAHILI_HINTS = {"mvua", "kavu", "ukame", "mafuriko", "dhoruba", "wadudu", "nzige", "joto"}
INTENSITY_WORDS = {
    "light": 2,
    "small": 2,
    "kidogo": 2,
    "moderate": 3,
    "medium": 3,
    "kati": 3,
    "heavy": 5,
    "severe": 5,
    "kubwa": 5,
    "kali": 5,
}


class FeedbackParser:
    def parse(self, body: str, language_hint: PreferredLanguage | None = None) -> ParsedFeedback:
        normalized = re.sub(r"\s+", " ", body.strip().lower())
        tokens = set(re.findall(r"[a-zA-Z]+", normalized))
        parsed_language = language_hint or self._detect_language(tokens)
        feedback_type = FeedbackType.UNKNOWN
        for candidate, keywords in KEYWORDS.items():
            if tokens.intersection(keywords):
                feedback_type = candidate
                break
        intensity = self._extract_intensity(normalized, tokens)
        return ParsedFeedback(
            feedback_type=feedback_type,
            intensity=intensity,
            parsed_language=parsed_language,
            normalized_text=normalized,
        )

    def _detect_language(self, tokens: set[str]) -> PreferredLanguage:
        if tokens.intersection(SWAHILI_HINTS):
            return PreferredLanguage.SW
        return PreferredLanguage.EN

    def _extract_intensity(self, normalized: str, tokens: set[str]) -> int | None:
        digit_match = re.search(r"\b([1-5])\b", normalized)
        if digit_match:
            return int(digit_match.group(1))
        for token in tokens:
            if token in INTENSITY_WORDS:
                return INTENSITY_WORDS[token]
        return None
