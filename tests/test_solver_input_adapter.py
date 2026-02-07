from dataclasses import dataclass

from optimise.routing.adapter.instance_to_solver_input import instance_to_solver_input


@dataclass
class DummyOrder:
    id: str
    workorder_penalty: int


@dataclass
class DummyWorker:
    id: str
    def get_schedule(self):
        return []


class DummyInstance:
    def __init__(self):
        self.time_matrix = [
            [0, 10, 12],
            [10, 0, 8],
            [12, 8, 0],
        ]
        self.distance_matrix = [
            [0, 5, 7],
            [5, 0, 4],
            [7, 4, 0],
        ]
        self.time_windows = [(0, 100), (0, 100), (0, 100)]
        self.service_durations = [0, 5, 5]
        self.num_vehicles = 1
        self.starts = [0]
        self.ends = [0]
        self.workers = [DummyWorker("vehicle_1")]
        self.max_working_time = 100
        self.allow_slack = 10
        self.horizon = 100
        self.distribute_load = False
        self.minimize_vehicles = True
        self.vehicle_penalty = 1234
        self.account_for_priority = False
        self.enable_neighborhood_clustering = False
        self.use_walking_distances_when_possible = False
        self.walking_distances_threshold = 200
        self.first_solution_strategy = "PATH_CHEAPEST_ARC"
        self.local_search_metaheuristic = "GREEDY_DESCENT"
        self.time_limit = 10
        self.no_improvement_limit = 50
        self.nb_depots = 1
        self.penalties = [9999]
        self.work_orders = [DummyOrder("task_a", 2000), DummyOrder("task_b", 2000)]
        self.location_priorities = []
        self.language = "en"
        self.blocked_time_tol = 15
        self.task_dependencies = [
            {"task_id": "task_a", "must_be_before": ["task_b"]}
        ]
        self.zone_restrictions = [
            {
                "task_ids": ["task_a"],
                "allowed_vehicles": ["vehicle_1"],
            }
        ]


def test_instance_to_solver_input_uses_work_order_penalties():
    instance = DummyInstance()
    solver_input = instance_to_solver_input(instance)

    assert solver_input.penalties == [2000, 2000]
    assert solver_input.num_depots == 1
    assert solver_input.vehicle_penalty == 1234
    assert solver_input.time_limit_seconds == 10
    assert solver_input.no_improvement_limit == 50
    assert solver_input.time_window_tolerance == 900
    assert solver_input.break_time_tolerance == 900
    assert solver_input.break_day_end == 86400 - 1
    assert solver_input.precedence_constraints == [(1, 2)]
    assert solver_input.allowed_vehicles_by_node == {1: [0]}
