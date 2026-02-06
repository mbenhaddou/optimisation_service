import sys
import json
from unittest.mock import Mock, patch
import time

from optimise.routing.constants import *
from optimise.routing.defaults import *
sys.path.append('../scheduling_optimization/')
from optimise.api import get_optimal_routes, get_optimization_instances
from solution_routing.solution_routing_model import SolutionRouting
import os
from optimise.routing.constants import translate

dirname = os.path.dirname(__file__)
import unittest

os.environ['TEST_ENVIRONMENT'] = 'True'
class TestRoutingSolver(unittest.TestCase):
    def setUp(self):
        self.db_session = Mock()
        self.solution_routing = self.solution_routing = SolutionRouting()#Mock()

    @patch('optimise.api.solution_routing_crud.update')
    def test_routing_priority(self, mock_update):
        with open(os.path.join(dirname, 'data/skills/request_test_priority.json'), encoding="utf-8") as f:
            data = f.read()
        self.solution_routing.optimization_request = data
        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        # check that first scheduled id priority is 1
        self.assertEqual(sol['2023-01-10'][0]['tour_steps'][1]['node']['id'], 'Priority_1')
        # check that last scheduled id priority is 5
        self.assertEqual(sol['2023-01-10'][0]['tour_steps'][-2]['node']['id'], 'Priority_5')
        #    change priority order_or_worker
        data = json.loads(data)
        data['orders'][0]['priority'] = 1
        data['orders'][3]['priority'] = 5

        # TODO this gives an error because deepcopy(data) transforms the date_string to datetime
        # self.solution_routing.optimization_request = deepcopy(data)
        # sol = get_optimal_routes(self.db_session, self.solution_routing)
        #
        # #check that first scheduled id priority is 1
        # self.assertEqual(sol['2023-01-10'][0]['tour_steps'][2]['node']['id'],'Priority_5')
        # #check that last scheduled id priority is 5
        # self.assertEqual(sol['2023-01-10'][0]['tour_steps'][-2]['node']['id'],'Priority_1')


    @patch('optimise.api.solution_routing_crud.update')
    def test_must_start_not_scheduled(self, mock_update):
        with open(os.path.join(dirname, 'data/constraints/order_must_start_not_scheduled.json'), encoding="utf-8") as f:
            data = f.read()

        self.solution_routing.optimization_request = data
        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        print(sol)

    @patch('optimise.api.solution_routing_crud.update')
    def test_routing_dispersion(self, mock_update):
        with open(os.path.join(dirname, 'data/clustered/clustered_orders_test.json'), encoding="utf-8") as f:
            data = f.read()

        self.solution_routing.optimization_request = data
        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        print(sol)

    @patch('optimise.api.solution_routing_crud.update')
    def test_routing_dispersion_3(self, mock_update):
        with open(os.path.join(dirname, 'data/clustered/clustered_orders_test3.json'), encoding="utf-8") as f:
            data = f.read()
        self.solution_routing.optimization_request = data
        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        print(sol)
    @patch('optimise.api.solution_routing_crud.update')
    def test_parameters(self, mock_update):
        with open(os.path.join(dirname, 'data/basic/basic_1.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None
        data = json.loads(self.solution_routing.optimization_request)
        instances, _ = get_optimization_instances(self.solution_routing)
        [instance.update_strategies() for instance in instances]
        assert len(instances) == 1
        assert instances[0].time_limit == DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES*60
        assert instances[0].allow_slack == 2*3600
        assert instances[0].result_type == DEFAULT_RESULT_TYPE
        assert instances[0].first_solution_strategy in FAST_FIRST_SOLUTIONS
        assert instances[0].local_search_metaheuristic in FAST_METAHEURISTIC_SEARCH
        assert instances[0].no_improvement_limit == DEFAULT_NO_IMPROVEMENT_LIMIT
        data['allow_slack'] = 0
        data['result_type'] = 'optimized'
        data['no_improvement_limit'] = 60

        self.solution_routing.optimization_request = json.dumps(data)
        instances, _ = get_optimization_instances(self.solution_routing)
        [instance.update_strategies() for instance in instances]
        assert instances[0].allow_slack == 0
        assert instances[0].result_type == 'optimized'
        instances[0].update_strategies()
        assert instances[0].first_solution_strategy in OPTIMIZED_FIRST_SOLUTIONS
        assert instances[0].local_search_metaheuristic in OPTIMIZED_METAHEURISTIC_SEARCH
        assert instances[0].no_improvement_limit == 60

    @patch('optimise.api.solution_routing_crud.update')
    def test_allowed_time(self, mock_update):
        with open(os.path.join(dirname, 'data/constraints/request_test_task_span.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        assert sol['dropped'] == []


    @patch('optimise.api.solution_routing_crud.update')
    def test_blocked_time_1(self, mock_update):
        with open(os.path.join(dirname, 'data/constraints/blocked_date_1.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        assert sol['dropped'] == []


    @patch('optimise.api.solution_routing_crud.update')
    def test_geo_coordinate_check(self, mock_update):
        with open(os.path.join(dirname, 'data/geo/geo_coordinate_check_offline.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        assert sol['dropped'] == []
        assert sol['2024-05-27'][0]['tour_steps'][1]['node']['latitude'] != sol['2024-05-27'][0]['tour_steps'][2]['node']['latitude']
        assert sol['2024-05-27'][0]['tour_steps'][1]['node']['longitude'] != sol['2024-05-27'][0]['tour_steps'][2]['node']['longitude']

    @patch('optimise.api.solution_routing_crud.update')
    def test_must_start(self, mock_update):
        with open(os.path.join(dirname, 'data/constraints/must_start_at.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        assert  sol['2024-02-21'][0]['tour_steps'][7]['node']['id']=='0000104427310010' or sol['2024-02-21'][0]['tour_steps'][8]['node']['id']=='0000104427310010'


    @patch('optimise.api.solution_routing_crud.update')
    def test_blocked_time(self, mock_update):
        with open(os.path.join(dirname, 'data/constraints/blocked_times.json'), encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)
        assert sol['2024-02-19'][0]['tour_steps'][1]['node']['service_start_time'] >= '12:00'
        assert sol['dropped'] == []


    @patch('optimise.api.solution_routing_crud.update')
    def test_orders_skills(self, mock_update):
        requests = [os.path.join(dirname, 'data/skills/skills_1.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request =f.read()
            mock_update.return_value = None

            sol = get_optimal_routes( self.solution_routing)
            assert len(sol['dropped']) == 1

    @patch('optimise.api.solution_routing_crud.update')
    def test_blocked_date(self, mock_update):
        requests = [os.path.join(dirname, 'data/constraints/blocked_times_1.2.7.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request =f.read()
            mock_update.return_value = None

            sol = get_optimal_routes( self.solution_routing)
            assert len(sol['dropped']) <= 9
            assert sol['2024-03-04'][1]['tour_steps'][1]['node']['service_start_time']<'09:00'
            assert sol['2024-03-05'][1]['tour_steps'][1]['node']['service_start_time'] >= '13:00'

    @patch('optimise.api.solution_routing_crud.update')
    def test_1_order_1_worker(self, mock_update):
        requests = [os.path.join(dirname, 'data/basic/1_order_1_worker.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request =f.read()
            data = json.loads(self.solution_routing.optimization_request)
            self.solution_routing.optimization_request = json.dumps(data)
            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert len(sol['dropped']) == 1

            data['teams']['10000013']['workers'][0]['shifts'][0]['optional'] = True

            self.solution_routing.optimization_request = json.dumps(data)
            mock_update.return_value = None
            sol = get_optimal_routes(self.solution_routing)
            assert len(sol['dropped']) == 0

    @patch('optimise.api.solution_routing_crud.update')
    def test_defect_17(self, mock_update):
        requests = [
            os.path.join(dirname, 'data/constraints/defect_17.json')]

        req = requests[0]
        with open(req, encoding="utf-8") as f:
            self.solution_routing.optimization_request = f.read()

        # mock_update.return_value = None
        # sol = get_optimal_routes(self.solution_routing)
        #
        # assert len(sol['dropped']) == 1
        #
        data = json.loads(self.solution_routing.optimization_request)
        # assert sol['dropped'][0]['reason_for_not_scheduling'] == translate("NO_SKILL_MATCH", data.get('language')).format('ELEC')

        data['result_type'] = 'fast'
        self.solution_routing.optimization_request = json.dumps(data)
        try:
            sol = get_optimal_routes(self.solution_routing)
        except Exception as e:
            print(e)
        assert len(sol['dropped']) == 1
        assert sol['dropped'][0]['reason_for_not_scheduling'] == translate("NO_SKILL_MATCH", data.get('language')).format('ELEC')

    @patch('optimise.api.solution_routing_crud.update')
    def test_workload_distribution(self, mock_update):
        requests = [
            os.path.join(dirname, 'data/basic/multiple_orders.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                data = f.read()

            self.solution_routing.optimization_request = data
            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert len([s for s in sol['2023-09-13'] if len(s['tour_steps']) > 2]) == 3
            # TODO this gives an error because deepcopy(data) transforms the date_string to datetime
            # data["minimize_vehicles"]=True
            # self.solution_routing.optimization_request = deepcopy(data)
            # sol=get_optimal_routes(self.db_session, self.solution_routing)
            # assert len([s for s in sol['2023-09-13'] if len(s['tour_steps'])>2])==1

    @patch('optimise.api.solution_routing_crud.update')
    def test_orders_are_sceduled(self, mock_update):
        requests = [os.path.join(dirname, 'data/misc/request1.json'),
                    os.path.join(dirname, 'data/constraints/request_test_task_span.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['dropped'] == []

    @patch('optimise.api.solution_routing_crud.update')
    def test_optimization_timing(self, mock_update):
        requests = [os.path.join(dirname, 'data/large/48_orders_2_employees.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['2023-12-18'] [0]['tour_steps'][-1]['node']['service_end_time'] >= '16:00'
            assert sol['dropped'] == []

        # data = json.loads(self.solution_routing.optimization_request)
        # data['result_type'] = 'optimized'
        # self.solution_routing.optimization_request = json.dumps(data)
        # sol = get_optimal_routes( self.solution_routing)
        # assert sol['2023-12-18'] [0]['tour_steps'][-1]['node']['service_end_time'] >= '16:00'
        # assert sol['dropped'] == []
        #
        # data = json.loads(self.solution_routing.optimization_request)
        # data['result_type'] = 'best'
        # self.solution_routing.optimization_request = json.dumps(data)
        # sol = get_optimal_routes(self.solution_routing)
        # assert sol['2023-12-18'][0]['tour_steps'][-1]['node']['service_end_time'] >= '16:00'
        # assert sol['dropped'] == []


    @patch('optimise.api.solution_routing_crud.update')
    def test_time_start_is_repected(self, mock_update):
        requests = [os.path.join(dirname, 'data/basic/basic_3orders.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['dropped'] == []
            assert sol['2023-09-18'][0]['tour_steps'][0]['node']['service_start_time'] == '08:00'

    @patch('optimise.api.solution_routing_crud.update')
    def test_unscheduled_date_is_repected(self, mock_update):
        requests = [os.path.join(dirname, 'data/basic/basic_3orders_shiftdate.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['2023-09-18'] == []

    @patch('optimise.api.solution_routing_crud.update')
    def test_end_at_home(self, mock_update):
        requests = [os.path.join(dirname, 'data/basic/basic_depot_home.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['2023-01-03'][0]['tour_steps'][-1]['node']['id'] == 'Home-1'

    @patch('optimise.api.solution_routing_crud.update')
    def test_satrt_end_at_home(self, mock_update):
        requests = [os.path.join(dirname, 'data/basic/basic_home_home.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes( self.solution_routing)
            assert sol['2023-01-03'][0]['tour_steps'][-1]['node']['id'] == 'Home-1'
    @patch('optimise.api.solution_routing_crud.update')
    def test_geolocated_addresses(self, mock_update):
        requests = [os.path.join(dirname, 'data/geo/basic_3orders_geolocation_only.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes(self.solution_routing)
            assert sol['dropped'] == []
            assert sol['2023-09-18'][0]['tour_steps'][0]['node']['service_start_time'] == '08:00'

    @patch('optimise.api.solution_routing_crud.update')
    def test_order_must_start_at(self, mock_update):
        requests = [os.path.join(dirname, 'data/constraints/must_start_on_date.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()

            mock_update.return_value = None
            sol = get_optimal_routes(self.solution_routing)
            assert sol['dropped'] == []
            assert sol['2024-01-05'][0]['tour_steps'][4]['node']['id'] == '0000070004120010'
            assert sol['2024-01-05'][0]['tour_steps'][4]['node']['service_start_time'] < '09:35'
            assert sol['2024-01-05'][0]['tour_steps'][5]['node']['id'] == '0000070004130010'
            assert sol['2024-01-05'][0]['tour_steps'][5]['node']['service_start_time'] < '10:05'



    @patch('optimise.api.solution_routing_crud.update')
    def test_worker_geolocation(self, mock_update):
        requests = [os.path.join(dirname, 'data/geo/test_coordinates_offline.json')]

        for req in requests:
            with open(req, encoding="utf-8") as f:
                self.solution_routing.optimization_request = f.read()
            data=json.loads(self.solution_routing.optimization_request)
            mock_update.return_value = None
            sol = get_optimal_routes(self.solution_routing)
            assert sol['dropped'] == []
            assert sol['2024-01-16'][0]['latitude'] == data['teams']['10000013']['workers'][0]['latitude']
            assert sol['2024-01-16'][0]['longitude'] == data['teams']['10000013']['workers'][0]['longitude']



if __name__ == '__main__':
    unittest.main()
