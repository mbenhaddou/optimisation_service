from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint


class TimeWindowConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        if not solver_input.time_windows:
            return

        routing = context.routing
        manager = context.manager

        transit_index = context.transit_callback_index
        if transit_index is None:
            def time_callback(from_index: int, to_index: int) -> int:
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int(
                    solver_input.service_durations[from_node]
                    + solver_input.time_matrix[from_node][to_node]
                )

            transit_index = routing.RegisterTransitCallback(time_callback)
            context.transit_callback_index = transit_index

        routing.AddDimension(
            transit_index,
            int(solver_input.allow_slack),
            int(solver_input.horizon),
            False,
            "Time",
        )

        time_dimension = routing.GetDimensionOrDie("Time")
        context.dimensions["Time"] = time_dimension

        for location_idx, window in enumerate(solver_input.time_windows):
            if location_idx in solver_input.starts or location_idx in solver_input.ends:
                continue

            index = manager.NodeToIndex(location_idx)
            start_time = window[0]
            end_time = window[1]
            service_time = (
                solver_input.service_durations[location_idx]
                if location_idx < len(solver_input.service_durations)
                else 0
            )
            end_with_tolerance = end_time - service_time + int(
                solver_input.time_window_tolerance
            )
            time_dimension.CumulVar(index).SetRange(start_time, end_with_tolerance)
            routing.AddToAssignment(time_dimension.SlackVar(index))

        for vehicle_id in range(solver_input.num_vehicles):
            start_node = (
                solver_input.starts[vehicle_id]
                if vehicle_id < len(solver_input.starts)
                else 0
            )
            if start_node < len(solver_input.time_windows):
                start_time, end_time = solver_input.time_windows[start_node]
            else:
                start_time, end_time = solver_input.time_windows[0]
            index = routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(start_time, end_time)
            routing.AddToAssignment(time_dimension.SlackVar(index))
