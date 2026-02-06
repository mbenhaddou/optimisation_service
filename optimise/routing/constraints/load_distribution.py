from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class LoadDistributionConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.distribute_load:
            return

        routing = context.routing
        num_nodes = len(solver_input.time_matrix)
        num_vehicles = max(solver_input.num_vehicles, 1)

        routing.AddConstantDimension(
            1,
            num_nodes // num_vehicles + 1,
            True,
            "count",
        )
