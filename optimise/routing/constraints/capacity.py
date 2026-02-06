from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class CapacityConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.max_working_time:
            return

        manager = context.manager
        routing = context.routing

        def demand_callback(index: int) -> int:
            node = manager.IndexToNode(index)
            return solver_input.service_durations[node]

        demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimension(
            demand_index,
            0,
            int(solver_input.max_working_time),
            True,
            "Capacity",
        )
