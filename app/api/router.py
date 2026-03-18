from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.forecast_delivery import router as forecast_delivery_router
from app.api.routes.farmers import router as farmers_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router
from app.api.routes.locations import router as locations_router
from app.api.routes.messages import router as messages_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.sms import router as sms_router
from app.api.routes.voice import router as voice_router
from app.api.routes.weather import router as weather_router

api_router = APIRouter()
api_router.include_router(farmers_router)
api_router.include_router(locations_router)
api_router.include_router(intake_router)
api_router.include_router(messages_router)
api_router.include_router(weather_router)
api_router.include_router(forecast_delivery_router)
api_router.include_router(alerts_router)
api_router.include_router(sms_router)
api_router.include_router(voice_router)
api_router.include_router(feedback_router)
api_router.include_router(simulation_router)
api_router.include_router(health_router)
