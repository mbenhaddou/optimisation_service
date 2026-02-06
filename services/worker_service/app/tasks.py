from datetime import datetime
from typing import Any, Dict, List

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from .config import settings  # noqa: F401
from .db import SessionLocal
from .models import Job
from optimise.routing.preprocessing import preprocess_request
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.solver.ortools_runner import solve_instances


@shared_task(name="worker.solve_job")
def solve_job(job_id: str) -> None:
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is None:
            return

        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

        errors: List[str] = []
        try:
            request_payload: Dict[str, Any] = job.request
            preprocessed = preprocess_request(request_payload, errors)
            instances = get_optimisation_instances(preprocessed)
            results = solve_instances(instances)
            job.result = {"solutions": results, "errors": errors}
            job.status = "COMPLETED"
        except SoftTimeLimitExceeded:
            job.status = "FAILED"
            job.error = "Job timed out"
        except Exception as exc:
            job.status = "FAILED"
            job.error = str(exc)
        finally:
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
