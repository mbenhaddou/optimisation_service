
import functools
import itertools
import math

from optimise.routing.defaults import *
from optimise.utils.dates import convert_units
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
#from optimise.routing.defaults import UNITS_PER_HOUR_MODEL

import logging

logger = logging.getLogger("app")

import random
import logging


import random
import logging



from itertools import product

def get_optimizer_strategy(type="fast", history=None, deterministic=False, rng=None):
    """
    Returns a unique pair of strategies (first_solution, local_search) for an optimizer based on the given type.
    History tracks combinations of pairs used for each type.
    The selection can be deterministic if specified.

    :param type: The type of strategy to generate. Options are "fast", "optimized", or any other value for the default strategy.
    :param history: A dictionary to keep track of used pairs for each strategy type.
    :param deterministic: If True, the selection of strategies will be deterministic (predictable and repeatable).
    :return: A dictionary representing the optimizer strategy, or None if no unique pair is available.
    :rtype: dict or None
    """

    # Correcting 'best' to 'optimized'
    if type == 'best':
        type = 'optimized'

    if type not in ["fast", "optimized", "default"]:
        logging.warning(f"Unknown type '{type}'. Defaulting to 'default' strategy.")
        type = "default"

    if history is None or not history:
        history = {"fast": set(), "optimized": set(), "default": set()}

    all_combinations = {
        "optimized": set(itertools.product(OPTIMIZED_FIRST_SOLUTIONS, OPTIMIZED_METAHEURISTIC_SEARCH)),
        "fast": set(itertools.product(FAST_FIRST_SOLUTIONS, FAST_METAHEURISTIC_SEARCH)),
        "default": set(itertools.product([DEFAULT_FIRST_SOLUTION_STRATEGY], [DEFAULT_LOCAL_SEARCH_METAHEURISTIC]))
    }

    available_combinations = all_combinations[type] - history[type]

    if not available_combinations:
        history[type] = set()
        available_combinations = all_combinations[type]
        logging.info(f"All combinations for {type} exhausted. History reset.")

    if deterministic:
        chosen_combination = sorted(available_combinations)[0]
    else:
        if rng is None:
            rng = random
        chosen_combination = rng.choice(list(available_combinations))

    history[type].add(chosen_combination)

    logger.info(f"Chosen Strategies: 'first_solution_strategy': {chosen_combination[0]}, 'local_search_metaheuristic': {chosen_combination[1]}")
    return {"first_solution_strategy": chosen_combination[0], "local_search_metaheuristic": chosen_combination[1]}, history

def create_demand_evaluator(instance):
    """Creates callback to get demands at each location."""
    demands_ = instance.service_durations

    def demand_evaluator(manager, node):
        """Returns the demand of the current node."""
        return demands_[manager.IndexToNode(node)]

    return demand_evaluator

def add_capacity_constraints(routing, manager, instance):
    """Adds capacity constraint."""

    demand_evaluator_index = routing.RegisterUnaryTransitCallback(
        functools.partial(create_demand_evaluator(instance), manager))
    capacity = 'Capacity'
    routing.AddDimension(
        demand_evaluator_index,
        0,  # null capacity slack
        instance.max_working_time,
        True,  # start cumul to zero
        capacity)


def create_time_evaluator( instance):
    """Creates callback to get total times between locations."""

    time_matrix = instance.time_matrix

    if instance.use_walking_distances_when_possible:
        time_matrix = create_combined_time_matrix(instance)


    def service_time(node):
        """Gets the service time for the specified location."""
        return instance.service_durations[node]

    def travel_time( from_node, to_node):
        """Gets the travel times between two locations."""
        return time_matrix[from_node][to_node]

    total_time_ = {}
    # precompute total time to have time callback in O(1)
    for from_node in range(instance.number_of_locations):
        total_time_[from_node] = {}
        for to_node in range(instance.number_of_locations):
            if from_node == to_node:
                total_time_[from_node][to_node] = 0
            else:
                total_time_[from_node][to_node] = int(
                    service_time( from_node) +
                    travel_time(from_node, to_node))

    def time_evaluator(manager, from_node, to_node):
        """Returns the total time between the two nodes."""
        return total_time_[manager.IndexToNode(from_node)][manager.IndexToNode(
            to_node)]

    return time_evaluator





def add_node_dispersion_constraints(routing, manager, instance):
    def node_dispersion_callback( from_node, to_node):

        from_node = manager.IndexToNode(from_node)
        to_node = manager.IndexToNode(to_node)
        if from_node in instance.starts or to_node in instance.starts:
            return 0
        if instance.neighborhood_clustering_distance == "haversine":
            return int(instance.neighborhood_clustering_penalty_factor * instance.haversine_distance[from_node][to_node])

    node_dispersion_callback_index = routing.RegisterTransitCallback(node_dispersion_callback)
    routing.AddDimension(
        node_dispersion_callback_index,
        0,  # No dispersion for the depot
        int(3e9),
        True,
        'NodeDispersion'
    )
    node_dispersion_dimension = routing.GetDimensionOrDie('NodeDispersion')
    node_dispersion_dimension.SetGlobalSpanCostCoefficient(1)


