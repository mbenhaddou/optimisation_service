from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_api_key, get_db
from ..schemas import (
    OptimizeRequest,
    OptimizeResponse,
    OptimizeMetrics,
    RouteResponse,
    RouteStop,
    StopLocation,
    UnassignedTaskResponse,
    WarningMessage,
    AlternativeSolution,
)
from ..services.mapping import ensure_mapping_defaults
from ..services.optimize_service import build_legacy_request, run_optimization
from ..services.rate_limit import enforce_rate_limit
from ..services.usage import compute_node_count, compute_usage_units, monthly_usage_units

router = APIRouter(prefix="/v1", tags=["optimize"])

CARBON_KG_PER_KM = 0.21


def _combine_date_time(date_str: str, time_str: str) -> Optional[datetime]:
    if not date_str or not time_str:
        return None
    time_str = time_str.strip()
    if len(time_str) == 5:
        time_str = f"{time_str}:00"
    try:
        return datetime.fromisoformat(f"{date_str}T{time_str}")
    except ValueError:
        return None


def _to_minutes(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric > 1000:
        return round(numeric / 60.0, 2)
    return round(numeric, 2)


def _to_km(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value) / 1000.0, 3)
    except (TypeError, ValueError):
        return None


def _build_metrics(
    routes: List[RouteResponse],
    assigned_tasks: int,
    total_tasks: int,
    payload: OptimizeRequest,
) -> OptimizeMetrics:
    total_distance_km = sum(route.total_distance_km for route in routes)
    total_duration_minutes = sum(route.total_duration_minutes for route in routes)
    total_service_minutes = sum(
        route.total_service_time_minutes or 0 for route in routes
    )

    unassigned_count = max(0, total_tasks - assigned_tasks)

    max_tasks = [v.max_tasks for v in payload.vehicles if v.max_tasks]
    avg_utilization = None
    if max_tasks:
        avg_utilization = assigned_tasks / max(1, sum(max_tasks))

    metrics = OptimizeMetrics(
        total_distance_km=round(total_distance_km, 3),
        total_duration_minutes=round(total_duration_minutes, 2),
        total_service_time_minutes=round(total_service_minutes, 2),
        total_cost=None,
        average_vehicle_utilization=round(avg_utilization, 3)
        if avg_utilization is not None
        else None,
        tasks_assigned=assigned_tasks,
        tasks_unassigned=unassigned_count,
    )
    if payload.options and payload.options.calculate_carbon_footprint:
        metrics.carbon_kg = round(total_distance_km * CARBON_KG_PER_KM, 3)
    return metrics


def _build_routes(
    raw_results: List[Dict[str, Any]],
    task_durations: Dict[str, int],
) -> Tuple[List[RouteResponse], List[UnassignedTaskResponse], int]:
    routes: List[RouteResponse] = []
    unassigned: List[UnassignedTaskResponse] = []
    assigned_tasks = 0

    for result in raw_results:
        for dropped in result.get("dropped", []):
            unassigned.append(
                UnassignedTaskResponse(
                    task_id=str(dropped.get("id", "")),
                    reason=dropped.get("reason_for_not_scheduling"),
                    details=dropped.get("reason_for_not_scheduling"),
                )
            )

        details = result.get("details", {})
        for _, day_details in details.items():
            for worker in day_details.get("by_worker", []):
                tour_steps = worker.get("tour_steps", [])
                if not tour_steps:
                    continue
                stops: List[RouteStop] = []
                for idx, step in enumerate(tour_steps):
                    node = step.get("node", {})
                    node_id = str(node.get("id", ""))
                    node_date = node.get("date")
                    start_time = node.get("service_start_time")
                    end_time = node.get("service_end_time")
                    arrival = _combine_date_time(node_date, start_time)
                    departure = _combine_date_time(node_date, end_time)

                    stop_type = "task"
                    if idx == 0:
                        stop_type = "start"
                    elif idx == len(tour_steps) - 1:
                        stop_type = "end"

                    service_minutes = None
                    if stop_type == "task":
                        service_minutes = task_durations.get(node_id)

                    if stop_type == "task":
                        assigned_tasks += 1

                    stops.append(
                        RouteStop(
                            sequence=idx,
                            type=stop_type,
                            task_id=node_id if stop_type == "task" else None,
                            location=StopLocation(
                                lat=node.get("latitude"),
                                lng=node.get("longitude"),
                            ),
                            arrival_time=arrival,
                            departure_time=departure,
                            service_duration_minutes=service_minutes,
                            waiting_time_minutes=None,
                            distance_from_previous_km=_to_km(
                                node.get("traveled_distance_from_last_node")
                            ),
                            duration_from_previous_minutes=_to_minutes(
                                node.get("travel_time_from_last_node")
                            ),
                        )
                    )

                total_distance_km = _to_km(worker.get("total_distance")) or 0.0
                total_duration_minutes = _to_minutes(worker.get("total_tour_time")) or 0.0
                total_service_minutes = sum(
                    task_durations.get(stop.task_id, 0)
                    for stop in stops
                    if stop.type == "task"
                )

                routes.append(
                    RouteResponse(
                        vehicle_id=str(worker.get("id")),
                        total_distance_km=total_distance_km,
                        total_duration_minutes=total_duration_minutes,
                        total_service_time_minutes=total_service_minutes,
                        total_cost=None,
                        stops=stops,
                    )
                )

    return routes, unassigned, assigned_tasks


