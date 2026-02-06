from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class BreaksConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.breaks:
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

        node_visit_transit = {}
        for index in range(routing.Size()):
            node = manager.IndexToNode(index)
            node_visit_transit[index] = int(solver_input.service_durations[node])

        break_day_end = (
            int(solver_input.break_day_end)
            if solver_input.break_day_end is not None
            else int(solver_input.horizon)
        )
        tolerance = int(solver_input.break_time_tolerance)

        for v in range(solver_input.num_vehicles):
            if v >= len(solver_input.breaks):
                continue
            vehicle_breaks = solver_input.breaks[v]
            break_intervals = []
            for t in vehicle_breaks:
                start = t[0]
                duration = t[1] if len(t) > 1 else 0
                optional = t[2] if len(t) > 2 else True
                break_intervals.append(
                    routing.solver().FixedDurationIntervalVar(
                        max(0, start - tolerance),
                        min(start + tolerance, break_day_end),
                        duration,
                        optional,
                        f"Break for vehicle {v}",
                    )
                )
            time_dimension.SetBreakIntervalsOfVehicle(
                break_intervals, v, node_visit_transit.values()
            )
