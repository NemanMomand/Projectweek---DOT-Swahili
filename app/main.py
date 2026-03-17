from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import RateLimitMiddleware
from app.db.session import dispose_engine
from app.services.scheduler_service import SchedulerService

setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = SchedulerService()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.stop()
        await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    description="API-first farmer early warning and SMS feedback backend for Dot Swahili",
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    # Threat 4: Never use allow_origins=["*"] with allow_credentials=True.
    # For a prototype served from the same host, restrict to localhost origins.
    # In production set CORS_ALLOW_ORIGINS env var to your actual domain.
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key", "X-Webhook-Token"],
)
app.include_router(api_router)

frontend_path = Path(__file__).resolve().parents[1] / "frontend"
if frontend_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(frontend_path), html=True), name="dashboard")


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/messages-live")


@app.get("/intake", include_in_schema=False)
async def intake_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/messages-live.html")


@app.get("/messages", include_in_schema=False)
async def messages_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/messages-live.html")


@app.get("/messages-live", include_in_schema=False)
async def messages_live_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/messages-live.html")


@app.get("/mvua-live", include_in_schema=False)
async def rain_live_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/rain-live.html")


@app.get("/forecast-delivery", include_in_schema=False)
async def forecast_delivery_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/forecast-delivery.html")


@app.get("/feedback-groups", include_in_schema=False)
async def feedback_groups_page_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/feedback-groups.html")
