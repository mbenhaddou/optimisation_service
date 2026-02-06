from optimise.routing.constraints.arc_cost import ArcCostConstraint
from optimise.routing.constraints.priority import PrioritySoftConstraint
from optimise.routing.constraints.time_windows import TimeWindowConstraint
from optimise.routing.input.solver_input import SolverInput
from optimise.routing.solver.ortools_builder import OrtoolsRoutingBuilder


def test_priority_constraint_sets_soft_upper_bound():
    solver_input = SolverInput(
        time_matrix=[[0, 10], [10, 0]],
        distance_matrix=[[0, 5], [5, 0]],
        time_windows=[(0, 100), (20, 80)],
        service_durations=[0, 5],
        num_vehicles=1,
        starts=[0],
        ends=[0],
        allow_slack=10,
        horizon=100,
        account_for_priority=True,
        location_priorities=[(1, 2)],
    )

    builder = OrtoolsRoutingBuilder(
        constraints=[ArcCostConstraint(), TimeWindowConstraint(), PrioritySoftConstraint()]
    )
    manager, routing, _ = builder.build(solver_input)
    time_dim = routing.GetDimensionOrDie("Time")
    idx = manager.NodeToIndex(1)

    assert time_dim.HasCumulVarSoftUpperBound(idx)
