from fastapi import FastAPI

from .config import settings
from .db import Base, engine
from .models import ApiKey, Job
from .routes.admin import router as admin_router
from .routes.health import router as health_router
from .routes.jobs import router as jobs_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.service_name)

    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(admin_router)

    @app.on_event("startup")
    def _startup() -> None:
        if settings.auto_create_db:
            Base.metadata.create_all(bind=engine)

    return app


app = create_app()
