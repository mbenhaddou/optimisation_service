from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class PrecedenceConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.precedence_constraints:
            return

        routing = context.routing
        manager = context.manager
        time_dimension = context.dimensions.get("Time")
        if time_dimension is None:
            return

        for before_node, after_node in solver_input.precedence_constraints:
            before_index = manager.NodeToIndex(before_node)
            after_index = manager.NodeToIndex(after_node)
            routing.solver().Add(
                routing.VehicleVar(before_index) == routing.VehicleVar(after_index)
            )
            routing.solver().Add(
                time_dimension.CumulVar(before_index)
                <= time_dimension.CumulVar(after_index)
            )
