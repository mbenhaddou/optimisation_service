from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .models import ApiKey, Job
from .routes.admin import router as admin_router
from .routes.auth import router as auth_router
from .routes.health import router as health_router
from .routes.jobs import router as jobs_router
from .routes.portal import router as portal_router
from .routes.billing import router as billing_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.service_name,
        description="Mentis Optimisation API for routing and scheduling jobs.",
        version="0.1.0",
    )

    origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=[m.strip() for m in settings.cors_allow_methods.split(",") if m.strip()],
            allow_headers=[h.strip() for h in settings.cors_allow_headers.split(",") if h.strip()],
        )

    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(portal_router)
    app.include_router(billing_router)

    @app.on_event("startup")
    def _startup() -> None:
        if settings.auto_create_db:
            Base.metadata.create_all(bind=engine)

    return app


app = create_app()
