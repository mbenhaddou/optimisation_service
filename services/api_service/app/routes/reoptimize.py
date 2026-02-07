from __future__ import annotations

import time
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_api_key, get_db
from ..schemas import (
    AlternativeSolution,
    OptimizeMetrics,
    OptimizeResponse,
    ReoptimizeRequest,
    WarningMessage,
)
from ..services.mapping import ensure_mapping_defaults
from ..services.optimize_service import build_legacy_request, run_optimization
from ..services.rate_limit import enforce_rate_limit
from ..services.reoptimize_service import apply_reoptimize_changes
from ..services.usage import compute_node_count, compute_usage_units, monthly_usage_units
from .optimize import (
    _build_metrics,
    _build_routes,
    _build_warnings,
    _fetch_osrm_geometry,
    _resolve_osrm_base,
)


router = APIRouter(prefix="/v1", tags=["reoptimize"])


@router.post("/reoptimize", response_model=OptimizeResponse)
async def reoptimize(
    request: Request,
    payload: ReoptimizeRequest = Body(...),
    db: Session = Depends(get_db),
):
    api_key_id = get_api_key(request, db, required_scopes={"solve:write"})
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)

    updated_request = apply_reoptimize_changes(payload.base_request, payload.changes)

    if not updated_request.vehicles or not updated_request.tasks:
        raise HTTPException(
            status_code=400,
            detail="vehicles and tasks must not be empty after applying changes",
        )

    node_count = compute_node_count(
        {"tasks": updated_request.tasks, "vehicles": updated_request.vehicles}
    )
    usage_units = compute_usage_units(
        {"tasks": updated_request.tasks, "vehicles": updated_request.vehicles}
    )

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

    if settings.enforce_usage_limits and settings.free_tier_units > 0:
        used_units = monthly_usage_units(db, api_key_id=api_key_id)
        if used_units + usage_units > settings.free_tier_units:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"usage_units {used_units + usage_units} exceeds FREE_TIER_UNITS "
                    f"({settings.free_tier_units})."
                ),
            )

    start_time = time.perf_counter()
    try:
        build_result = build_legacy_request(updated_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    legacy_request = dict(build_result.legacy_request)
    if settings.mapping_service_url and not (
        updated_request.routing and updated_request.routing.distance_matrix_method
    ):
        legacy_request["distance_matrix_method"] = "osrm"
    legacy_request = ensure_mapping_defaults(legacy_request)

    if updated_request.optimization and updated_request.optimization.max_computation_time_seconds:
        legacy_request["time_limit"] = int(
            updated_request.optimization.max_computation_time_seconds
        )

    try:
        raw = run_optimization(legacy_request)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    solutions = raw.get("solutions", [])

    task_durations = {
        task.id: task.service_duration_minutes for task in updated_request.tasks
    }
    routes, unassigned, assigned_tasks = _build_routes(solutions, task_durations)

    geometry_warnings: List[WarningMessage] = []
    if updated_request.options and updated_request.options.include_route_geometry:
        osrm_base = _resolve_osrm_base(updated_request)
        if osrm_base:
            for route in routes:
                geometry = _fetch_osrm_geometry(osrm_base, route.stops)
                route.route_geometry = geometry
                if geometry is None:
                    geometry_warnings.append(
                        WarningMessage(
                            type="route_geometry_unavailable",
                            message="OSRM route geometry could not be fetched for one or more routes.",
                        )
                    )
        else:
            geometry_warnings.append(
                WarningMessage(
                    type="route_geometry_unavailable",
                    message="Routing engine URL not configured; route geometry omitted.",
                )
            )

    total_tasks = len(updated_request.tasks)
    solution_quality = (assigned_tasks / total_tasks) if total_tasks else 1.0

    warnings = _build_warnings(updated_request)
    warnings.extend(geometry_warnings)
    if updated_request.traffic and updated_request.traffic.mode == "predictive":
        warnings.append(
            WarningMessage(
                type="predictive_traffic_placeholder",
                message="Predictive traffic mode is enabled; travel times are still sourced from routing engine data.",
            )
        )
    if payload.changes and payload.changes.minimize_changes:
        warnings.append(
            WarningMessage(
                type="minimize_changes_not_enforced",
                message="minimize_changes is not enforced in the current solver.",
            )
        )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    metrics = _build_metrics(routes, assigned_tasks, total_tasks, updated_request)

    alternative_solutions = None
    if (
        updated_request.optimization
        and updated_request.optimization.return_alternative_solutions
    ):
        alternative_solutions = []
        requested = max(
            1, int(updated_request.optimization.return_alternative_solutions)
        )
        alternative_solutions.append(
            AlternativeSolution(
                quality_score=round(solution_quality, 3),
                routes=routes,
                metrics=metrics,
            )
        )
        for idx in range(1, requested):
            alt_request = dict(legacy_request)
            alt_request["deterministic"] = False
            alt_request["random_seed"] = 200 + idx
            alt_request["randomize_response"] = True
            try:
                alt_raw = run_optimization(alt_request)
            except Exception:
                continue
            alt_solutions = alt_raw.get("solutions", [])
            alt_routes, _, alt_assigned = _build_routes(
                alt_solutions, task_durations
            )
            alt_quality = (alt_assigned / total_tasks) if total_tasks else 1.0
            alt_metrics = _build_metrics(
                alt_routes, alt_assigned, total_tasks, updated_request
            )
            alternative_solutions.append(
                AlternativeSolution(
                    quality_score=round(alt_quality, 3),
                    routes=alt_routes,
                    metrics=alt_metrics,
                )
            )

    return OptimizeResponse(
        status="success",
        computation_time_ms=elapsed_ms,
        solution_quality_score=round(solution_quality, 3),
        routes=routes,
        unassigned_tasks=unassigned,
        metrics=metrics,
        warnings=warnings or None,
        alternative_solutions=alternative_solutions,
    )
