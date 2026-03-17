from app.models.enums import WeatherSource
from app.services.weather_provider import VisualCrossingWeatherProvider


def test_visual_crossing_normalization():
    payload = {
        "queryCost": 1,
        "currentConditions": {
            "datetimeEpoch": 1710662400,
            "precip": 3.5,
            "temp": 31.2,
            "humidity": 74,
            "windspeed": 18,
        },
        "days": [
            {
                "hours": [
                    {
                        "datetimeEpoch": 1710662400,
                        "precip": 4.0,
                        "temp": 31.0,
                        "humidity": 75,
                        "windspeed": 17,
                    },
                    {
                        "datetimeEpoch": 1710666000,
                        "precip": 8.0,
                        "temp": 32.0,
                        "humidity": 73,
                        "windspeed": 22,
                    },
                ]
            }
        ],
    }

    current = VisualCrossingWeatherProvider.normalize_current_payload(payload, -3.3, 36.8)
    forecast = VisualCrossingWeatherProvider.normalize_forecast_payload(payload, -3.3, 36.8)

    assert current.source == WeatherSource.VISUAL_CROSSING
    assert current.rainfall_mm == 3.5
    assert forecast.source == WeatherSource.VISUAL_CROSSING
    assert len(forecast.timeline) == 2
    assert forecast.timeline[1].wind_speed_kph == 22
