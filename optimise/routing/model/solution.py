from optimise.routing.model import WorkOrder
from optimise.utils.dates import convert_time_to_app_unit, format_time_as_hours_minutes
import copy

class Solution:
    def __init__(self, instance, assignement, routing_model, manager):
        self.instance = instance
        self.assignement = assignement
        self.routing_model=routing_model
        self.manager= manager
        self.scheduled=[]
        self.Errors=[]
        self.objective_value=0
        if assignement is not None:
            self.objective_value=assignement.ObjectiveValue()
        self.__dropped_nodes=[]
        self.current_date = self.instance.current_optimization_date
        if assignement is not None:
            self._init_solution()
            self.results=self._get_results()
            self.print_status()
        else:
            self.results = None

    def _init_solution(self):

        time_dimension = self.routing_model.GetDimensionOrDie('Time')

        num_workers = len(self.instance.workers)
        for worker_id in range(num_workers):
                index = self.routing_model.Start(worker_id)
                previous_index = index
                worker = self.instance.workers[worker_id]
                i = 0
                time_to_next_node = 0
                previous_node_leave_time = 0
                while not self.routing_model.IsEnd(index):

                    node_index = self.manager.IndexToNode(index)
                    if node_index < self.instance.nb_depots:
                        node = self.instance.depots[node_index]
                    else:
                        node = self.instance.work_orders[node_index - self.instance.nb_depots]

                    node.date = self.current_date.strftime(format="%Y-%m-%d")
                    travel_var = time_dimension.CumulVar(index)
                    node._visit_start_time = self.assignement.Min(travel_var)
                    node_leave_time = self.assignement.Min(travel_var)
                    slack_time = 0
                    if i == 0:
                        day_start= convert_time_to_app_unit(worker.day_starts_at)
                        if node_leave_time <= day_start:
                            node._visit_start_time = self.assignement.Min(travel_var)
                            worker.tour_start_time = format_time_as_hours_minutes(day_start)
                            worker.tour_end_time = format_time_as_hours_minutes(node_leave_time)
                            node.wait_time_minutes = 0
                        else:
                            node._visit_start_time = day_start
                            worker.tour_start_time =format_time_as_hours_minutes(day_start)
                            worker.tour_end_time = format_time_as_hours_minutes(node_leave_time)
                            node.wait_time_minutes = node_leave_time - day_start
                            slack_time = node.wait_time_minutes
                    else:
                        slack_time = max(
                            node_leave_time - previous_node_leave_time -
                            self.instance.time_matrix[self.manager.IndexToNode(previous_index)][
                                node_index] - node.work_order_duration, 0)
                        node.slack_time = slack_time

                    node.travel_distance = self.instance.distance_matrix[self.manager.IndexToNode(previous_index)][
                        node_index]
                    node.travel_time = self.instance.time_matrix[self.manager.IndexToNode(previous_index)][node_index]

                    node.step_number = i
                    worker.add_work_order(node=node, slack_time=slack_time)
                    #                time_to_next_node = self.assignement.Min(travel_var)
                    previous_index = index
                    previous_node_leave_time = node_leave_time
                    index = self.assignement.Value(self.routing_model.NextVar(index))

                    i += 1

                node_index = self.manager.IndexToNode(index)
                if node_index < self.instance.nb_depots:
                    node = self.instance.depots[node_index]
                else:
                    node = self.instance.work_orders[node_index - self.instance.nb_depots]

                node.date = self.current_date.strftime(format="%Y-%m-%d")
                travel_var = time_dimension.CumulVar(index)
                node._visit_start_time = self.assignement.Min(travel_var)
                node_leave_time = self.assignement.Min(travel_var)
                day_end = convert_time_to_app_unit(worker.day_ends_at)

                slack_time = 0
                if node_leave_time > day_end:
                    node._visit_start_time = self.assignement.Min(travel_var)
                    worker.tour_end_time = format_time_as_hours_minutes(node_leave_time)
                    worker.tour_start_time =format_time_as_hours_minutes(node_leave_time)
                    node.wait_time_minutes = 0
                else:
                    #                node._visit_start_time = day_end
                    worker.tour_end_time = format_time_as_hours_minutes(day_end)
                    worker.tour_start_time = format_time_as_hours_minutes(node_leave_time)

                    node.wait_time_minutes = day_end - node_leave_time
                    slack_time = node.wait_time_minutes

                node.travel_distance = self.instance.distance_matrix[self.manager.IndexToNode(previous_index)][
                    node_index]
                node.travel_time = self.instance.time_matrix[self.manager.IndexToNode(previous_index)][node_index]

                worker.add_work_order(node=node, slack_time=slack_time)

        self.total_tour_distance=sum(worker.total_distance for worker in self.instance.workers)
        self.total_tour_time=sum(worker.total_tour_time for worker in self.instance.workers)
        self.total_working_time=sum(worker.total_working_time for worker in self.instance.workers)
        self.total_driving_time=sum(worker.tour_driving_time for worker in self.instance.workers)


    def print_status(self):
        all_nodes_done = False
        time_dimension = self.routing_model.GetDimensionOrDie('Time')
        for vehicle_id in range(len(self.instance.workers)):
            index = self.routing_model.Start(vehicle_id)

            while not all_nodes_done:
                node = self.manager.IndexToNode(index)

                has_soft_upper_bound = time_dimension.HasCumulVarSoftUpperBound(index)
                upper_bound = time_dimension.GetCumulVarSoftUpperBound(index)

                print('node ' + str(node) + ' has soft upper bound ' + str(upper_bound))
                print('node  ' + str(node) + ' upper bound is ' + str(upper_bound))
                print(
                    'node ' + str(index) + ' cumulVar is ' + str(self.assignement.Value(time_dimension.CumulVar(index))))

                if self.routing_model.IsEnd(index):
                    all_nodes_done = True
                else:
                    index = self.assignement.Value(self.routing_model.NextVar(index))
    def set_scheduled_workorder(self):
        scheduled= [step.node.id for worker in self.instance.workers for step in worker.tour_steps if isinstance(step.node, WorkOrder)]
        for wo in self.instance._work_orders:
            if wo.id in scheduled:
                wo.is_scheduled=True

    def _get_results(self, view="by_worker"):
        results={}
        if view=="by_worker":
            results['by_worker'] = []
            for worker in self.instance.workers:
                results['by_worker'].append(worker.to_dict())
        elif view =="by_work_order":
            results['by_work_order'] = []
            for wo in self.instance.work_orders:
                if wo.assigned_worker is not None:
                    results['by_work_order'].append(wo.to_dict())
        results["summary"] = {"total_tour_distance": self.total_tour_distance, "total_tour_time": self.total_tour_time, "total_working_time": self.total_working_time, "total_driving_time": self.total_driving_time, "objective_value": self.objective_value}
        return results
    def visualize(self):
        solution_str="\n______Day: {0}__________\n".format(self.instance.current_optimization_date)

        for worker in self.instance.workers:
            solution_str+="Tour for employee: {0}:\n".format(worker.id)
            for step in worker.tour_steps:
                solution_str+="\tWO {0}: {1} - {2}\n".format(step.node.id, step.node.service_start_time, step.node.service_end_time)

        return solution_str

    def __repr__(self):
        return self.instance.name