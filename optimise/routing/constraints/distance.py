from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class DistanceConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.max_route_distance:
            return

        routing = context.routing
        manager = context.manager

        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(solver_input.distance_matrix[from_node][to_node])

        distance_index = routing.RegisterTransitCallback(distance_callback)
        routing.AddDimension(
            distance_index,
            0,
            int(solver_input.max_route_distance),
            True,
            "Distance",
        )
