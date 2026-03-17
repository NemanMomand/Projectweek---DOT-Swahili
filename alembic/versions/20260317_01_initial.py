"""initial dot swahili schema

Revision ID: 20260317_01
Revises:
Create Date: 2026-03-17 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260317_01"
down_revision = None
branch_labels = None
depends_on = None


preferred_language = sa.Enum("sw", "en", name="preferredlanguage", native_enum=False)
alert_type = sa.Enum("rain", "drought", "storm", "heat", name="alerttype", native_enum=False)
alert_severity = sa.Enum("info", "warning", "critical", name="alertseverity", native_enum=False)
delivery_status = sa.Enum(
    "pending", "sent", "failed", "delivered", "received", name="deliverystatus", native_enum=False
)
sms_direction = sa.Enum("outbound", "inbound", name="smsdirection", native_enum=False)
sms_status = sa.Enum(
    "queued", "sent", "delivered", "received", "failed", "duplicate", name="smsstatus", native_enum=False
)
feedback_type = sa.Enum(
    "rain_seen", "dry_soil", "flood", "storm", "pest", "unknown", name="feedbacktype", native_enum=False
)
weather_source = sa.Enum(
    "visual_crossing", "fasta", "mock", "simulation", name="weathersource", native_enum=False
)
simulation_event_type = sa.Enum(
    "storm", "drought", "heavy_rain", "heat", name="simulationeventtype", native_enum=False
)
simulation_status = sa.Enum(
    "pending",
    "detected",
    "alert_created",
    "sms_sent",
    "completed",
    "skipped_duplicate",
    "cancelled",
    name="simulationstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "farmers",
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("preferred_language", preferred_language, nullable=False),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("village", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("crop_type", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farmers")),
        sa.UniqueConstraint("phone_number", name=op.f("uq_farmers_phone_number")),
    )
    op.create_index(op.f("ix_farmers_id"), "farmers", ["id"], unique=False)
    op.create_index(op.f("ix_farmers_phone_number"), "farmers", ["phone_number"], unique=False)
    op.create_index(op.f("ix_farmers_region"), "farmers", ["region"], unique=False)
    op.create_index(op.f("ix_farmers_district"), "farmers", ["district"], unique=False)
    op.create_index(op.f("ix_farmers_latitude"), "farmers", ["latitude"], unique=False)
    op.create_index(op.f("ix_farmers_longitude"), "farmers", ["longitude"], unique=False)
    op.create_index(op.f("ix_farmers_is_active"), "farmers", ["is_active"], unique=False)

    op.create_table(
        "locations",
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("village", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_locations")),
    )
    op.create_index(op.f("ix_locations_id"), "locations", ["id"], unique=False)
    op.create_index(op.f("ix_locations_region"), "locations", ["region"], unique=False)
    op.create_index(op.f("ix_locations_district"), "locations", ["district"], unique=False)
    op.create_index(op.f("ix_locations_latitude"), "locations", ["latitude"], unique=False)
    op.create_index(op.f("ix_locations_longitude"), "locations", ["longitude"], unique=False)

    op.create_table(
        "risk_rules",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_rules")),
        sa.UniqueConstraint("name", name=op.f("uq_risk_rules_name")),
    )
    op.create_index(op.f("ix_risk_rules_id"), "risk_rules", ["id"], unique=False)

    op.create_table(
        "simulation_events",
        sa.Column("event_type", simulation_event_type, nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("target_region", sa.String(length=120), nullable=True),
        sa.Column("target_farmer_id", sa.Integer(), nullable=True),
        sa.Column("language", preferred_language, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger_after_minutes", sa.Integer(), nullable=False),
        sa.Column("sms_delay_seconds", sa.Integer(), nullable=False),
        sa.Column("custom_message", sa.Text(), nullable=True),
        sa.Column("status", simulation_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["target_farmer_id"], ["farmers.id"], name=op.f("fk_simulation_events_target_farmer_id_farmers"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_events")),
    )
    op.create_index(op.f("ix_simulation_events_id"), "simulation_events", ["id"], unique=False)
    op.create_index(op.f("ix_simulation_events_event_type"), "simulation_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_simulation_events_target_region"), "simulation_events", ["target_region"], unique=False)
    op.create_index(op.f("ix_simulation_events_target_farmer_id"), "simulation_events", ["target_farmer_id"], unique=False)
    op.create_index(op.f("ix_simulation_events_starts_at"), "simulation_events", ["starts_at"], unique=False)
    op.create_index(op.f("ix_simulation_events_status"), "simulation_events", ["status"], unique=False)

    op.create_table(
        "sms_messages",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("direction", sms_direction, nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sms_status, nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sms_messages")),
        sa.UniqueConstraint("provider_message_id", name=op.f("uq_sms_messages_provider_message_id")),
    )
    op.create_index(op.f("ix_sms_messages_id"), "sms_messages", ["id"], unique=False)
    op.create_index(op.f("ix_sms_messages_provider_message_id"), "sms_messages", ["provider_message_id"], unique=False)
    op.create_index(op.f("ix_sms_messages_phone_number"), "sms_messages", ["phone_number"], unique=False)

    op.create_table(
        "weather_observations",
        sa.Column("source", weather_source, nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rainfall_mm", sa.Float(), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False),
        sa.Column("humidity_pct", sa.Float(), nullable=False),
        sa.Column("wind_speed_kph", sa.Float(), nullable=False),
        sa.Column("soil_moisture_index", sa.Float(), nullable=True),
        sa.Column("drought_risk_score", sa.Float(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weather_observations")),
    )
    op.create_index(op.f("ix_weather_observations_id"), "weather_observations", ["id"], unique=False)
    op.create_index(op.f("ix_weather_observations_latitude"), "weather_observations", ["latitude"], unique=False)
    op.create_index(op.f("ix_weather_observations_longitude"), "weather_observations", ["longitude"], unique=False)
    op.create_index(op.f("ix_weather_observations_observed_at"), "weather_observations", ["observed_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("language", preferred_language, nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", delivery_status, nullable=False),
        sa.Column("source_observation_id", sa.Integer(), nullable=True),
        sa.Column("simulation_event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], name=op.f("fk_alerts_farmer_id_farmers"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_observation_id"], ["weather_observations.id"], name=op.f("fk_alerts_source_observation_id_weather_observations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["simulation_event_id"], ["simulation_events.id"], name=op.f("fk_alerts_simulation_event_id_simulation_events"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_farmer_id"), "alerts", ["farmer_id"], unique=False)
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_alerts_scheduled_for"), "alerts", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_alerts_source_observation_id"), "alerts", ["source_observation_id"], unique=False)
    op.create_index(op.f("ix_alerts_simulation_event_id"), "alerts", ["simulation_event_id"], unique=False)

    op.create_table(
        "farmer_feedback",
        sa.Column("farmer_id", sa.Integer(), nullable=True),
        sa.Column("sms_message_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", feedback_type, nullable=False),
        sa.Column("intensity", sa.Integer(), nullable=True),
        sa.Column("free_text", sa.Text(), nullable=False),
        sa.Column("parsed_language", preferred_language, nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], name=op.f("fk_farmer_feedback_farmer_id_farmers"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sms_message_id"], ["sms_messages.id"], name=op.f("fk_farmer_feedback_sms_message_id_sms_messages"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farmer_feedback")),
    )
    op.create_index(op.f("ix_farmer_feedback_id"), "farmer_feedback", ["id"], unique=False)
    op.create_index(op.f("ix_farmer_feedback_sms_message_id"), "farmer_feedback", ["sms_message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_farmer_feedback_sms_message_id"), table_name="farmer_feedback")
    op.drop_index(op.f("ix_farmer_feedback_id"), table_name="farmer_feedback")
    op.drop_table("farmer_feedback")

    op.drop_index(op.f("ix_alerts_simulation_event_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_source_observation_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_scheduled_for"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_severity"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_alert_type"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_farmer_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_weather_observations_observed_at"), table_name="weather_observations")
    op.drop_index(op.f("ix_weather_observations_longitude"), table_name="weather_observations")
    op.drop_index(op.f("ix_weather_observations_latitude"), table_name="weather_observations")
    op.drop_index(op.f("ix_weather_observations_id"), table_name="weather_observations")
    op.drop_table("weather_observations")

    op.drop_index(op.f("ix_sms_messages_phone_number"), table_name="sms_messages")
    op.drop_index(op.f("ix_sms_messages_provider_message_id"), table_name="sms_messages")
    op.drop_index(op.f("ix_sms_messages_id"), table_name="sms_messages")
    op.drop_table("sms_messages")

    op.drop_index(op.f("ix_simulation_events_status"), table_name="simulation_events")
    op.drop_index(op.f("ix_simulation_events_starts_at"), table_name="simulation_events")
    op.drop_index(op.f("ix_simulation_events_target_farmer_id"), table_name="simulation_events")
    op.drop_index(op.f("ix_simulation_events_target_region"), table_name="simulation_events")
    op.drop_index(op.f("ix_simulation_events_event_type"), table_name="simulation_events")
    op.drop_index(op.f("ix_simulation_events_id"), table_name="simulation_events")
    op.drop_table("simulation_events")

    op.drop_index(op.f("ix_risk_rules_id"), table_name="risk_rules")
    op.drop_table("risk_rules")

    op.drop_index(op.f("ix_locations_longitude"), table_name="locations")
    op.drop_index(op.f("ix_locations_latitude"), table_name="locations")
    op.drop_index(op.f("ix_locations_district"), table_name="locations")
    op.drop_index(op.f("ix_locations_region"), table_name="locations")
    op.drop_index(op.f("ix_locations_id"), table_name="locations")
    op.drop_table("locations")

    op.drop_index(op.f("ix_farmers_is_active"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_longitude"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_latitude"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_district"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_region"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_phone_number"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_id"), table_name="farmers")
    op.drop_table("farmers")
