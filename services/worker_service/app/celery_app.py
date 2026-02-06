from celery import Celery

from .config import settings

celery_app = Celery(
    "optimisation-worker",
    broker=settings.resolved_celery_broker(),
    backend=settings.resolved_celery_backend(),
)

if settings.job_timeout_seconds > 0:
    celery_app.conf.update(
        task_time_limit=settings.job_timeout_seconds,
        task_soft_time_limit=settings.job_timeout_seconds,
    )

celery_app.autodiscover_tasks(["services.worker_service.app"])
