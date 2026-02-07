from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .db import Base, engine
from .models import ApiKey, Job
from .observability import RequestIdMiddleware
from .errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .routes.admin import router as admin_router
from .routes.auth import router as auth_router
from .routes.health import router as health_router
from .routes.jobs import router as jobs_router
from .routes.metrics import router as metrics_router
from .routes.portal import router as portal_router
from .routes.billing import router as billing_router
from .routes.optimize import router as optimize_router
from .routes.matrix import router as matrix_router
from .routes.reoptimize import router as reoptimize_router
from .routes.webhooks import router as webhooks_router
from .routes.analytics import router as analytics_router
from .routes.exports import router as exports_router
from .routes.oauth import router as oauth_router
from .routes.reports import router as reports_router


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
    app.add_middleware(RequestIdMiddleware)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(optimize_router)
    app.include_router(matrix_router)
    app.include_router(reoptimize_router)
    app.include_router(webhooks_router)
    app.include_router(analytics_router)
    app.include_router(exports_router)
    app.include_router(oauth_router)
    app.include_router(reports_router)
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