def add_drivers_break_constraints(routing, manager, instance):
    # Add breaks
    time_dimension = routing.GetDimensionOrDie('Time')
    node_visit_transit = {}
    for index in range(routing.Size()):
        node = manager.IndexToNode(index)
        node_visit_transit[index] = int(instance.service_durations[node])

    breaks=[instance.workers[v].get_schedule() for v in range(len(instance.workers))]
    break_intervals = {}
    for v in range(instance.num_vehicles):
        vehicle_break = breaks[v]
        break_intervals[v] = [
            routing.solver().FixedDurationIntervalVar(
                max(0, t[0] - instance.blocked_time_tol),  # start min
                min(t[0] + instance.blocked_time_tol, convert_units(24, "hours",instance.language)-1) , # start max
                t[1],  # duration
                t[2],  # optional: no
                f'Break for vehicle {v}')
            for t in vehicle_break
        ]
        time_dimension.SetBreakIntervalsOfVehicle(break_intervals[v], v,
                                                  node_visit_transit.values())


def add_time_window_constraints(routing, manager, instance, time_evaluator_index):
    """Add time window constraints to the routing model."""
    time = 'Time'
    routing.AddDimension(
        time_evaluator_index,
        instance.allow_slack,  # allow waiting time
        instance.horizon,  # maximum time per vehicle
        False,  # don't force start cumul to zero
        time)

    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot
    for location_idx, time_window in enumerate(instance.time_windows):
        if location_idx in instance.starts or location_idx in instance.ends:
            continue

        index = manager.NodeToIndex(location_idx)
        start_time = time_window[0]
        end_time = time_window[1]
        service_time = instance.service_durations[
            location_idx]  # Assuming service_times is a list of service times for each location

        # Ensure the visit starts within the time window
        time_dimension.CumulVar(index).SetRange(start_time, end_time - service_time+convert_units(DEFAULT_TIME_TOLERANCE_MINUTES, "minutes",instance.language))
        routing.AddToAssignment(time_dimension.SlackVar(index))

    # Add time window constraints for each vehicle start node
    for vehicle_id in range(instance.num_vehicles):
        index = routing.Start(vehicle_id)
        start_time = instance.time_windows[0][0]
        end_time = instance.time_windows[0][1]
        time_dimension.CumulVar(index).SetRange(start_time, end_time)
        routing.AddToAssignment(time_dimension.SlackVar(index))

        # The time window at the end node was implicitly set in the time dimension definition to be [0, horizon].
        # Warning: Slack var is not defined for vehicle end nodes and should not be added to the assignment.



