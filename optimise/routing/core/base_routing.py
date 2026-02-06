
from optimise.routing.core.functions import *
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optimise.routing.core.monitoring import NoImprovementMonitor
from time import time
# This module seems to be local; make sure it's available in the same package or adjust the import
import logging

logger = logging.getLogger("detailed")

def create_data_model(instance):
    """Stores the data for the problem."""
    data = {}

    # Compute locations in meters using the block dimension defined as follow
    # Manhattan average block: 750ft x 264ft -> 228m x 80m
    # here we use: 114m x 80m city block
    # src: https://nyti.ms/2GDoRIe "NY Times: Know Your distance"
    data['time_matrix'] = instance.time_matrix
    data['numlocations_'] = instance.number_of_locations
    data['time_windows'] = instance.time_windows
    data['demands'] = instance.service_durations
    data['time_per_demand_unit'] = 1
    data['vehicle_speed']=1
    data['num_vehicles'] = instance.num_vehicles
    data['breaks'] = [instance.workers[v].get_schedule() for v in range(len(instance.workers))]
    data['vehicle_capacity'] = instance.max_working_time
    data['starts'] = instance.starts
    data['ends'] = instance.ends
    data['depot'] = 0
    return data
    # [END data_model]
class RoutingOptimizer:
    """Base class for routing optimization using Google OR-Tools."""
    def __init__(self, instance, target='duration'):

        self.instance = instance

        if self.instance.starts !=[] and self.instance.ends !=[]:
            try:
                self.manager = pywrapcp.RoutingIndexManager(self.instance.number_of_locations,
                                                   self.instance.num_vehicles, self.instance.starts,
                                                   self.instance.ends)
            except Exception as e:
                raise Exception("Cannot create optimisation manager. The following exception heppened: "+str(e))

        elif self.instance.starts !=[] and self.instance.ends ==[]:

            self.manager = pywrapcp.RoutingIndexManager(self.instance.number_of_locations,
                                                   self.instance.num_vehicles, self.instance.starts)
        else:
            raise Exception("'starts' parameter not found in 'routing_params'")


        try:
            # Create Routing Model.
            self.routing = pywrapcp.RoutingModel(self.manager)
        except Exception as e:
            raise Exception("Connot create the routing model. An exception happened: "+str(e))
        primary_evaluator=None
        if target == "duration":
            # Define weight of each edge
            self.time_evaluator_index = self.routing.RegisterTransitCallback(
                functools.partial(create_time_evaluator(instance=self.instance), self.manager))
            self.routing.SetArcCostEvaluatorOfAllVehicles(self.time_evaluator_index)


        if self.instance.distribute_load:
            count_dimension_name = 'count'
            # assume some variable num_nodes holds the total number of nodes
            self.routing.AddConstantDimension(
                1,  # increment by one every time
                self.instance.number_of_locations // self.instance.num_vehicles + 1,  # max value forces equivalent # of jobs
                True,  # set count to zero
                count_dimension_name)

        elif self.instance.minimize_vehicles:
            for vehicle_id in range(self.instance.num_vehicles):
                self.routing.SetFixedCostOfVehicle(self.instance.vehicle_penalty, vehicle_id)

        if instance.enable_neighborhood_clustering:
            add_node_dispersion_constraints(self.routing, self.manager, instance)

        # Add Capacity constraint
        add_capacity_constraints(self.routing, self.manager, instance)

#        self.time_evaluator_index = self.routing.RegisterTransitCallback(
#            functools.partial(create_time_evaluator(instance=self.instance), self.manager)
#        )
        # Add Time Window constraint
        add_time_window_constraints(self.routing, self.manager, instance, self.time_evaluator_index)

        add_drivers_break_constraints(self.routing, self.manager, instance)

        if self.instance.account_for_priority:
            add_priority_soft_constraint(self.routing, self.manager, instance)


          # Number of steps without improvement
        monitor = NoImprovementMonitor( self.routing, self.instance.no_improvement_limit)
        self.routing.AddAtSolutionCallback(monitor)

    def optimize(self):
        """Entry point of the program."""
#        penalty=1000000
        for node in range(0, self.instance.number_of_locations):
            if node in self.instance.starts or node in self.instance.ends:
                continue
            penalty = int(self.instance.work_orders[node-self.instance.nb_depots].workorder_penalty)
            self.routing.AddDisjunction([self.manager.NodeToIndex(node)], penalty)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        if self.instance.first_solution_strategy is not None:
            search_parameters.first_solution_strategy = getattr(routing_enums_pb2.FirstSolutionStrategy, self.instance.first_solution_strategy)
        if self.instance.local_search_metaheuristic is not None:
            search_parameters.local_search_metaheuristic = getattr(routing_enums_pb2.LocalSearchMetaheuristic, self.instance.local_search_metaheuristic)
            search_parameters.time_limit.seconds = self.instance.time_limit



        # [END parameters]

        search_parameters.log_search = True
        try:
            start_time = time()
            assignment = self.routing.SolveWithParameters(search_parameters)
            end_time = time()
            execution_time = end_time - start_time

        except Exception as e:
            print(e)
        # [END solve]

        # Print assignement on console.
        # [START print_solution]
        if assignment:
            # logging.info("Total distance of the route: %d", assignment.ObjectiveValue())
            # logging.info("Number of vehicles used: %d", assignment.Value(self.routing.NumVehicles()))
            # logging.info(f"Execution Time: {execution_time:.4f} seconds")
            # logging.info(f"nb of workers:  %d",{len(self.instance.workers)})
            # logging.info(f"first_solution_strategy:  %s",{len(self.instance.first_solution_strategy)})
            # logging.info(f"local_search_metaheuristic:  %s",{len(self.instance.local_search_metaheuristic)})

            log_message = f"{assignment.ObjectiveValue()},{self.instance.num_vehicles},{execution_time:.4f},{len(self.instance.workers)},{self.instance.first_solution_strategy},{self.instance.local_search_metaheuristic}"
            logger.info(log_message)
            print_solution(self.instance, self.manager, self.routing, assignment)
            return assignment
        else:
            print('No assignement found!')
        # [END print_solution]






