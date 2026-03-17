from fastapi import APIRouter

from app.db.session import check_database_health
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    await check_database_health()
    return HealthResponse(status="ready")