def _build_warnings(payload: OptimizeRequest) -> List[WarningMessage]:
    warnings: List[WarningMessage] = []
    for task in payload.tasks:
        if not task.time_windows:
            if task.preferred_time_windows:
                window = task.preferred_time_windows[0]
            else:
                continue
        else:
            window = task.time_windows[0]
        duration_minutes = task.service_duration_minutes
        if (window.end - window.start) < timedelta(minutes=duration_minutes):
            warnings.append(
                WarningMessage(
                    type="tight_time_window",
                    task_ids=[task.id],
                    message="Task time window is shorter than service duration.",
                )
            )
        if task.time_windows and task.preferred_time_windows and task.soft_time_window_penalty is None:
            warnings.append(
                WarningMessage(
                    type="preferred_time_window_missing_penalty",
                    task_ids=[task.id],
                    message="Preferred time windows require a soft_time_window_penalty to be enforced.",
                )
            )
    if payload.constraints and payload.constraints.zone_restrictions:
        invalid = [
            zone
            for zone in payload.constraints.zone_restrictions
            if not zone.get("task_ids") or not zone.get("allowed_vehicles")
        ]
        if invalid:
            warnings.append(
                WarningMessage(
                    type="zone_restrictions_partial",
                    message="zone_restrictions without task_ids or allowed_vehicles were ignored.",
                )
            )
    return warnings


def _resolve_osrm_base(payload: OptimizeRequest) -> Optional[str]:
    if payload.routing and payload.routing.routing_engine_url:
        return payload.routing.routing_engine_url
    if settings.mapping_service_url:
        return settings.mapping_service_url
    return os.getenv("ROUTING_ENGINE")


def _fetch_osrm_geometry(base_url: str, stops: List[RouteStop]) -> Optional[List[StopLocation]]:
    coords = [
        f"{stop.location.lng},{stop.location.lat}"
        for stop in stops
        if stop.location and stop.location.lat is not None and stop.location.lng is not None
    ]
    if len(coords) < 2:
        return None

    url = f"{base_url.rstrip('/')}/route/v1/driving/{';'.join(coords)}"
    try:
        res = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=8)
        if not res.ok:
            return None
        data = res.json()
        geometry = data.get("routes", [{}])[0].get("geometry", {})
        points = geometry.get("coordinates")
        if not points:
            return None
        return [StopLocation(lat=coord[1], lng=coord[0]) for coord in points]
    except Exception:
        return None


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(
    request: Request,
    payload: OptimizeRequest = Body(...),
    db: Session = Depends(get_db),
):
    api_key_id = get_api_key(request, db, required_scopes={"solve:write"})
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)

    if not payload.vehicles:
        raise HTTPException(
            status_code=400,
            detail={"message": "vehicles must not be empty", "field": "vehicles"},
        )
    if not payload.tasks:
        raise HTTPException(
            status_code=400,
            detail={"message": "tasks must not be empty", "field": "tasks"},
        )

    node_count = compute_node_count({"tasks": payload.tasks, "vehicles": payload.vehicles})
    usage_units = compute_usage_units({"tasks": payload.tasks, "vehicles": payload.vehicles})

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
        build_result = build_legacy_request(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    legacy_request = dict(build_result.legacy_request)
    if settings.mapping_service_url and not (
        payload.routing and payload.routing.distance_matrix_method
    ):
        legacy_request["distance_matrix_method"] = "osrm"
    legacy_request = ensure_mapping_defaults(legacy_request)

    if payload.optimization and payload.optimization.max_computation_time_seconds:
        legacy_request["time_limit"] = int(payload.optimization.max_computation_time_seconds)

    try:
        raw = run_optimization(legacy_request)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    solutions = raw.get("solutions", [])

    task_durations = {task.id: task.service_duration_minutes for task in payload.tasks}
    routes, unassigned, assigned_tasks = _build_routes(solutions, task_durations)

    geometry_warnings: List[WarningMessage] = []
    if payload.options and payload.options.include_route_geometry:
        osrm_base = _resolve_osrm_base(payload)
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

    total_tasks = len(payload.tasks)
    solution_quality = (assigned_tasks / total_tasks) if total_tasks else 1.0

    warnings = _build_warnings(payload)
    warnings.extend(geometry_warnings)
    if payload.traffic and payload.traffic.mode == "predictive":
        warnings.append(
            WarningMessage(
                type="predictive_traffic_placeholder",
                message="Predictive traffic mode is enabled; travel times are still sourced from routing engine data.",
            )
        )
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    metrics = _build_metrics(routes, assigned_tasks, total_tasks, payload)

    alternative_solutions = None
    if payload.optimization and payload.optimization.return_alternative_solutions:
        alternative_solutions = []
        requested = max(1, int(payload.optimization.return_alternative_solutions))
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
            alt_request["random_seed"] = 100 + idx
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
                alt_routes, alt_assigned, total_tasks, payload
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
