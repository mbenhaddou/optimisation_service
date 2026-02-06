from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Job
from optimise.routing.preprocessing import preprocess_request
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.solver.ortools_runner import solve_instances


def _run_solver(request_payload: Dict[str, Any], errors: List[str]):
    preprocessed = preprocess_request(request_payload, errors)
    instances = get_optimisation_instances(preprocessed)
    return solve_instances(instances)


def solve_job_inline(db: Session, job_id: str) -> Job:
    job = db.query(Job).filter(Job.id == job_id).one_or_none()
    if job is None:
        raise ValueError("Job not found")

    job.status = "RUNNING"
    job.started_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    errors: List[str] = []
    try:
        request_payload: Dict[str, Any] = job.request
        if settings.job_timeout_seconds > 0:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_solver, request_payload, errors)
                results = future.result(timeout=settings.job_timeout_seconds)
        else:
            results = _run_solver(request_payload, errors)
        job.result = {"solutions": results, "errors": errors}
        job.status = "COMPLETED"
    except TimeoutError:
        job.status = "FAILED"
        job.error = "Job timed out"
    except Exception as exc:
        job.status = "FAILED"
        job.error = str(exc)
    finally:
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

    return job
