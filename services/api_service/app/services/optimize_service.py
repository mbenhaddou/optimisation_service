from __future__ import annotations

from dataclasses import dataclass
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from optimise.routing.defaults import DEFAULT_DRIVING_SPEED_KMH, DEFAULT_SLACK_MINUTES
from optimise.routing.preprocessing.preprocess_request import preprocess_request
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.solver.ortools_runner import solve_instances

from ..schemas import OptimizeRequest, Depot, Location


@dataclass(frozen=True)
class LegacyBuildResult:
    legacy_request: Dict[str, Any]
    period_start: datetime
    period_end: datetime


def _collect_window_bounds(request: OptimizeRequest) -> Tuple[datetime, datetime]:
    candidates: List[datetime] = []

    if request.traffic and request.traffic.departure_time:
        candidates.append(request.traffic.departure_time)

    for vehicle in request.vehicles:
        for window in vehicle.available_time_windows:
            candidates.append(window.start)
            candidates.append(window.end)

    for task in request.tasks:
        for window in task.time_windows:
            candidates.append(window.start)
            candidates.append(window.end)

    if not candidates:
        now = datetime.utcnow()
        return now, now

    start = min(candidates)
    end = max(candidates)
    return start, end


def _normalize_priority(priority: Optional[int]) -> int:
    if priority is None:
        return 3
    value = max(1, min(10, int(priority)))
    return max(1, min(5, (value + 1) // 2))


def _format_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def _format_time(value: datetime) -> str:
    return value.strftime("%H:%M:%S")


def _window_or_default(
    windows: List[Any],
    default_start: datetime,
    default_end: datetime,
) -> Tuple[datetime, datetime]:
    if windows:
        return windows[0].start, windows[0].end
    return default_start, default_end


def _to_depot(location: Any, depot_id: str) -> Dict[str, Any]:
    address = location.address or ""
    return {
        "id": depot_id,
        "street": address,
        "postal_code": "",
        "city": "",
        "country": "",
        "latitude": location.lat,
        "longitude": location.lng,
        "address": address,
    }


def _resolve_depot(
    depots: List[Depot],
    depot_id: Optional[str],
    fallback: Location,
    default_start: datetime,
    default_end: datetime,
) -> Tuple[Dict[str, Any], Tuple[datetime, datetime]]:
    if depot_id:
        for depot in depots:
            if depot.id == depot_id:
                window = _window_or_default(depot.time_windows, default_start, default_end)
                return _to_depot(depot.location, depot.id), window
    return _to_depot(fallback, depot_id or "DEPOT"), _window_or_default([], default_start, default_end)


def build_legacy_request(request: OptimizeRequest) -> LegacyBuildResult:
    period_start, period_end = _collect_window_bounds(request)
    horizon_days = max(1, (period_end.date() - period_start.date()).days + 1)

    objectives_primary = request.objectives.primary.lower().strip()
    if objectives_primary in {"minimize_total_duration", "minimize_duration"}:
        optimization_target = "duration"
    elif objectives_primary in {"minimize_total_distance", "minimize_distance"}:
        optimization_target = "distance"
    else:
        raise ValueError("Unsupported primary objective for V1")

    if request.options and request.options.eco_routing:
        optimization_target = "distance"

    has_priority = any(task.priority is not None for task in request.tasks)
    constraints = request.constraints

    allow_slack = 0
    if constraints and constraints.allow_overtime:
        allow_slack = DEFAULT_SLACK_MINUTES

    max_working_time = None
    if constraints and constraints.max_route_duration_minutes:
        max_working_time = int(constraints.max_route_duration_minutes)

    max_route_distance = None
    if constraints and constraints.max_route_distance_km is not None:
        max_route_distance = int(constraints.max_route_distance_km * 1000)

    vehicle_ranges = [
        int(v.range_km * 1000)
        for v in request.vehicles
        if getattr(v, "range_km", None)
    ]
    if vehicle_ranges:
        if max_route_distance is None:
            max_route_distance = min(vehicle_ranges)
        else:
            max_route_distance = min(max_route_distance, min(vehicle_ranges))

    legacy_orders: List[Dict[str, Any]] = []
    for task in request.tasks:
        tw_start, tw_end = _window_or_default(task.time_windows, period_start, period_end)
        if not task.time_windows and task.preferred_time_windows:
            tw_start, tw_end = _window_or_default(
                task.preferred_time_windows, period_start, period_end
            )
        preferred_window = task.preferred_time_windows[0] if task.preferred_time_windows else None
        skill = "default"
        if task.required_skills:
            skill = task.required_skills[0]
        order = {
            "id": task.id,
            "skill": skill,
            "priority": _normalize_priority(task.priority),
            "latitude": task.location.lat,
            "longitude": task.location.lng,
            "visits_schedule": [],
            "visiting_hour_start": _format_time(tw_start),
            "visiting_hour_end": _format_time(tw_end),
            "work_hours": task.service_duration_minutes,
            "earliest_start_date": _format_date(tw_start),
            "earliest_start_time": _format_time(tw_start),
            "latest_end_date": _format_date(tw_end),
            "latest_end_time": _format_time(tw_end),
        }
        if constraints and constraints.required_task_assignments:
            if task.id in constraints.required_task_assignments:
                order["required_assignment"] = True
        if preferred_window:
            order["preferred_time_window_start"] = preferred_window.start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            order["preferred_time_window_end"] = preferred_window.end.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        if task.soft_time_window_penalty is not None:
            order["soft_time_window_penalty"] = float(task.soft_time_window_penalty)
        legacy_orders.append(order)

    teams: Dict[str, Any] = {}
    team_name_counts: Dict[str, int] = {}
    for index, vehicle in enumerate(request.vehicles, start=1):
        depot, depot_window = _resolve_depot(
            request.depots, vehicle.depot_id, vehicle.start_location, period_start, period_end
        )
        day_start, day_end = _window_or_default(
            vehicle.available_time_windows, depot_window[0], depot_window[1]
        )

        pause_start = "00:00:00"
        pause_end = "00:00:00"
        if vehicle.breaks:
            break_window = vehicle.breaks[0].time_window
            pause_start_dt = break_window.earliest
            pause_end_dt = pause_start_dt + timedelta(
                minutes=int(vehicle.breaks[0].duration_minutes)
            )
            pause_start = _format_time(pause_start_dt)
            pause_end = _format_time(pause_end_dt)

        worker = {
            "e_id": vehicle.id,
            "skills": vehicle.skills or ["default"],
            "street": depot["street"],
            "postal_code": depot["postal_code"],
            "city": depot["city"],
            "country": depot["country"],
            "address": depot["address"],
            "latitude": depot["latitude"],
            "longitude": depot["longitude"],
            "blocked_times": [],
            "shifts": [],
            "day_starts_at": _format_time(day_start),
            "day_ends_at": _format_time(day_end),
            "pause_starts_at": pause_start,
            "pause_ends_at": pause_end,
        }
        depot_key = vehicle.depot_id or f"{vehicle.start_location.lat},{vehicle.start_location.lng}"
        team_key = f"{vehicle.team_id or vehicle.id}:{depot_key}"
        if team_key not in teams:
            base_name = f"team_{vehicle.team_id or vehicle.id}"
            if base_name not in team_name_counts:
                team_name_counts[base_name] = 0
            if base_name in team_name_counts and team_name_counts[base_name] > 0:
                team_name = f"{base_name}_{team_name_counts[base_name] + 1}"
            else:
                team_name = base_name
            team_name_counts[base_name] += 1
            teams[team_key] = {"name": team_name, "depot": depot, "workers": []}
        teams[team_key]["workers"].append(worker)

    teams_payload: Dict[str, Any] = {}
    for team_key, team_payload in teams.items():
        teams_payload[team_payload["name"]] = {
            "depot": team_payload["depot"],
            "workers": team_payload["workers"],
        }

    root_depot, _ = _resolve_depot(
        request.depots,
        request.vehicles[0].depot_id if request.vehicles else None,
        request.vehicles[0].start_location,
        period_start,
        period_end,
    )

    legacy_request: Dict[str, Any] = {
        "language": "en",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "time_unit": "minutes",
        "optimization_target": optimization_target,
        "optimization_horizon": horizon_days,
        "period_start": period_start.strftime("%Y-%m-%d %H:%M:%S"),
        "enable_geocoding": False,
        "distance_matrix_method": "haversine",
        "driving_speed_kmh": DEFAULT_DRIVING_SPEED_KMH,
        "deterministic": True,
        "random_seed": 42,
        "account_for_priority": has_priority,
        "orders": legacy_orders,
        "teams": teams_payload,
        "depot": root_depot,
        "distribute_load": bool(constraints.balance_routes) if constraints else False,
        "minimize_vehicles": bool(request.objectives.minimize_vehicles)
        if request.objectives and request.objectives.minimize_vehicles
        else False,
        "allow_slack": allow_slack,
        "max_working_time": max_working_time,
        "max_route_distance": max_route_distance,
    }

    if constraints and constraints.task_dependencies:
        legacy_request["task_dependencies"] = constraints.task_dependencies
    if constraints and constraints.zone_restrictions:
        legacy_request["zone_restrictions"] = constraints.zone_restrictions

    if request.routing:
        if request.routing.distance_matrix_method:
            legacy_request["distance_matrix_method"] = request.routing.distance_matrix_method
        if request.routing.routing_engine_url:
            legacy_request["routing_engine_url"] = request.routing.routing_engine_url

    if request.matrix:
        legacy_request["precomputed_distance_matrix"] = request.matrix.distances_m
        legacy_request["precomputed_time_matrix"] = request.matrix.durations_s
    if request.traffic:
        legacy_request["traffic_mode"] = request.traffic.mode
        legacy_request["traffic_include_historical"] = bool(
            request.traffic.include_historical_patterns
        )

    return LegacyBuildResult(
        legacy_request=legacy_request,
        period_start=period_start,
        period_end=period_end,
    )


def run_optimization(legacy_request: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    routing_engine_url = legacy_request.get("routing_engine_url")
    previous_routing_engine = os.environ.get("ROUTING_ENGINE")
    try:
        if routing_engine_url:
            os.environ["ROUTING_ENGINE"] = routing_engine_url
        preprocessed = preprocess_request(legacy_request, errors)
        instances = get_optimisation_instances(preprocessed)
        results = solve_instances(instances)
        return {"solutions": results, "errors": errors}
    finally:
        if routing_engine_url:
            if previous_routing_engine is None:
                os.environ.pop("ROUTING_ENGINE", None)
            else:
                os.environ["ROUTING_ENGINE"] = previous_routing_engine