def add_time_window_constraints_(routing, manager, instance, time_evaluator_index):
    """Add Global Span constraint."""
    time = 'Time'
    routing.AddDimension(
        time_evaluator_index,
        instance.allow_slack,  # allow waiting time
        instance.horizon,  # maximum time per vehicle
        False,  # don't force start cumul to zero
        time)
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot
    # and 'copy' the slack var in the assignement object (aka Assignment) to print it
    for location_idx, time_window in enumerate(instance.time_windows):
        if location_idx in instance.starts or location_idx in instance.ends:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
    # Add time window constraints for each vehicle start node
    # and 'copy' the slack var in the assignement object (aka Assignment) to print it
    for vehicle_id in range(instance.num_vehicles):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(instance.time_windows[0][0],
                                                instance.time_windows[0][1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
        # The time window at the end node was impliclty set in the time dimension
        # definition to be [0, horizon].
        # Warning: Slack var is not defined for vehicle end nodes and should not
        # be added to the assignment.


def add_priority_soft_constraint(routing, manager, instance):
    time_dimension = routing.GetDimensionOrDie('Time')
    for location_idx, time_window in enumerate(instance.time_windows):
        if location_idx in instance.starts or location_idx in instance.ends:
            continue

        index = manager.NodeToIndex(location_idx)
        min_time=instance.time_windows[location_idx][0] + instance.service_durations[location_idx]
        priority=instance.work_orders[location_idx-instance.nb_depots].priority
        time_dimension.SetCumulVarSoftUpperBound(index, int(min_time), int(5-priority))


def calculate_workload_imbalance(routing, manager, assignment):
    """
    Calculates the workload imbalance across vehicles.
    Returns the difference between the maximum and minimum workload.
    """
    time_dimension = routing.GetDimensionOrDie('Time')
    vehicle_workloads = []
    for vehicle_id in range(routing.vehicles()):
        index = routing.Start(vehicle_id)
        workload = 0
        while not routing.IsEnd(index):
            workload += assignment.Value(time_dimension.CumulVar(index))
            index = assignment.Value(routing.NextVar(index))
        vehicle_workloads.append(workload)

    max_workload = max(vehicle_workloads)
    min_workload = min(vehicle_workloads)
    return max_workload - min_workload

def create_priority_evaluator(instance):
    """Creates callback to get priority of each location."""

    priorities_ = dict(instance.location_priorities)  # Convert list of tuples to dictionary

    def priority_evaluator(manager, node):
        """Returns the priority of the current node."""
        return priorities_.get(manager.IndexToNode(node), 0)  # Default priority is 0 if not found

    return priority_evaluator

# [START solution_printer]
def print_solution(instance, manager, routing, assignment):  # pylint:disable=too-many-locals
    """Prints assignment on console."""
    print('Objective: {}'.format(assignment.ObjectiveValue()))

    print('Breaks:')
    intervals = assignment.IntervalVarContainer()
    for i in range(intervals.Size()):
        brk = intervals.Element(i)
        if brk.PerformedValue() == 1:
            print('{}: Start({}) Duration({})'.format(brk.Var().Name(),
                                                      brk.StartValue(),
                                                      brk.DurationValue()))
        else:
            print('{}: Unperformed'.format(brk.Var().Name()))

    total_distance = 0
    total_load = 0
    total_time = 0
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    time_dimension = routing.GetDimensionOrDie('Time')
    for vehicle_id in range(instance.num_vehicles):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        distance = 0
        while not routing.IsEnd(index):
            load_var = capacity_dimension.CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            slack_var = time_dimension.SlackVar(index)
            plan_output += ' {0} Load({1}) Time({2},{3}) Slack({4},{5}) ->'.format(
                manager.IndexToNode(index), assignment.Value(load_var),
                assignment.Min(time_var), assignment.Max(time_var),
                assignment.Min(slack_var), assignment.Max(slack_var))
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            distance += routing.GetArcCostForVehicle(previous_index, index,
                                                     vehicle_id)
        load_var = capacity_dimension.CumulVar(index)
        time_var = time_dimension.CumulVar(index)
        plan_output += ' {0} Load({1}) Time({2},{3})\n'.format(
            manager.IndexToNode(index), assignment.Value(load_var),
            assignment.Min(time_var), assignment.Max(time_var))
        plan_output += 'Distance of the route: {0}m\n'.format(distance)
        plan_output += 'Load of the route: {}\n'.format(
            assignment.Value(load_var))
        plan_output += 'Time of the route: {}\n'.format(
            assignment.Value(time_var))
        print(plan_output)
        total_distance += distance
        total_load += assignment.Value(load_var)
        total_time += assignment.Value(time_var)
    print('Total Distance of all routes: {0}m'.format(total_distance))
    print('Total Load of all routes: {}'.format(total_load))
    print('Total Time of all routes: {0}min'.format(total_time))
    # [END solution_printer]


def check_initialization(variable_name):
    try:
        _ = variable_name  # Attempt to use the variable without actually doing anything with it
        return True  # If this line is reached, 'solution' is initialized
    except NameError:
        return False  # 'solution' is not initialized 'solution' has not been initialized.")



def euclidean_distance(location1, location2):
    lat1, long1 = location1
    lat2, long2 = location2
    return math.sqrt((lat1 - lat2) ** 2 + (long1 - long2) ** 2)


def create_combined_time_matrix(instance):
    """
    Creates a combined time matrix using driving and walking times.

    If the distance between two points is less than the threshold (in meters),
    it uses the haversine-based walking time; otherwise, it uses the driving time.
    The walking time is applied symmetrically if either of the distances (i->j or j->i) is below the threshold.

    Parameters:
    - instance: An object containing 'number_of_locations', 'time_matrix', and 'haversine_distance_matrix'.
    - threshold: The distance threshold (in meters) to switch between walking and driving times.

    Returns:
    - A 2D list representing the combined time matrix.
    """
    combined_time_matrix = [[0] * instance.number_of_locations for _ in range(instance.number_of_locations)]
    threshold =  instance.walking_distances_threshold
    # Loop through each pair of locations
    for from_node in range(instance.number_of_locations):
        for to_node in range(instance.number_of_locations):
            if from_node == to_node:
                combined_time_matrix[from_node][to_node] = 0
            else:

                walking_distance_from_to = instance.haversine_distance[from_node][to_node]
                walking_distance_to_from = instance.haversine_distance[to_node][from_node]

                # Assuming walking speed is 5 km/h (5000 meters per hour), convert it to time in minutes
                walking_time_from_to = convert_units((walking_distance_from_to / 5000) * 3600, "seconds")
                walking_time_to_from = convert_units((walking_distance_to_from / 5000) * 3600, "seconds")

                if walking_distance_from_to < threshold or walking_distance_to_from < threshold:
                    combined_time_matrix[from_node][to_node] = min(walking_time_from_to, walking_time_to_from)
                    combined_time_matrix[to_node][from_node] = min(walking_time_from_to, walking_time_to_from)
                else:
                    combined_time_matrix[from_node][to_node] = instance.time_matrix[from_node][to_node]
                    combined_time_matrix[to_node][from_node] = instance.time_matrix[to_node][from_node]

    return combined_time_matrix
