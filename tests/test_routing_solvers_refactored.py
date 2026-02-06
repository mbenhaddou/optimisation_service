import copy
import json
from pathlib import Path

from optimise.routing.defaults import (
    FAST_FIRST_SOLUTIONS,
    FAST_METAHEURISTIC_SEARCH,
    OPTIMIZED_FIRST_SOLUTIONS,
    OPTIMIZED_METAHEURISTIC_SEARCH,
)
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.defaults import (
    DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES,
    DEFAULT_RESULT_TYPE,
    DEFAULT_SLACK_MINUTES,
    DEFAULT_NO_IMPROVEMENT_LIMIT,
    ROUTING_TIME_RESOLUTION,
)
from optimise.routing.preprocessing.preprocess_request import preprocess_request
from optimise.routing.solver.ortools_runner import solve_instances
from optimise.utils.dates import convert_units


def _load_payload():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "optimise" / "routing" / "request_offline_deterministic.json"
    payload = json.loads(path.read_text())
    # Adjust to avoid short horizon when time_unit is minutes.
    if payload.get("time_unit") == "minutes":
        payload["time_unit"] = "hours"
        for order in payload.get("orders", []):
            if "work_hours" in order and isinstance(order["work_hours"], (int, float)):
                order["work_hours"] = order["work_hours"] / 60.0
    return payload


def _solve_request(payload):
    errors = []
    request = preprocess_request(payload, errors)
    instances = get_optimisation_instances(request)
    solutions = solve_instances(instances, solution_routing=None)
    assert errors == []
    return solutions, instances


def _parse_time_to_minutes(time_str: str) -> int:
    if not time_str:
        return 0
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + minutes


def test_routing_offline_smoke():
    solutions, _ = _solve_request(_load_payload())

    assert solutions
    results = solutions[0]
    assert "details" in results
    assert "dropped" in results
    assert "performance" in results

    day_keys = list(results["details"].keys())
    assert day_keys
    day = day_keys[0]
    assert results["details"][day]

    by_worker = results["details"][day]["by_worker"][0]
    assert "tour_steps" in by_worker
    assert len(by_worker["tour_steps"]) > 0


def test_routing_respects_visiting_hours():
    payload = _load_payload()
    solutions, _ = _solve_request(payload)
    results = solutions[0]

    day_keys = list(results["details"].keys())
    day = day_keys[0]
    by_worker = results["details"][day]["by_worker"][0]

    visiting_start = _parse_time_to_minutes("08:00")
    visiting_end = _parse_time_to_minutes("17:00")

    for step in by_worker["tour_steps"]:
        node = step.get("node", {})
        if not node or not node.get("id", "").startswith("WO-"):
            continue
        start_time = _parse_time_to_minutes(node.get("service_start_time"))
        assert visiting_start <= start_time <= visiting_end


def test_routing_parameters_defaults_and_strategies():
    payload = _load_payload()
    _, instances = _solve_request(payload)

    instance = instances[0]
    instance.update_strategies()
    expected_allow_slack = convert_units(
        DEFAULT_SLACK_MINUTES, "minutes", "en", ROUTING_TIME_RESOLUTION
    )
    expected_time_limit = convert_units(
        DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES, "minutes", "en", ROUTING_TIME_RESOLUTION
    )

    assert instance.allow_slack == expected_allow_slack
    assert instance.time_limit == expected_time_limit
    assert instance.result_type == DEFAULT_RESULT_TYPE
    assert instance.first_solution_strategy in FAST_FIRST_SOLUTIONS
    assert instance.local_search_metaheuristic in FAST_METAHEURISTIC_SEARCH
    assert instance.no_improvement_limit == DEFAULT_NO_IMPROVEMENT_LIMIT

    optimized_payload = _load_payload()
    optimized_payload["allow_slack"] = 0
    optimized_payload["result_type"] = "optimized"
    optimized_payload["no_improvement_limit"] = 60

    _, optimized_instances = _solve_request(optimized_payload)
    opt_instance = optimized_instances[0]
    opt_instance.update_strategies()

    assert opt_instance.allow_slack == 0
    assert opt_instance.result_type == "optimized"
    assert opt_instance.first_solution_strategy in OPTIMIZED_FIRST_SOLUTIONS
    assert opt_instance.local_search_metaheuristic in OPTIMIZED_METAHEURISTIC_SEARCH
    assert opt_instance.no_improvement_limit == 60
