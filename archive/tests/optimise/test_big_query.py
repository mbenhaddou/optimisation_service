import sys
import time
import json
from unittest.mock import Mock, patch
from solution_routing.solution_routing_model import SolutionRouting

sys.path.append('../scheduling_optimization/')
from optimise.api import get_optimal_routes
import os

dirname = os.path.dirname(__file__)

import unittest
os.environ['TEST_ENVIRONMENT'] = 'True'

class TestRouting(unittest.TestCase):
    def setUp(self):
        self.db_session = Mock()
        self.solution_routing = SolutionRouting()#Mock()

    @patch('optimise.api.solution_routing_crud.update')
    def test_routing(self, mock_update):
        with open(os.path.join(dirname, 'data/large/request_test_Mecanique.json')) as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        data = json.loads(self.solution_routing.optimization_request)
        mock_update.return_value = None

        data['result_type'] = 'optimized'
        self.solution_routing.optimization_request = json.dumps(data)
        start_time_2=time.time()
        sol_2 = get_optimal_routes(self.solution_routing)
        time_span_2 = time.time() - start_time_2

        data['result_type'] = 'fast'
        start_time=time.time()
        sol_1 = get_optimal_routes( self.solution_routing)
        time_span_1 = time.time() - start_time


        print('time_span_1', time_span_1)
        print('time_span_2', time_span_2)

#        assert time_span_1 < time_span_2
        self.assertTrue(len(sol_1['dropped']) <= 43)


if __name__ == '__main__':
    unittest.main()
