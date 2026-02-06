from dataclasses import dataclass
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
    service_name: str = os.getenv("SERVICE_NAME", "optimisation-api")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/api_service.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "")
    api_key_header: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    admin_key_header: str = os.getenv("ADMIN_KEY_HEADER", "X-Admin-Key")
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    allow_anonymous: bool = _get_bool("ALLOW_ANON", True)
    auto_create_db: bool = _get_bool("AUTO_CREATE_DB", True)
    sync_execution: bool = _get_bool("SYNC_EXECUTION", False)
    enable_rate_limiting: bool = _get_bool("ENABLE_RATE_LIMITING", True)
    rate_limit_per_minute: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_window_seconds: int = int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60"))
    max_job_nodes: int = int(os.getenv("MAX_JOB_NODES", "0"))
    max_job_units: int = int(os.getenv("MAX_JOB_UNITS", "0"))
    job_timeout_seconds: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "300"))
    enforce_usage_limits: bool = _get_bool("ENFORCE_USAGE_LIMITS", False)
    free_tier_units: int = int(os.getenv("FREE_TIER_UNITS", "200000"))
    mapping_service_url: str = os.getenv("MAPPING_SERVICE_URL", "")

    def resolved_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    def resolved_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()
