from app.api.routes.alerts import router as alerts_router
from app.api.routes.farmers import router as farmers_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router
from app.api.routes.locations import router as locations_router
from app.api.routes.messages import router as messages_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.sms import router as sms_router
from app.api.routes.weather import router as weather_router

__all__ = [
    "alerts_router",
    "farmers_router",
    "feedback_router",
    "health_router",
    "intake_router",
    "locations_router",
    "messages_router",
    "simulation_router",
    "sms_router",
    "weather_router",
]
