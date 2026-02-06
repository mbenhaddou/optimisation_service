from dataclasses import dataclass

from optimise.routing.adapter.instance_to_solver_input import instance_to_solver_input


@dataclass
class DummyOrder:
    workorder_penalty: int


class DummyInstance:
    def __init__(self):
        self.time_matrix = [[0, 10], [10, 0]]
        self.distance_matrix = [[0, 5], [5, 0]]
        self.time_windows = [(0, 100), (0, 100)]
        self.service_durations = [0, 5]
        self.num_vehicles = 1
        self.starts = [0]
        self.ends = [0]
        self.workers = []
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
        self.work_orders = [DummyOrder(2000)]
        self.location_priorities = []
        self.language = "en"
        self.blocked_time_tol = 15


def test_instance_to_solver_input_uses_work_order_penalties():
    instance = DummyInstance()
    solver_input = instance_to_solver_input(instance)

    assert solver_input.penalties == [2000]
    assert solver_input.num_depots == 1
    assert solver_input.vehicle_penalty == 1234
    assert solver_input.time_limit_seconds == 10
    assert solver_input.no_improvement_limit == 50
    assert solver_input.time_window_tolerance == 900
    assert solver_input.break_time_tolerance == 900
    assert solver_input.break_day_end == 86400 - 1
