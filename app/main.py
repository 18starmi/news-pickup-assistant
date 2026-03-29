from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.sources import router as sources_router
from app.api.routes.trending import router as trending_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.bootstrap_service import bootstrap_application


settings = get_settings()
configure_logging(settings.app_env)


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_application()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/items/view", status_code=302)


app.include_router(health_router)
app.include_router(items_router)
app.include_router(jobs_router)
app.include_router(sources_router)
app.include_router(trending_router)
