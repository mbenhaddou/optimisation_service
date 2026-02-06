import copy
import json
from optimise.routing.model.solution import Solution
from optimise.routing.preprocessing import preprocess_request as routing_preprocess_request
from optimise.routing.core.base_routing import RoutingOptimizer as Optimizer
from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.constants import translate
from datetime import timedelta
from optimise.routing.core.parallel_routing import ParallelRoutingOptimizer
from optimise.routing.defaults import USE_NEW_SOLVER
import logging
import backoff

from solution_routing.solution_routing_CRUD import solution_routing_crud
from solution_routing.solution_routing_model import SolutionRouting

logger = logging.getLogger("app")

def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        if value.lower() in ("1", "true", "yes", "y", "on"):
            return True
        if value.lower() in ("0", "false", "no", "n", "off"):
            return False
    return None


def _resolve_use_new_solver(solution_routing: SolutionRouting) -> bool:
    use_new_solver = None
    request_payload = {}
    try:
        if isinstance(solution_routing.optimization_request, str):
            request_payload = json.loads(solution_routing.optimization_request)
        elif isinstance(solution_routing.optimization_request, dict):
            request_payload = solution_routing.optimization_request
    except Exception:
        request_payload = {}

    if isinstance(request_payload, dict):
        use_new_solver = _coerce_bool(request_payload.get("use_new_solver"))
        if use_new_solver is None:
            parameters = request_payload.get("parameters")
            if isinstance(parameters, dict):
                use_new_solver = _coerce_bool(parameters.get("use_new_solver"))

    if use_new_solver is None and solution_routing.parameters:
        try:
            parameters_payload = (
                json.loads(solution_routing.parameters)
                if isinstance(solution_routing.parameters, str)
                else solution_routing.parameters
            )
            if isinstance(parameters_payload, dict):
                use_new_solver = _coerce_bool(parameters_payload.get("use_new_solver"))
        except Exception:
            pass

    if use_new_solver is None:
        use_new_solver = USE_NEW_SOLVER

    return bool(use_new_solver)

def get_optimization_instances(solution_routing: SolutionRouting):
    json_request=json.loads(solution_routing.optimization_request)
    errors=[]
    logger.info("getting request..... OK")

    solution_routing.status_msg = translate("preprocessing_request", json_request.get("language"))

    solution_routing_crud.update(solution_routing)
    request = routing_preprocess_request(json_request, errors)
    logger.info("preprocessing request.....OK")

    return get_optimisation_instances(request), errors

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def get_optimal_routes(solution_routing: SolutionRouting):

    instances, errors=get_optimization_instances(solution_routing)
    logger.info("getting instances.....OK")

    results_json = {}


    instance_errors=check_errors(instances)

    if len(instance_errors)>0:
        results_json["errors"]=instance_errors
        logger.error(instance_errors)
        return results_json

    try:
        logger.info("starting optimisation")
        use_new_solver = _resolve_use_new_solver(solution_routing)
        logger.info("solver path: %s", "new" if use_new_solver else "legacy")

        if use_new_solver:
            from optimise.routing.solver.ortools_runner import solve_instances
            solutions = solve_instances(instances, solution_routing)
        else:
            parallel_optimizer=ParallelRoutingOptimizer(instances, solution_routing)
            solutions=parallel_optimizer.parallel_optimize()

        results_json=post_process_solutions(solutions)
        results_json['errors']= errors

    except Exception as e:
        results_json["errors"]=str(e)
        logger.info(e)
        raise e
#    logger.info(results_json)

    for day in results_json['message'].keys():
        results_json['message'][day]='\n'.join(results_json['message'][day])

    return results_json




def _multi_day_routing_optimize(instance, solution_routing, results_str={}, resutls_jsn={}, dropped_tours=[]):
    logger.info("optimising instance: " + str(instance))
    solution_routing.status_msg = translate("optimizing_for_skill", instance.language).format(str(instance))
    solution_routing_crud.update(solution_routing)

    horizon=instance.optimization_horizon
    day_start=instance.period_start
    day_i=0
    solutions=[]
    while day_i<horizon:
        day=day_start+timedelta(days=day_i)

        if str(day.date()) not in results_str:
            results_str[str(day.date())]=[]
            resutls_jsn[str(day.date())]=[]

        logger.info('Day: {0} - Instance: {1}'.format(day, instance.name))

        instance.init_instance(day)

        if not instance.can_schedule_new_orders:
            day_i += 1

            continue
        try:
            optimizer=Optimizer(instance)
            assignement=optimizer.optimize()
            if assignement is not None:
                solution=Solution(instance, assignement, optimizer.routing, optimizer.manager)
                solutions.append(solution)
                res=solution.get_results()
                resutls_jsn[str(day.date())].extend(copy.deepcopy(res['by_worker']))
                results_str[str(day.date())].append(solution.visualize())
                logger.info(solution.visualize())
                solution.set_scheduled_workorder()
                logger.info(instance.work_orders)
        except Exception as e:
            logger.error(e)
        day_i += 1

    dropped=instance.get_dropped_nodes()
    for d in dropped:
        message=d.validate_optimization_period(day_start, day_start+timedelta(days=horizon))
        if not d.has_been_scheduled:
            d.reason_for_not_scheduling=translate("OUTSIDE_OPTIMISATION_PERIOD",instance.language)
        elif message:
            d.reason_for_not_scheduling=message
        elif d.errors:
            d.reason_for_not_scheduling = '\n'.join(d.errors)
        else:
            d.reason_for_not_scheduling=translate("WAS_SCHEDULED_BUT_DROPPED",instance.language)

    dropped_tours.extend([d.to_dict() for d in dropped])

    logger.info("optimising instance: " + str(instance) + ".....OK")

    return solutions

def post_process_solutions(solutions):
    results_str = {}
    resutls_jsn = {}
    dropped_tours = []

    for solution_list in solutions:
        if solution_list is None:
            continue
        instance=None
        for day, solution in solution_list['details'].items():
            if day not in results_str:
                results_str[day]=[]
                resutls_jsn[day]=[]

            res=solution['by_worker']
            if res is not None:
                resutls_jsn[day].extend(copy.deepcopy(res))
                results_str[day].extend(solution['strings'])

    #            logger.info(solution.visualize())
    #            assignement.set_scheduled_workorder()
    #            logger.info(instance.work_orders)

        dropped_tours.extend(solution_list['dropped'])

    #    logger.info("optimising instance: " + str(instance) + ".....OK")

    resutls_jsn['message'] = results_str
    resutls_jsn['dropped'] = dropped_tours
    performances=[s['performance'] for s in solutions]
    resutls_jsn['performance'] = {key: sum(d.get(key, 0) for d in performances) for key in set().union(*performances)}
    return resutls_jsn

def check_errors(instances):

    errors=[]
    for instance in instances:
        for error in instance.errors:
            if error not in errors:
                errors.append(error)
#        errors.extend(instance.check_for_errors())

    return errors
