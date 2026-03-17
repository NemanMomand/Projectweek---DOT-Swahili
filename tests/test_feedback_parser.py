from app.models.enums import FeedbackType, PreferredLanguage
from app.services.feedback_parser import FeedbackParser


def test_feedback_parser_detects_swahili_dry_signal():
    result = FeedbackParser().parse("Udongo ni kavu sana 5")
    assert result.feedback_type == FeedbackType.DRY_SOIL
    assert result.parsed_language == PreferredLanguage.SW
    assert result.intensity == 5
