from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.services.alert_engine import AlertEngine
from app.services.daily_forecast_delivery_service import DailyForecastDeliveryService
from app.services.simulation_service import SimulationService

logger = get_logger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.alert_engine = AlertEngine()
        self.simulation_service = SimulationService(alert_engine=self.alert_engine)
        self.daily_forecast_delivery_service = DailyForecastDeliveryService()
        self._started = False

    def start(self) -> None:
        if self._started or not self.settings.scheduler_enabled:
            return
        self.scheduler.add_job(
            self.run_weather_cycle,
            IntervalTrigger(minutes=self.settings.scheduler_interval_minutes),
            id="weather-cycle",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_dispatch_cycle,
            IntervalTrigger(seconds=5),
            id="dispatch-cycle",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_simulation_cycle,
            IntervalTrigger(seconds=5),
            id="simulation-cycle",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_daily_forecast_cycle,
            IntervalTrigger(minutes=30),
            id="daily-forecast-cycle",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("scheduler_started")

    def stop(self) -> None:
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("scheduler_stopped")

    async def run_weather_cycle(self) -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as session:
            await self.alert_engine.evaluate_all(session)

    async def run_dispatch_cycle(self) -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as session:
            await self.alert_engine.dispatch_pending_alerts(session)

    async def run_simulation_cycle(self) -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as session:
            await self.simulation_service.process_due_events(session)

    async def run_daily_forecast_cycle(self) -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as session:
            await self.daily_forecast_delivery_service.send_tomorrow_forecast_if_due(session)
