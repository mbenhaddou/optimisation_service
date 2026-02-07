from dataclasses import dataclass, fields
import os
from dotenv import load_dotenv

load_dotenv()
if os.getenv("MAPPING_SERVICE_URL") and not os.getenv("ROUTING_ENGINE"):
    os.environ["ROUTING_ENGINE"] = os.getenv("MAPPING_SERVICE_URL")


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    service_name: str = "optimisation-api"
    database_url: str = "sqlite:///./data/api_service.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    api_key_header: str = "X-API-Key"
    admin_key_header: str = "X-Admin-Key"
    admin_api_key: str = ""
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_allow_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = False
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,X-API-Key,X-Admin-Key"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""
    frontend_base_url: str = "http://localhost:3000"
    log_level: str = "INFO"
    log_format: str = "json"
    allow_anonymous: bool = True
    auto_create_db: bool = True
    sync_execution: bool = False
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_window_seconds: int = 60
    max_job_nodes: int = 0
    max_job_units: int = 0
    job_timeout_seconds: int = 300
    enforce_usage_limits: bool = False
    free_tier_units: int = 200000
    mapping_service_url: str = ""

    def resolved_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    def resolved_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


def _read_settings() -> Settings:
    return Settings(
        service_name=os.getenv("SERVICE_NAME", Settings.service_name),
        database_url=os.getenv("DATABASE_URL", Settings.database_url),
        redis_url=os.getenv("REDIS_URL", Settings.redis_url),
        celery_broker_url=os.getenv("CELERY_BROKER_URL", Settings.celery_broker_url),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", Settings.celery_result_backend),
        api_key_header=os.getenv("API_KEY_HEADER", Settings.api_key_header),
        admin_key_header=os.getenv("ADMIN_KEY_HEADER", Settings.admin_key_header),
        admin_api_key=os.getenv("ADMIN_API_KEY", Settings.admin_api_key),
        jwt_secret=os.getenv("JWT_SECRET", Settings.jwt_secret),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", Settings.jwt_algorithm),
        access_token_expire_minutes=int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(Settings.access_token_expire_minutes))
        ),
        cors_allow_origins=os.getenv("CORS_ALLOW_ORIGINS", Settings.cors_allow_origins),
        cors_allow_credentials=_get_bool("CORS_ALLOW_CREDENTIALS", Settings.cors_allow_credentials),
        cors_allow_methods=os.getenv("CORS_ALLOW_METHODS", Settings.cors_allow_methods),
        cors_allow_headers=os.getenv("CORS_ALLOW_HEADERS", Settings.cors_allow_headers),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", Settings.stripe_secret_key),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", Settings.stripe_webhook_secret),
        stripe_price_id=os.getenv("STRIPE_PRICE_ID", Settings.stripe_price_id),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", Settings.frontend_base_url),
        log_level=os.getenv("LOG_LEVEL", Settings.log_level),
        log_format=os.getenv("LOG_FORMAT", Settings.log_format),
        allow_anonymous=_get_bool("ALLOW_ANON", Settings.allow_anonymous),
        auto_create_db=_get_bool("AUTO_CREATE_DB", Settings.auto_create_db),
        sync_execution=_get_bool("SYNC_EXECUTION", Settings.sync_execution),
        enable_rate_limiting=_get_bool("ENABLE_RATE_LIMITING", Settings.enable_rate_limiting),
        rate_limit_per_minute=int(
            os.getenv("API_RATE_LIMIT_PER_MINUTE", str(Settings.rate_limit_per_minute))
        ),
        rate_limit_window_seconds=int(
            os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", str(Settings.rate_limit_window_seconds))
        ),
        max_job_nodes=int(os.getenv("MAX_JOB_NODES", str(Settings.max_job_nodes))),
        max_job_units=int(os.getenv("MAX_JOB_UNITS", str(Settings.max_job_units))),
        job_timeout_seconds=int(
            os.getenv("JOB_TIMEOUT_SECONDS", str(Settings.job_timeout_seconds))
        ),
        enforce_usage_limits=_get_bool("ENFORCE_USAGE_LIMITS", Settings.enforce_usage_limits),
        free_tier_units=int(os.getenv("FREE_TIER_UNITS", str(Settings.free_tier_units))),
        mapping_service_url=os.getenv("MAPPING_SERVICE_URL", Settings.mapping_service_url),
    )


settings = _read_settings()


def reload_settings() -> Settings:
    """Reload environment-driven settings in place to preserve object identity."""
    refreshed = _read_settings()
    for field in fields(Settings):
        object.__setattr__(settings, field.name, getattr(refreshed, field.name))
    return settings
