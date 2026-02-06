from .config import settings

try:
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover - optional in local tests
    Celery = None

celery_app = None
if Celery is not None:
    celery_app = Celery(
        "optimisation-api",
        broker=settings.resolved_celery_broker(),
        backend=settings.resolved_celery_backend(),
    )


def enqueue_job(job_id: str) -> None:
    if celery_app is None:
        raise RuntimeError("Celery is not available")
    celery_app.send_task("worker.solve_job", args=[job_id])
