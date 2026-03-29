from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.core.config import get_settings


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_name=settings.app_name, environment=settings.app_env)
