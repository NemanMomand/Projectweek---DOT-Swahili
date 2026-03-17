from enum import StrEnum


class PreferredLanguage(StrEnum):
    SW = "sw"
    EN = "en"


class AlertType(StrEnum):
    RAIN = "rain"
    DROUGHT = "drought"
    STORM = "storm"
    HEAT = "heat"


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    RECEIVED = "received"


class SMSDirection(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class SMSStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    RECEIVED = "received"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class FeedbackType(StrEnum):
    RAIN_SEEN = "rain_seen"
    DRY_SOIL = "dry_soil"
    FLOOD = "flood"
    STORM = "storm"
    PEST = "pest"
    UNKNOWN = "unknown"


class WeatherSource(StrEnum):
    VISUAL_CROSSING = "visual_crossing"
    FASTA = "fasta"
    MOCK = "mock"
    SIMULATION = "simulation"


class SimulationEventType(StrEnum):
    STORM = "storm"
    DROUGHT = "drought"
    HEAVY_RAIN = "heavy_rain"
    HEAT = "heat"


class SimulationStatus(StrEnum):
    PENDING = "pending"
    DETECTED = "detected"
    ALERT_CREATED = "alert_created"
    SMS_SENT = "sms_sent"
    COMPLETED = "completed"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    CANCELLED = "cancelled"
