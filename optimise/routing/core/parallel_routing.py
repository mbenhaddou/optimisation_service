from optimise.routing.core.base_routing import RoutingOptimizer
from ortools.constraint_solver import pywrapcp
import logging
import os
import math
from datetime import timedelta
from solution_routing.solution_routing_CRUD import solution_routing_crud
from optimise.routing.model.solution import Solution
from optimise.routing.constants import translate
from solution_routing.solution_routing_model import SolutionRouting
from optimise.routing.defaults import NUM_RUNS_FOR_BEST_RESULT_TYPE, MAX_NUM_WORKERS
logger = logging.getLogger("app")
import concurrent.futures

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import copy

class ParallelRoutingOptimizer:
    def __init__(self, base_instances, solution_routing: SolutionRouting, num_runs=1):

        self.instances = copy.deepcopy(base_instances)

        self.num_runs = num_runs
        if len(base_instances)>0:
            if base_instances[0].result_type == "best":
                self.num_runs = NUM_RUNS_FOR_BEST_RESULT_TYPE

        self.solution_routing = solution_routing



    def _multi_day_routing_optimize(self, instance):
        logger.info("optimising instance: " + str(instance))
        self.solution_routing.status_msg = translate("optimizing_for_skill",instance.language).format(str(instance))
        solution_routing_crud.update(self.solution_routing)

        horizon = instance.optimization_horizon
        day_start = instance.period_start
        day_i = 0
        solutions = []
        while day_i < horizon:
            day = day_start + timedelta(days=day_i)

            logger.info('Day: {0} - Instance: {1}'.format(day, instance.name))

            instance.init_instance(day)

            if not instance.can_schedule_new_orders:
                solution = Solution(instance, None,None,None)
                solutions.append(solution)
                day_i += 1
                continue
            try:
                optimizer = RoutingOptimizer(instance)
                assignement = optimizer.optimize()
                if assignement is not None:
                    solution = Solution(instance, assignement, optimizer.routing, optimizer.manager)
                    solutions.append(solution)
                    solution.set_scheduled_workorder()
                    logger.info(instance.work_orders)
                else:
                    solutions.append(Solution(instance, None,None,None))
            except NameError as e:
                pass
            except Exception as e:
                print(e)
            day_i += 1


        logger.info("optimising instance: " + str(instance) + ".....OK")
        return self.post_process_solution(solutions)  # return solutions
    def post_process_solution(self, solution_list):
        results_str = {}
        resutls_jsn = {"details":{}}
        dropped_tours = []


        if solution_list is None:
            return {}
        instance = None
        for solution in solution_list:
            instance = solution.instance
            day = solution.current_date
            if str(day.date()) not in results_str:
                results_str[str(day.date())] = []
                resutls_jsn["details"][str(day.date())] = {}
                resutls_jsn["details"][str(day.date())]['by_worker'] = []
                resutls_jsn["details"][str(day.date())]['summaries']= []
                resutls_jsn["details"][str(day.date())]['strings']= []
                resutls_jsn["details"][str(day.date())]['objective_value'] = 0
            res = solution.results
            if res is not None:
                resutls_jsn["details"][str(day.date())]['by_worker'].extend(copy.deepcopy(res['by_worker']))
                resutls_jsn["details"][str(day.date())]['summaries'].append(copy.deepcopy(res['summary']))
                resutls_jsn["details"][str(day.date())]['strings'].append(solution.visualize())
                logger.info(solution.visualize())
                #            assignement.set_scheduled_workorder()
                logger.info(instance.work_orders)
                resutls_jsn["details"][str(day.date())]['objective_value'] = solution.objective_value
        if instance is None:
            return resutls_jsn
        dropped = instance.get_dropped_nodes()
        for d in dropped:
            message = d.validate_optimization_period(solution_list[0].instance.period_start,
                                                         solution_list[0].instance.period_start + timedelta(
                                                             days=solution_list[0].instance.optimization_horizon))
            if not d.has_been_scheduled:
                d.reason_for_not_scheduling = translate("OUTSIDE_OPTIMISATION_PERIOD",instance.language)
            elif d.errors:
                d.reason_for_not_scheduling = ' | '.join(d.errors)
            elif message:
                d.reason_for_not_scheduling = message
            elif d.errors:
                d.reason_for_not_scheduling = '\n'.join(d.errors)
            else:
                d.reason_for_not_scheduling = translate("WAS_SCHEDULED_BUT_DROPPED",instance.language)

        dropped_tours.extend([d.to_dict() for d in dropped])

        logger.info("optimising instance: " + str(instance) + ".....OK")

        resutls_jsn['dropped'] = dropped_tours
        return resutls_jsn

    def parallel_optimize(self, single_instance=True):
        best_solutions = [None] * len(self.instances)
        best_costs = [float('inf')] * len(self.instances)

        max_workers = min(max(len(self.instances) * self.num_runs, 1), MAX_NUM_WORKERS)
        # Use ThreadPoolExecutor if in a test environment, otherwise ProcessPoolExecutor
        executor_class = ThreadPoolExecutor if os.getenv('TEST_ENVIRONMENT') else ProcessPoolExecutor

        with executor_class(max_workers=max_workers) as executor:
            futures = {}
            for idx, instance in enumerate(self.instances):
                for run in range(self.num_runs):
                    if run==0 and instance.result_type=="best":
                        instance.update_strategies(result_type="fast")
                    else:
                        instance.update_strategies()
                    # Ensure the instance is pickleable for ProcessPoolExecutor
                    future = executor.submit(self._multi_day_routing_optimize, copy.deepcopy(instance))
                    futures[future] = idx  # Map each future to its instance index


            # Wait for all futures to complete
            concurrent.futures.wait(futures)
            results=[]
            try:
                results = [(future.result(),futures[future]) for future in futures]
            except Exception as exc:
                import traceback

                logger.error(f'An error occurred: {traceback.format_exc()}')

            for result, idx in results:
                if result and 'details' in result:
                    self._compute_performance(result)
            for result, idx in results:
                if result and 'details' in result and result['details']:
                    overall_cost = sum([r['objective_value'] for r in result['details'].values()])
                    if overall_cost < best_costs[idx]:
                        best_solutions[idx] = result
                        best_costs[idx] = overall_cost
        return best_solutions

    def _compute_performance(self, json_data):
        total_sums = {}

        # Extract the summaries from all dates and sum their numerical fields
        for date in json_data['details']:
            if 'summaries' in json_data['details'][date]:
                summaries = json_data['details'][date]['summaries']
                for summary in summaries:
                    for key, value in summary.items():
                        if isinstance(value, (int, float)):  # Check if the value is numerical
                            if key not in total_sums:
                                total_sums[key] = 0
                            total_sums[key] += value
        json_data["performance"] = total_sums

        return json_data
