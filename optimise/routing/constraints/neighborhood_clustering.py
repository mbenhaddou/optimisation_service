from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class NeighborhoodClusteringConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.enable_neighborhood_clustering:
            return
        if solver_input.neighborhood_clustering_distance != "haversine":
            return
        if solver_input.haversine_distance is None:
            return
        try:
            if len(solver_input.haversine_distance) == 0:
                return
        except TypeError:
            pass

        routing = context.routing
        manager = context.manager
        penalty_factor = solver_input.neighborhood_clustering_penalty_factor or 1

        def node_dispersion_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            if from_node in solver_input.starts or to_node in solver_input.starts:
                return 0
            return int(
                penalty_factor * solver_input.haversine_distance[from_node][to_node]
            )

        node_dispersion_callback_index = routing.RegisterTransitCallback(
            node_dispersion_callback
        )
        routing.AddDimension(
            node_dispersion_callback_index,
            0,
            int(3e9),
            True,
            "NodeDispersion",
        )
        node_dispersion_dimension = routing.GetDimensionOrDie("NodeDispersion")
        node_dispersion_dimension.SetGlobalSpanCostCoefficient(1)
