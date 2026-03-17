from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="Dot Swahili API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    # Threat 4: default False so stack traces are not exposed to API callers.
    # Set DEBUG=true only in local development.
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/dotswahili",
        alias="DATABASE_URL",
    )
    alembic_database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/dotswahili",
        alias="ALEMBIC_DATABASE_URL",
    )

    weather_provider: str = Field(default="visual_crossing", alias="WEATHER_PROVIDER")
    visual_crossing_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "VISUAL_CROSSING_API_KEY",
            "VISUALCROSSING_API_KEY",
            "WEATHER_API_KEY",
        ),
    )
    visual_crossing_base_url: str = Field(
        default="https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline",
        alias="VISUAL_CROSSING_BASE_URL",
    )
    weather_timeout_seconds: int = Field(default=15, alias="WEATHER_TIMEOUT_SECONDS")
    weather_retry_attempts: int = Field(default=3, alias="WEATHER_RETRY_ATTEMPTS")
    weather_retry_backoff_seconds: float = Field(default=1.0, alias="WEATHER_RETRY_BACKOFF_SECONDS")
    weather_mock_fallback: bool = Field(default=True, alias="WEATHER_MOCK_FALLBACK")

    sms_provider: str = Field(default="mock", alias="SMS_PROVIDER")
    sms_from_number: str = Field(default="DOTSWAHILI", alias="SMS_FROM_NUMBER")
    twilio_account_sid: str | None = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_messaging_service_sid: str | None = Field(
        default=None,
        alias="TWILIO_MESSAGING_SERVICE_SID",
    )
    sms_webhook_token: str = Field(default="local-webhook-token", alias="SMS_WEBHOOK_TOKEN")

    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_interval_minutes: int = Field(default=30, alias="SCHEDULER_INTERVAL_MINUTES")
    alert_lead_minutes: int = Field(default=20, alias="ALERT_LEAD_MINUTES")
    alert_cooldown_hours: int = Field(default=12, alias="ALERT_COOLDOWN_HOURS")
    rain_24h_threshold_mm: float = Field(default=35.0, alias="RAIN_24H_THRESHOLD_MM")
    drought_72h_threshold_mm: float = Field(default=5.0, alias="DROUGHT_72H_THRESHOLD_MM")
    heat_threshold_c: float = Field(default=34.0, alias="HEAT_THRESHOLD_C")
    storm_wind_threshold_kph: float = Field(default=45.0, alias="STORM_WIND_THRESHOLD_KPH")
    feedback_signal_window_hours: int = Field(default=6, alias="FEEDBACK_SIGNAL_WINDOW_HOURS")
    feedback_signal_threshold: int = Field(default=2, alias="FEEDBACK_SIGNAL_THRESHOLD")

    rate_limit_max_requests: int = Field(default=120, alias="RATE_LIMIT_MAX_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    seed_sample_data: bool = Field(default=True, alias="SEED_SAMPLE_DATA")

    # Threat 3: admin key for sensitive endpoints (simulation, delete, manual alerts)
    # Set ADMIN_API_KEY env var to a strong random string in production.
    admin_api_key: str = Field(default="change-me", alias="ADMIN_API_KEY")

    @field_validator("visual_crossing_api_key", mode="before")
    @classmethod
    def normalize_visual_crossing_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().strip('"').strip("'")
        if not cleaned:
            return None
        if cleaned.upper() in {"YOUR_API_KEY", "CHANGE_ME", "CHANGEME"}:
            return None
        return cleaned


@lru_cache
def get_settings() -> Settings:
    return Settings()
