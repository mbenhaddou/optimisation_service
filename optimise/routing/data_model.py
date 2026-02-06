
from copy import deepcopy

from optimise.routing.model import Instance, WorkOrder, Worker


fields_to_remove={}
fields_to_remove["orders"]=["earliest_start_datetime", "latest_end_datetime", "earliest_machine_availability_datetime", "latest_machine_availability_datetime", "earliest_datetime", "latest_datetime"]

from typing import List, Dict, Any
from copy import deepcopy
from optimise.routing.model import Instance, WorkOrder, Worker
from optimise.routing.constants import translate



def validate_request_fields(request: Dict[str, Any]):
    required_fields = ['orders', 'workers', 'depot', 'period_start', 'orders_skills']
    for field in required_fields:
        if field not in request:
            raise ValueError(translate("missing_required_field", request.get('language')).format(field))


def get_optimisation_instances(original_request: Dict[str, Any]) -> List[Instance]:
    request = deepcopy(original_request)
    try:
        validate_request_fields(request)  # This function validates that all required fields are in the request
        instances = []

        for skill in request['orders_skills']:
            instance = Instance.from_dict({'name': skill, **request})
            add_orders_to_instance(instance, request['orders'], skill, request)
            add_workers_to_instance(instance, request['workers'], skill, request)

            instances.append(instance)

        return instances
    except Exception as e:
        raise ValueError(translate("failed_to_create_optimization_instances", request.get('language')).format(e))

def add_orders_to_instance(instance: Instance, orders: List[Dict[str, Any]], skill: str, request: Dict[str, Any]):
    for order in orders:
        if order['skill'] == skill:
            try:
                order['date_format'] = request["date_format"]
                work_order = WorkOrder.from_dict(order)
                instance.add_workorder(work_order)
            except Exception as e:
                raise ValueError(translate("failed_to_add_order_to_instance", request.get('language')).format(order['id'], e))

def add_workers_to_instance(instance: Instance, workers: List[Dict[str, Any]], skill: str, request: Dict[str, Any]):
    for worker in workers:
        if skill in worker['skills']:
            try:
                w = Worker.from_dict(worker, request)
                instance.add_worker(w)
            except Exception as e:
                raise ValueError(translate("failed_to_add_worker_to_instance", request.get('language')).format(worker['e_id'], e))
