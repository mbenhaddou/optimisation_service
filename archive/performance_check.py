import json
from optimise.api import get_optimal_routes, get_schedule, get_schedule_str
from optimise.api import get_schedule_str, get_schedule
from solution_routing.solution_routing_model import SolutionRouting
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import time

def main():
    _1000_order_file = "tests/optimise/data/1000_orders.json"
    with open(_1000_order_file) as f:
        data = f.read()
        data = json.loads(data)
        data['result_type'] = 'fast'

        solution_routing=SolutionRouting()
        solution_routing.optimization_request = json.dumps(data)
        start_time = time.time()
        solutions = get_optimal_routes(solution_routing)

        end_time = time.time()
        execution_time = end_time - start_time
        print('execution_time', execution_time)


if __name__ == '__main__':
    main()






