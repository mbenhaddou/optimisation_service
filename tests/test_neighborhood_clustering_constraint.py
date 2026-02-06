from optimise.routing.constraints.arc_cost import ArcCostConstraint
from optimise.routing.constraints.neighborhood_clustering import (
    NeighborhoodClusteringConstraint,
)
from optimise.routing.input.solver_input import SolverInput
from optimise.routing.solver.ortools_builder import OrtoolsRoutingBuilder


def test_neighborhood_clustering_adds_dimension():
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
        enable_neighborhood_clustering=True,
        neighborhood_clustering_distance="haversine",
        neighborhood_clustering_penalty_factor=10,
        haversine_distance=[[0, 1], [1, 0]],
    )

    builder = OrtoolsRoutingBuilder(
        constraints=[ArcCostConstraint(), NeighborhoodClusteringConstraint()]
    )
    _, routing, _ = builder.build(solver_input)
    routing.GetDimensionOrDie("NodeDispersion")
