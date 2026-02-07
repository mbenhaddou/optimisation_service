from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class ZoneRestrictionConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.allowed_vehicles_by_node:
            return

        routing = context.routing
        manager = context.manager

        for node, allowed in solver_input.allowed_vehicles_by_node.items():
            index = manager.NodeToIndex(node)
            routing.SetAllowedVehiclesForIndex(list(allowed), index)
