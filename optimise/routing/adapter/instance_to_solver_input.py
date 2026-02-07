from typing import Any, List

from optimise.routing.defaults import DEFAULT_TIME_TOLERANCE_MINUTES, ROUTING_TIME_RESOLUTION
from optimise.routing.input.solver_input import SolverInput
from optimise.utils.dates import convert_units


def instance_to_solver_input(instance: Any) -> SolverInput:
    """
    Convert a legacy Instance object into a pure SolverInput.
    This is a compatibility adapter to support incremental refactors.
    """
    breaks: List[List] = []
    if hasattr(instance, "workers"):
        breaks = [w.get_schedule() for w in instance.workers]

    penalties: List[int] = []
    if hasattr(instance, "work_orders"):
        penalties = [wo.workorder_penalty for wo in instance.work_orders]
    else:
        penalties = getattr(instance, "penalties", [])

    time_window_tolerance = convert_units(
        DEFAULT_TIME_TOLERANCE_MINUTES,
        "minutes",
        getattr(instance, "language", "en"),
        ROUTING_TIME_RESOLUTION,
    )
    break_time_tolerance = convert_units(
        getattr(instance, "blocked_time_tol", 0),
        "minutes",
        getattr(instance, "language", "en"),
        ROUTING_TIME_RESOLUTION,
    )
    break_day_end = convert_units(
        24,
        "hours",
        getattr(instance, "language", "en"),
        ROUTING_TIME_RESOLUTION,
    ) - 1

    precedence_constraints: List[tuple] = []
    if hasattr(instance, "task_dependencies"):
        dependencies = getattr(instance, "task_dependencies", []) or []
        if hasattr(instance, "work_orders"):
            order_index = {str(wo.id): idx for idx, wo in enumerate(instance.work_orders)}
            num_depots = getattr(instance, "nb_depots", len(set(instance.starts)) if instance.starts else 1)
            for dependency in dependencies:
                before_id = dependency.get("task_id")
                after_ids = dependency.get("must_be_before") or []
                if before_id is None:
                    continue
                before_idx = order_index.get(str(before_id))
                if before_idx is None:
                    continue
                before_node = before_idx + num_depots
                for after_id in after_ids:
                    after_idx = order_index.get(str(after_id))
                    if after_idx is None:
                        continue
                    after_node = after_idx + num_depots
                    precedence_constraints.append((before_node, after_node))

    allowed_vehicles_by_node: dict[int, list[int]] = {}
    if hasattr(instance, "zone_restrictions"):
        zone_restrictions = getattr(instance, "zone_restrictions", []) or []
        if hasattr(instance, "work_orders") and hasattr(instance, "workers"):
            order_index = {str(wo.id): idx for idx, wo in enumerate(instance.work_orders)}
            vehicle_index = {str(worker.id): idx for idx, worker in enumerate(instance.workers)}
            num_depots = getattr(instance, "nb_depots", len(set(instance.starts)) if instance.starts else 1)
            for zone in zone_restrictions:
                task_ids = zone.get("task_ids") or []
                allowed_vehicles = zone.get("allowed_vehicles") or []
                if not task_ids or not allowed_vehicles:
                    continue
                allowed_indices = [
                    vehicle_index[vid] for vid in allowed_vehicles if vid in vehicle_index
                ]
                if not allowed_indices:
                    continue
                for task_id in task_ids:
                    idx = order_index.get(str(task_id))
                    if idx is None:
                        continue
                    node = idx + num_depots
                    allowed_vehicles_by_node[node] = allowed_indices

    return SolverInput(
        time_matrix=instance.time_matrix,
        distance_matrix=instance.distance_matrix,
        time_windows=instance.time_windows,
        service_durations=instance.service_durations,
        num_vehicles=instance.num_vehicles,
        starts=instance.starts,
        ends=instance.ends,
        breaks=breaks,
        soft_time_windows=getattr(instance, "soft_time_windows", []),
        precedence_constraints=precedence_constraints,
        allowed_vehicles_by_node=allowed_vehicles_by_node,
        max_working_time=instance.max_working_time,
        max_route_distance=getattr(instance, "max_route_distance", 0),
        allow_slack=instance.allow_slack,
        horizon=instance.horizon,
        penalties=penalties,
        location_priorities=getattr(instance, "location_priorities", []),
        distribute_load=getattr(instance, "distribute_load", False),
        minimize_vehicles=getattr(instance, "minimize_vehicles", False),
        account_for_priority=getattr(instance, "account_for_priority", False),
        enable_neighborhood_clustering=getattr(instance, "enable_neighborhood_clustering", False),
        neighborhood_clustering_distance=getattr(instance, "neighborhood_clustering_distance", None),
        neighborhood_clustering_penalty_factor=getattr(instance, "neighborhood_clustering_penalty_factor", None),
        haversine_distance=getattr(instance, "haversine_distance", None),
        use_walking_distances_when_possible=getattr(instance, "use_walking_distances_when_possible", False),
        walking_distances_threshold=getattr(instance, "walking_distances_threshold", None),
        first_solution_strategy=getattr(instance, "first_solution_strategy", None),
        local_search_metaheuristic=getattr(instance, "local_search_metaheuristic", None),
        time_limit_seconds=getattr(instance, "time_limit", None),
        no_improvement_limit=getattr(instance, "no_improvement_limit", None),
        objective=getattr(instance, "optimization_target", None),
        num_depots=getattr(instance, "nb_depots", None),
        vehicle_penalty=getattr(instance, "vehicle_penalty", None),
        time_window_tolerance=time_window_tolerance,
        break_time_tolerance=break_time_tolerance,
        break_day_end=break_day_end,
        meta={"instance_name": getattr(instance, "name", None)},
    )
