import copy
from dataclasses import replace
from datetime import timedelta
from typing import Any, Dict, List

from optimise.routing.adapter.instance_to_solver_input import instance_to_solver_input
from optimise.routing.config.solve_profile import SolveProfile
from optimise.routing.constants import translate
from optimise.routing.defaults import (
    SEARCH_WORKERS,
    SOLVER_LOG_SEARCH_PROGRESS,
    SOLVER_MAX_SEARCH_TIME_IN_SECONDS,
)
from optimise.routing.model.solution import Solution
from optimise.routing.solver.ortools_builder import OrtoolsSolver
from solution_routing.solution_routing_CRUD import solution_routing_crud


def _post_process_solution(solution_list: List[Solution]) -> Dict[str, Any]:
    results_str: Dict[str, List[str]] = {}
    results_json: Dict[str, Any] = {"details": {}}
    dropped_tours: List[Dict[str, Any]] = []

    if solution_list is None:
        return {}

    instance = None
    for solution in solution_list:
        instance = solution.instance
        day = solution.current_date
        day_key = str(day.date()) if hasattr(day, "date") else str(day)
        if day_key not in results_str:
            results_str[day_key] = []
            results_json["details"][day_key] = {
                "by_worker": [],
                "summaries": [],
                "strings": [],
                "objective_value": 0,
            }
        if solution.results is not None:
            results_json["details"][day_key]["by_worker"].extend(
                copy.deepcopy(solution.results["by_worker"])
            )
            results_json["details"][day_key]["summaries"].append(
                copy.deepcopy(solution.results["summary"])
            )
            results_json["details"][day_key]["strings"].append(solution.visualize())
            results_json["details"][day_key]["objective_value"] = solution.objective_value

    if instance is None:
        return results_json

    dropped = instance.get_dropped_nodes()
    for d in dropped:
        message = d.validate_optimization_period(
            solution_list[0].instance.period_start,
            solution_list[0].instance.period_start
            + timedelta(days=solution_list[0].instance.optimization_horizon),
        )
        if not d.has_been_scheduled:
            d.reason_for_not_scheduling = translate(
                "OUTSIDE_OPTIMISATION_PERIOD", instance.language
            )
        elif d.errors:
            d.reason_for_not_scheduling = " | ".join(d.errors)
        elif message:
            d.reason_for_not_scheduling = message
        elif d.errors:
            d.reason_for_not_scheduling = "\n".join(d.errors)
        else:
            d.reason_for_not_scheduling = translate(
                "WAS_SCHEDULED_BUT_DROPPED", instance.language
            )
    dropped_tours.extend([d.to_dict() for d in dropped])

    results_json["dropped"] = dropped_tours

    # Compute performance sums
    total_sums: Dict[str, Any] = {}
    for date in results_json["details"]:
        summaries = results_json["details"][date].get("summaries", [])
        for summary in summaries:
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    if key not in total_sums:
                        total_sums[key] = 0
                    total_sums[key] += value
    results_json["performance"] = total_sums

    return results_json


def solve_instances(instances: List[Any], solution_routing=None) -> List[Dict[str, Any]]:
    results = []
    for instance in instances:
        results.append(_solve_instance(instance, solution_routing))
    return results


def _solve_instance(instance: Any, solution_routing=None) -> Dict[str, Any]:
    if solution_routing is not None:
        solution_routing.status_msg = translate(
            "optimizing_for_skill", instance.language
        ).format(str(instance))
        solution_routing_crud.update(solution_routing)

    horizon = instance.optimization_horizon
    day_start = instance.period_start
    solutions: List[Solution] = []

    for day_i in range(horizon):
        day = day_start + timedelta(days=day_i)
        instance.init_instance(day)

        if not instance.can_schedule_new_orders:
            solutions.append(Solution(instance, None, None, None))
            continue

        solver_input = instance_to_solver_input(instance)
        profile = SolveProfile.from_solver_input(solver_input)

        if (
            SOLVER_MAX_SEARCH_TIME_IN_SECONDS > 0
            and (profile.time_limit_seconds is None or profile.time_limit_seconds <= 0)
        ):
            profile = replace(
                profile, time_limit_seconds=SOLVER_MAX_SEARCH_TIME_IN_SECONDS
            )
        if SOLVER_LOG_SEARCH_PROGRESS and not profile.log_search:
            profile = replace(profile, log_search=True)
        if SEARCH_WORKERS > 0 and profile.search_workers is None:
            profile = replace(profile, search_workers=SEARCH_WORKERS)

        solver = OrtoolsSolver()
        assignment, routing, manager = solver.solve(solver_input, profile)
        if assignment is not None:
            solution = Solution(instance, assignment, routing, manager)
            solutions.append(solution)
            solution.set_scheduled_workorder()
        else:
            solutions.append(Solution(instance, None, None, None))

    return _post_process_solution(solutions)
