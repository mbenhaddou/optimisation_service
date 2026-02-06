from datetime import datetime
from unittest.mock import patch

from optimise.routing.model.instance import Instance


def _base_instance():
    return Instance(
        name="test",
        language="en",
        period_start=datetime(2024, 1, 1, 0, 0, 0),
        time_unit="minutes",
        date_format="%Y-%m-%d %H:%M:%S",
        start_at="depot",
        end_at="depot",
        optimization_horizon=1,
        distance_matrix_method="haversine",
    )


def test_instance_haversine_generates_time_matrix():
    instance = _base_instance()

    worker = type("Worker", (), {})()
    worker.is_working = True
    worker.depot = {
        "id": "d1",
        "address": "Depot",
        "latitude": 0.0,
        "longitude": 0.0,
    }
    worker.address = "Home"
    worker.latitude = 0.0
    worker.longitude = 0.0
    worker.get_schedule = lambda: []
    worker.init_worker = lambda: None
    worker.day_starts_at = datetime(2024, 1, 1, 0, 0, 0).time()
    worker.day_ends_at = datetime(2024, 1, 1, 23, 59, 59).time()
    worker.pause_starts_at = datetime(2024, 1, 1, 0, 0, 0).time()
    worker.pause_ends_at = datetime(2024, 1, 1, 0, 0, 0).time()
    worker.tour_steps = []
    worker.id = "w1"
    instance.add_worker(worker)

    class WorkOrderStub:
        def __init__(self):
            self.address = "Order"
            self.latitude = 0.0
            self.longitude = 0.01
            self.work_order_duration = 60
            self.priority = 1
            self.is_eligible = True

        def get_time_constraint(self):
            return (0, 86400)

    instance.add_workorder(WorkOrderStub())

    with patch("optimise.routing.model.instance.haversine_distance_matrix") as hm:
        hm.return_value = [[0.0, 1000.0], [1000.0, 0.0]]
        instance.init_instance(datetime(2024, 1, 1, 0, 0, 0))

    assert instance.time_matrix
    assert len(instance.time_matrix) == 2
