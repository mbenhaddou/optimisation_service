from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_api_key, get_db
from ..queue import enqueue_job
from ..schemas import JobListResponse, JobResponse
from ..services.job_service import JobService
from ..services.mapping import ensure_mapping_defaults
from ..services.rate_limit import enforce_rate_limit
from ..services.usage import compute_node_count, compute_usage_units, monthly_usage_units

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.post("/solve", response_model=JobResponse)
async def submit_job(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    api_key_id = get_api_key(request, db)
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)

    payload = ensure_mapping_defaults(payload)
    node_count = compute_node_count(payload)
    usage_units = compute_usage_units(payload)

    if settings.max_job_nodes and node_count > settings.max_job_nodes:
        raise HTTPException(
            status_code=422,
            detail=f"node_count {node_count} exceeds MAX_JOB_NODES",
        )

    if settings.max_job_units and usage_units > settings.max_job_units:
        raise HTTPException(
            status_code=422,
            detail=f"usage_units {usage_units} exceeds MAX_JOB_UNITS",
        )

    org_id = JobService.resolve_org_id(db, api_key_id)

    if settings.enforce_usage_limits and settings.free_tier_units > 0:
        if api_key_id:
            used_units = monthly_usage_units(db, api_key_id=api_key_id, org_id=org_id)
            if used_units + usage_units > settings.free_tier_units:
                raise HTTPException(
                    status_code=402,
                    detail=(
                        f"usage_units {used_units + usage_units} exceeds FREE_TIER_UNITS "
                        f"({settings.free_tier_units})."
                    ),
                )
        else:
            if usage_units > settings.free_tier_units:
                raise HTTPException(
                    status_code=402,
                    detail=(
                        f"usage_units {usage_units} exceeds FREE_TIER_UNITS "
                        f"({settings.free_tier_units})."
                    ),
                )

    job = JobService.create_job(
        db,
        payload=payload,
        node_count=node_count,
        usage_units=usage_units,
        api_key_id=api_key_id,
        org_id=org_id,
    )

    if settings.sync_execution:
        from ..services.solve import solve_job_inline

        job = solve_job_inline(db, job.id)
    else:
        enqueue_job(job.id)
        db.refresh(job)

    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, request: Request, db: Session = Depends(get_db)):
    api_key_id = get_api_key(request, db)
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)
    job = JobService.get_job(db, job_id, api_key_id=api_key_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    api_key_id = get_api_key(request, db)
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)
    items, total = JobService.list_jobs(db, limit=limit, offset=offset, api_key_id=api_key_id)
    return JobListResponse(items=items, total=total)
