from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class VehicleCostConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if solver_input.distribute_load:
            return
        if not solver_input.minimize_vehicles:
            return
        if not solver_input.vehicle_penalty:
            return

        routing = context.routing
        for vehicle_id in range(solver_input.num_vehicles):
            routing.SetFixedCostOfVehicle(int(solver_input.vehicle_penalty), vehicle_id)
