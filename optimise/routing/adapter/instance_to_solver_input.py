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

    return SolverInput(
        time_matrix=instance.time_matrix,
        distance_matrix=instance.distance_matrix,
        time_windows=instance.time_windows,
        service_durations=instance.service_durations,
        num_vehicles=instance.num_vehicles,
        starts=instance.starts,
        ends=instance.ends,
        breaks=breaks,
        max_working_time=instance.max_working_time,
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
        num_depots=getattr(instance, "nb_depots", None),
        vehicle_penalty=getattr(instance, "vehicle_penalty", None),
        time_window_tolerance=time_window_tolerance,
        break_time_tolerance=break_time_tolerance,
        break_day_end=break_day_end,
        meta={"instance_name": getattr(instance, "name", None)},
    )
