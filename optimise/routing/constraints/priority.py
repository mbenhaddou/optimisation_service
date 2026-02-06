from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class PrioritySoftConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.account_for_priority:
            return
        if not solver_input.location_priorities:
            return

        routing = context.routing
        manager = context.manager

        if "Time" not in context.dimensions:
            try:
                time_dimension = routing.GetDimensionOrDie("Time")
            except Exception:
                return
        else:
            time_dimension = context.dimensions["Time"]

        priorities = dict(solver_input.location_priorities)

        for location_idx, _ in enumerate(solver_input.time_windows):
            if location_idx in solver_input.starts or location_idx in solver_input.ends:
                continue

            if location_idx not in priorities:
                continue

            index = manager.NodeToIndex(location_idx)
            min_time = (
                solver_input.time_windows[location_idx][0]
                + solver_input.service_durations[location_idx]
            )
            priority = priorities[location_idx]
            time_dimension.SetCumulVarSoftUpperBound(
                index,
                int(min_time),
                int(5 - priority),
            )
