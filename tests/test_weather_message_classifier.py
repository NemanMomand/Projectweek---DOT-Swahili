from app.models.enums import AlertSeverity, AlertType
from app.services.weather_message_classifier import WeatherMessageClassifier


def test_classifier_detects_typos_and_swahili_intensity():
    result = WeatherMessageClassifier().classify("Mvuaa kubwa sana leo")
    assert AlertType.RAIN in result.labels
    assert result.severity == AlertSeverity.CRITICAL


def test_classifier_detects_heat_signal():
    result = WeatherMessageClassifier().classify("Very hot sun and heat on the farm")
    assert AlertType.HEAT in result.labels
