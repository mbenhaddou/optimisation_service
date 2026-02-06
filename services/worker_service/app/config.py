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
    service_name: str = os.getenv("SERVICE_NAME", "optimisation-worker")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/api_service.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "")
    job_timeout_seconds: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "300"))
    enable_usage_update: bool = _get_bool("ENABLE_USAGE_UPDATE", True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")

    def resolved_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    def resolved_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()
