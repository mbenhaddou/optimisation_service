from dataclasses import dataclass, field
from typing import Dict, Optional

from ortools.constraint_solver import pywrapcp

from optimise.routing.input.solver_input import SolverInput


@dataclass
class ConstraintContext:
    manager: pywrapcp.RoutingIndexManager
    routing: pywrapcp.RoutingModel
    solver_input: SolverInput
    transit_callback_index: Optional[int] = None
    dimensions: Dict[str, pywrapcp.RoutingDimension] = field(default_factory=dict)


class RoutingConstraint:
    def apply(self, context: ConstraintContext) -> None:
        raise NotImplementedError
