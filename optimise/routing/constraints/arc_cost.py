from typing import List

from optimise.routing.constraints.base import ConstraintContext, RoutingConstraint
from optimise.routing.defaults import ROUTING_TIME_RESOLUTION
from optimise.utils.dates import convert_units


def _combine_time_matrix(
    time_matrix: List[List[int]],
    haversine_distance: List[List[float]],
    threshold: int,
) -> List[List[int]]:
    size = len(time_matrix)
    combined = [[0] * size for _ in range(size)]

    for from_node in range(size):
        for to_node in range(size):
            if from_node == to_node:
                combined[from_node][to_node] = 0
                continue

            walking_distance_from_to = haversine_distance[from_node][to_node]
            walking_distance_to_from = haversine_distance[to_node][from_node]

            # Walking speed: 5 km/h -> 5000 meters/hour
            walking_time_from_to = convert_units(
                (walking_distance_from_to / 5000) * 3600,
                "seconds",
                "en",
                ROUTING_TIME_RESOLUTION,
            )
            walking_time_to_from = convert_units(
                (walking_distance_to_from / 5000) * 3600,
                "seconds",
                "en",
                ROUTING_TIME_RESOLUTION,
            )

            if walking_distance_from_to < threshold or walking_distance_to_from < threshold:
                combined[from_node][to_node] = min(
                    walking_time_from_to, walking_time_to_from
                )
                combined[to_node][from_node] = min(
                    walking_time_from_to, walking_time_to_from
                )
            else:
                combined[from_node][to_node] = time_matrix[from_node][to_node]
                combined[to_node][from_node] = time_matrix[to_node][from_node]

    return combined


class ArcCostConstraint(RoutingConstraint):
    def apply(self, context: ConstraintContext) -> None:
        solver_input = context.solver_input
        manager = context.manager
        routing = context.routing

        time_matrix = solver_input.time_matrix
        cost_matrix = time_matrix
        if solver_input.objective == "distance":
            cost_matrix = solver_input.distance_matrix
        has_haversine = solver_input.haversine_distance is not None
        if has_haversine:
            try:
                has_haversine = len(solver_input.haversine_distance) > 0
            except TypeError:
                has_haversine = True

        if (
            solver_input.use_walking_distances_when_possible
            and has_haversine
            and solver_input.walking_distances_threshold
        ):
            time_matrix = _combine_time_matrix(
                time_matrix,
                solver_input.haversine_distance,
                int(solver_input.walking_distances_threshold),
            )

        def time_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            base = cost_matrix[from_node][to_node]
            if solver_input.objective != "distance":
                base += solver_input.service_durations[from_node]
            return int(base)

        transit_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_index)
        context.transit_callback_index = transit_index
