from datetime import datetime
import time
from typing import Any, Dict, List

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from .config import settings  # noqa: F401
from .db import SessionLocal
from .models import Job, WebhookEndpoint
from .observability import configure_logger
from optimise.routing.preprocessing.preprocess_request import preprocess_request
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.solver.ortools_runner import solve_instances
import hashlib
import hmac
import json
import requests

logger = configure_logger("optimisation.worker")


@shared_task(name="worker.solve_job")
def solve_job(job_id: str) -> None:
    db: Session = SessionLocal()
    start = time.perf_counter()
    try:
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is None:
            return

        logger.info("job.start", extra={"job_id": job_id, "status": "RUNNING", "component": "worker"})
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
            logger.warning(
                "job.timeout",
                extra={"job_id": job_id, "status": job.status, "component": "worker"},
            )
        except Exception as exc:
            job.status = "FAILED"
            job.error = str(exc)
            logger.exception(
                "job.error",
                extra={"job_id": job_id, "status": job.status, "component": "worker"},
            )
        finally:
            job.finished_at = datetime.utcnow()
            db.commit()
            _send_webhooks(db, job)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "job.complete",
                extra={
                    "job_id": job_id,
                    "status": job.status,
                    "duration_ms": round(duration_ms, 2),
                    "component": "worker",
                },
            )
    finally:
        db.close()


def _send_webhooks(db: Session, job: Job) -> None:
    event_name = "optimization.completed" if job.status == "COMPLETED" else "optimization.failed"
    payload = {
        "event": event_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {"job_id": job.id, "status": job.status},
    }
    raw_payload = json.dumps(payload)
    endpoints = (
        db.query(WebhookEndpoint)
        .filter(WebhookEndpoint.org_id == job.org_id, WebhookEndpoint.active.is_(True))
        .all()
    )
    for endpoint in endpoints:
        if endpoint.events and event_name not in endpoint.events:
            continue
        headers = {"Content-Type": "application/json"}
        if endpoint.secret:
            digest = hmac.new(
                endpoint.secret.encode("utf-8"),
                raw_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = digest
        try:
            requests.post(endpoint.url, data=raw_payload, headers=headers, timeout=4)
        except Exception:
            continue
