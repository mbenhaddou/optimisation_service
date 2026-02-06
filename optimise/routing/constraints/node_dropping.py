from typing import List

from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class NodeDroppingConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        penalties: List[int] = solver_input.penalties or []
        if not penalties:
            return

        routing = context.routing
        manager = context.manager

        num_locations = len(solver_input.time_matrix)
        num_depots = solver_input.num_depots
        if num_depots is None:
            num_depots = len(set(solver_input.starts)) if solver_input.starts else 1

        for node in range(num_locations):
            if node in solver_input.starts or node in solver_input.ends:
                continue

            order_index = node - num_depots
            if order_index < 0 or order_index >= len(penalties):
                continue

            penalty = penalties[order_index]
            routing.AddDisjunction([manager.NodeToIndex(node)], int(penalty))
