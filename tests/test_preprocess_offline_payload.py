import json
from pathlib import Path

from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.preprocessing.preprocess_request import preprocess_request
from optimise.routing.defaults import (
    DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES,
    DEFAULT_SLACK_MINUTES,
    ROUTING_TIME_RESOLUTION,
)
from optimise.utils.dates import convert_units


def _load_offline_request():
    path = Path("optimise/routing/request_offline_deterministic.json")
    return json.loads(path.read_text())


def test_preprocess_offline_request_builds_instance():
    errors = []
    request = preprocess_request(_load_offline_request(), errors)
    instances = get_optimisation_instances(request)

    assert errors == []
    assert len(instances) == 1

    instance = instances[0]
    instance.init_instance(instance.period_start)
    assert instance.time_matrix
    assert instance.distance_matrix is not None
    assert len(instance.distance_matrix) > 0
    assert instance.haversine_distance is not None
    assert instance.work_orders[0].latitude != instance.work_orders[1].latitude
    assert instance.work_orders[0].longitude != instance.work_orders[1].longitude


def test_preprocess_defaults_applied():
    errors = []
    request = preprocess_request(_load_offline_request(), errors)
    instances = get_optimisation_instances(request)

    instance = instances[0]
    expected_allow_slack = convert_units(
        DEFAULT_SLACK_MINUTES, "minutes", "en", ROUTING_TIME_RESOLUTION
    )
    expected_time_limit = convert_units(
        DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES,
        "minutes",
        "en",
        ROUTING_TIME_RESOLUTION,
    )

    assert instance.allow_slack == expected_allow_slack
    assert instance.time_limit == expected_time_limit
