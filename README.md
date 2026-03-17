# Dot Swahili API

Production-ready MVP backend for an East Africa farmer early-warning platform. The system collects weather forecasts, evaluates farmer-specific risk, sends short bilingual SMS alerts, ingests SMS feedback, stores hyper-local field observations, and provides a simulation dashboard for demo and testing.

## Stack

- Python 3.12
- FastAPI + OpenAPI docs
- PostgreSQL
- SQLAlchemy 2.0 async
- Alembic migrations
- Pydantic v2
- APScheduler
- httpx
- Docker + docker-compose
- pytest

## Features

- Farmer CRUD API with E.164 validation and coordinate normalization
- Weather provider abstraction with Visual Crossing implementation and FASTA adapter stub
- Alert engine with rainfall, drought, heat, and storm evaluation
- Duplicate alert suppression using a configurable cooldown window
- SMS provider abstraction with mock provider and Twilio-ready structure
- Idempotent inbound SMS webhook handling
- Structured feedback parsing for English and Swahili replies
- Simulation event pipeline with delayed trigger and SMS countdown testing
- HTML demo dashboard at `/dashboard/`
- Structured JSON logging, health checks, readiness checks, and rate limiting

## File Tree

```text
.
├── .env.example
├── Dockerfile
├── README.md
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 20260317_01_initial.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── alerts.py
│   │       ├── farmers.py
│   │       ├── feedback.py
│   │       ├── health.py
│   │       ├── locations.py
│   │       ├── simulation.py
│   │       ├── sms.py
│   │       └── weather.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── alert.py
│   │   ├── enums.py
│   │   ├── farmer.py
│   │   ├── farmer_feedback.py
│   │   ├── location.py
│   │   ├── risk_rule.py
│   │   ├── simulation_event.py
│   │   ├── sms_message.py
│   │   └── weather_observation.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── alert_repository.py
│   │   ├── farmer_repository.py
│   │   ├── feedback_repository.py
│   │   ├── location_repository.py
│   │   ├── risk_rule_repository.py
│   │   ├── simulation_repository.py
│   │   ├── sms_repository.py
│   │   └── weather_repository.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── alert.py
│   │   ├── farmer.py
│   │   ├── feedback.py
│   │   ├── health.py
│   │   ├── location.py
│   │   ├── simulation.py
│   │   ├── sms.py
│   │   └── weather.py
│   ├── scripts/
│   │   └── seed.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_engine.py
│   │   ├── feedback_parser.py
│   │   ├── scheduler_service.py
│   │   ├── simulation_service.py
│   │   ├── sms_service.py
│   │   ├── translation_service.py
│   │   └── weather_provider.py
│   └── workers/
│       ├── __init__.py
│       └── scheduler_jobs.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── tests/
		├── conftest.py
		├── test_alert_engine.py
		├── test_feedback_parser.py
		├── test_integration_flow.py
		├── test_simulation_service.py
		└── test_weather_provider.py
```

## Quick Start

### Docker first startup

```bash
docker compose up --build
```

The container entrypoint automatically:

1. runs Alembic migrations
2. seeds sample East Africa farmer data
3. starts the FastAPI app on port `8000`

Open:

- API docs: `http://localhost:8000/docs`
- Demo dashboard: `http://localhost:8000/dashboard/`
- Health: `http://localhost:8000/api/v1/health`

### Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload
```

### Visual Crossing key setup

If you use live weather data, set one of these environment variables:

- `VISUAL_CROSSING_API_KEY` (recommended)
- `WEATHER_API_KEY` (accepted alias)

For strict live mode (no mock fallback), also set:

- `WEATHER_PROVIDER=visual_crossing`
- `WEATHER_MOCK_FALLBACK=false`

PowerShell example:

```powershell
$env:VISUAL_CROSSING_API_KEY='YOUR_REAL_KEY'
$env:WEATHER_PROVIDER='visual_crossing'
$env:WEATHER_MOCK_FALLBACK='false'
```

### Run tests

```bash
pytest
```

## Example curl Commands

Create a farmer:

```bash
curl -X POST http://localhost:8000/api/v1/farmers \
	-H "Content-Type: application/json" \
	-d "{\"full_name\":\"Asha Mollel\",\"phone_number\":\"+255700999111\",\"preferred_language\":\"sw\",\"region\":\"Arusha\",\"district\":\"Meru\",\"village\":\"Usa River\",\"latitude\":-3.369,\"longitude\":36.8569,\"crop_type\":\"Maize\",\"is_active\":true}"
