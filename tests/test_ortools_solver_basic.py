from optimise.routing.input.solver_input import SolverInput
from optimise.routing.solver.ortools_builder import OrtoolsSolver


def test_ortools_solver_basic_route():
    solver_input = SolverInput(
        time_matrix=[[0, 10], [10, 0]],
        distance_matrix=[[0, 5], [5, 0]],
        time_windows=[(0, 100), (0, 100)],
        service_durations=[0, 5],
        num_vehicles=1,
        starts=[0],
        ends=[0],
        max_working_time=100,
        allow_slack=10,
        horizon=100,
        penalties=[1000],
        num_depots=1,
        time_limit_seconds=1,
        first_solution_strategy="PATH_CHEAPEST_ARC",
        local_search_metaheuristic="GREEDY_DESCENT",
    )

    solver = OrtoolsSolver()
    assignment, routing, manager = solver.solve(solver_input)
    assert assignment is not None
    assert routing is not None
    assert manager is not None
