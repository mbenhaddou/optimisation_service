from ortools.constraint_solver import pywrapcp
from math import inf
from collections import deque
import numpy as np



class NoImprovementMonitor():
    def __init__(self, routing: pywrapcp.RoutingModel, no_improvement_limit: int, fixed_point_tolerance: int=10,max_cycle_length: int=10, cycle_tolerance: int=1):
        self.routing = routing
        self.no_improvement_limit = no_improvement_limit
        self.no_improvement_steps = 0
        self.fixed_point_tolerance=fixed_point_tolerance
        self.best_solution_value = inf
        self.max_cycle_length = max_cycle_length
        self.current_fixed_point_count = 0

        self.cycle_tolerance = cycle_tolerance
        self.history = deque(maxlen=max_cycle_length * 3)  # Store enough values for 3 repetitions

    def __call__(self):
        self.update()
        self.is_cycling()
        self.is_fixed_point()
        self.reached_limit()

    def update(self):
        current_solution_value = self.routing.CostVar().Max()
        self.history.append(current_solution_value)
        if current_solution_value < self.best_solution_value:
            self.best_solution_value = current_solution_value
            self.no_improvement_steps = 0
            return
        else:
            self.no_improvement_steps += 1
        if current_solution_value == self.best_solution_value:
            self.current_fixed_point_count += 1
        else:
            self.current_fixed_point_count = 0




    def is_cycling(self):
        history_length = len(self.history)
        for cycle_length in range(2, min(self.max_cycle_length, history_length // 3) + 1):
            if self._check_cycle_for_length(cycle_length):
                print('cycle detected')
                self.routing.solver().FinishCurrentSearch()
        return False

    def _check_cycle_for_length(self, cycle_length):
        if len(self.history) < cycle_length * 3:
            return False

        # Split the history into segments and compare
        segments = [np.array(list(self.history)[i:i + cycle_length]) for i in range(0, len(self.history) - cycle_length + 1, cycle_length)]
        for i in range(len(segments) - 2):
            if self._segments_are_similar(segments[i], segments[i + 1], self.cycle_tolerance) and \
               self._segments_are_similar(segments[i + 1], segments[i + 2], self.cycle_tolerance):
                return True
        return False

    def _segments_are_similar(self, seg1, seg2, tolerance):
        return np.all(np.abs(seg1 - seg2) <= tolerance)
    def reached_limit(self):
        if self.no_improvement_steps >= self.no_improvement_limit:
            print('reached limit')
            self.routing.solver().FinishCurrentSearch()

    def is_fixed_point(self):
        if self.current_fixed_point_count >= self.fixed_point_tolerance:
            print('fixed point')
            self.routing.solver().FinishCurrentSearch()