```

Evaluate alerts for all active farmers:

```bash
curl -X POST http://localhost:8000/api/v1/alerts/evaluate \
	-H "Content-Type: application/json" \
	-d "{\"force_send\":true}"
```

Create a simulation event:

```bash
curl -X POST http://localhost:8000/api/v1/simulation/events \
	-H "Content-Type: application/json" \
	-d "{\"event_type\":\"storm\",\"severity\":\"critical\",\"starts_in_minutes\":10,\"sms_delay_seconds\":5,\"target_region\":\"Arusha\",\"language\":\"sw\"}"
```

Trigger a simulation event immediately:

```bash
curl -X POST http://localhost:8000/api/v1/simulation/events/1/trigger
```

Submit inbound SMS feedback:

```bash
curl -X POST http://localhost:8000/api/v1/sms/webhooks/inbound \
	-H "Content-Type: application/json" \
	-H "x-webhook-token: local-webhook-token" \
	-d "{\"provider_message_id\":\"demo-123\",\"phone_number\":\"+255700999111\",\"body\":\"MVUA kubwa 4\",\"raw_payload\":{\"source\":\"curl\"}}"
```

## Android Studio Flow (Inbox + Reply + HTTPS overview)

You can use a simple Android app as your farmer client:

- Pull outgoing messages from API: `GET /api/v1/messages/sms?phone_number=...`
- Send reply from app to API: `POST /api/v1/sms/reply`
- View returned replies on HTTPS page: `GET /messages` (frontend calls `/api/v1/messages/replies`)

For demo, secure mobile reply calls with the same token header:

- Header: `x-webhook-token: local-webhook-token`

### Retrofit interface example

```kotlin
interface DotSwahiliApi {
	@GET("api/v1/messages/sms")
	suspend fun getInbox(@Query("phone_number") phoneNumber: String): List<SmsMessage>

	@POST("api/v1/sms/reply")
	suspend fun sendReply(
		@Header("x-webhook-token") token: String,
		@Body request: MobileReplyRequest
	): ReplyResponse
}

data class SmsMessage(
	val id: Int,
	val phone_number: String,
	val body: String,
	val status: String,
	val sent_at: String?
)

data class MobileReplyRequest(
	val phone_number: String,
	val body: String,
	val provider_message_id: String? = null,
	val raw_payload: Map<String, String> = mapOf("source" to "android")
)

data class ReplyResponse(
	val status: String,
	val duplicate: Boolean,
	val message_id: Int
)
```

### HTTPS page to inspect replies

Open:

- `http://<your-host>/messages`

Filter by phone number and you will see:

- Alerts
- Outbound SMS
- Inbound replies sent from Android

## Architecture Decisions

- Monolith first: one FastAPI service with clear boundaries across routes, services, repositories, and models.
- Provider abstractions: weather and SMS integrations are swappable and mockable for local development and tests.
- Reliability over novelty: alerts are deterministic, template-driven, short, and language-specific without requiring an LLM.
- Operational clarity: migrations, seed data, health checks, structured logging, and a demo dashboard are part of the repo, not afterthoughts.
- Simulation is real: the dashboard creates actual database records, actual alerts, and actual mock SMS log entries through the same backend pipeline used for provider-driven alerts.

## Default Secrets and Local Behavior

- `.env.example` is wired into Docker Compose so the app boots immediately.
- If Visual Crossing credentials are missing, the backend falls back to a mock weather payload.
- The default SMS provider is mock mode, so outbound SMS is stored and visible without external credentials.
- Inbound webhook authorization uses the default token `local-webhook-token` for local testing.