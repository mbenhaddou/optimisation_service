from typing import Iterable, Optional, Tuple

from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from optimise.routing.config.solve_profile import SolveProfile
from optimise.routing.constraints import (
    ArcCostConstraint,
    BreaksConstraint,
    CapacityConstraint,
    ConstraintContext,
    LoadDistributionConstraint,
    NeighborhoodClusteringConstraint,
    NodeDroppingConstraint,
    PrioritySoftConstraint,
    RoutingConstraint,
    TimeWindowConstraint,
    VehicleCostConstraint,
)
from optimise.routing.core.monitoring import NoImprovementMonitor
from optimise.routing.input.solver_input import SolverInput

DEFAULT_CONSTRAINTS = (
    ArcCostConstraint(),
    LoadDistributionConstraint(),
    VehicleCostConstraint(),
    NeighborhoodClusteringConstraint(),
    CapacityConstraint(),
    TimeWindowConstraint(),
    BreaksConstraint(),
    PrioritySoftConstraint(),
    NodeDroppingConstraint(),
)


class OrtoolsRoutingBuilder:
    """
    Build a routing model and apply a configurable list of constraints.
    """

    def __init__(self, constraints: Optional[Iterable[RoutingConstraint]] = None) -> None:
        self.constraints = list(constraints) if constraints is not None else list(DEFAULT_CONSTRAINTS)

    def build(
        self, solver_input: SolverInput
    ) -> Tuple[pywrapcp.RoutingIndexManager, pywrapcp.RoutingModel, ConstraintContext]:
        if solver_input.starts and solver_input.ends:
            manager = pywrapcp.RoutingIndexManager(
                len(solver_input.time_matrix),
                solver_input.num_vehicles,
                solver_input.starts,
                solver_input.ends,
            )
        elif solver_input.starts:
            manager = pywrapcp.RoutingIndexManager(
                len(solver_input.time_matrix),
                solver_input.num_vehicles,
                solver_input.starts,
            )
        else:
            raise ValueError("SolverInput must define starts (and optionally ends).")

        routing = pywrapcp.RoutingModel(manager)
        context = ConstraintContext(manager=manager, routing=routing, solver_input=solver_input)

        for constraint in self.constraints:
            constraint.apply(context)

        return manager, routing, context


class OrtoolsSolver:
    """
    Execution layer for OR-Tools with pluggable constraint sets.
    """

    def __init__(self, constraints: Optional[Iterable[RoutingConstraint]] = None) -> None:
        self.builder = OrtoolsRoutingBuilder(constraints=constraints)

    def solve(
        self,
        solver_input: SolverInput,
        profile: Optional[SolveProfile] = None,
    ):
        manager, routing, _context = self.builder.build(solver_input)

        if solver_input.no_improvement_limit is not None:
            monitor = NoImprovementMonitor(routing, solver_input.no_improvement_limit)
            routing.AddAtSolutionCallback(monitor)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        if profile:
            if profile.first_solution_strategy:
                search_parameters.first_solution_strategy = getattr(
                    routing_enums_pb2.FirstSolutionStrategy,
                    profile.first_solution_strategy,
                )
            if profile.local_search_metaheuristic:
                search_parameters.local_search_metaheuristic = getattr(
                    routing_enums_pb2.LocalSearchMetaheuristic,
                    profile.local_search_metaheuristic,
                )
            if profile.time_limit_seconds is not None:
                search_parameters.time_limit.seconds = int(profile.time_limit_seconds)
            if profile.search_workers is not None and profile.search_workers > 0:
                search_parameters.num_search_workers = int(profile.search_workers)
            if profile.solution_limit is not None:
                search_parameters.solution_limit = int(profile.solution_limit)
            search_parameters.log_search = profile.log_search

        assignment = routing.SolveWithParameters(search_parameters)
        return assignment, routing, manager
