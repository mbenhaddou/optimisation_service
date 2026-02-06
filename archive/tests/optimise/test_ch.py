import sys
import json
from unittest.mock import Mock, patch

sys.path.append('../scheduling_optimization/')
from optimise.api import get_optimal_routes
import os

dirname = os.path.dirname(__file__)

import unittest

os.environ['TEST_ENVIRONMENT'] = 'True'
class TestRouting(unittest.TestCase):
    def setUp(self):
        self.db_session = Mock()
        self.solution_routing = Mock()

    @patch('optimise.api.solution_routing_crud.update')
    def test_routing(self, mock_update):
        with open(os.path.join(dirname, 'data/large/ch_large_test.json')) as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None

        sol = get_optimal_routes( self.solution_routing)

        self.assertTrue(len(sol['dropped']) == 0)
        self.assertTrue(len(sol['errors']) == 0)

    @patch('optimise.api.solution_routing_crud.update')
    def test_addresses(self, mock_update):
        with open(os.path.join(dirname, 'data/geo/ch_addresses.json')) as f:
            self.solution_routing.optimization_request = f.read()

        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None
        sol = get_optimal_routes( self.solution_routing)

        self.assertTrue(
            sol['2023-09-18'][0]['tour_steps'][1]['node']['latitude'] != sol['2023-09-18'][0]['tour_steps'][2]['node'][
                'latitude'])
        self.assertTrue(
            sol['2023-09-18'][0]['tour_steps'][1]['node']['longitude'] != sol['2023-09-18'][0]['tour_steps'][2]['node'][
                'longitude'])

    @patch('optimise.api.solution_routing_crud.update')
    def test_latency(self, mock_update):
        with open(os.path.join(dirname, 'data/large/soa_1.1.2.json')) as f:
            self.solution_routing.optimization_request = f.read()
        # Set up the mock behavior for solution_routing_crud.update
        mock_update.return_value = None
        sol = get_optimal_routes( self.solution_routing)

        print(sol)


if __name__ == '__main__':
    unittest.main()
