import unittest
import json
from unittest.mock import Mock, patch

from optimise import api
import os

dirname = os.path.dirname(__file__)

os.environ['TEST_ENVIRONMENT'] = 'True'
class TestBasicsRun(unittest.TestCase):
    """
    Class TestBasicsRun:
    this class tests the basic functionality of the API : if the most basic problems can be solved
    """

    @patch('optimise.api.solution_routing_crud.update')
    def setUp(self, mock_update) -> None:
        self.db_session = Mock()
        self.solution_routing = Mock()
        mock_update.return_value = None
        with open(os.path.join(dirname, "inputs/basic_1.json"), 'r', encoding='utf8') as f:
            self.solution_routing.optimization_request = f.read()
        self.response = api.get_optimal_routes( self.solution_routing)


    def test_response_format(self) -> None:
        response_keys = self.response.keys()
        for K in ['2023-01-03', '2023-01-04', 'message', 'dropped', 'errors']:
            with self.subTest(msg="the response is missing the key: " + str(K)):
                self.assertIn(K, response_keys)
            if K == "message":
                with self.subTest(msg="the response['message'] is not a dict"):
                    self.assertIsInstance(self.response['message'], dict)
            else:
                with self.subTest(msg="the response['" + str(K) + "'] is not a list"):
                    self.assertIsInstance(self.response[K], list)

        r_message_keys = self.response['message'].keys()
        for K in ['2023-01-03', '2023-01-04']:
            with self.subTest(msg="the response['message'] is missing the key: " + str(K)):
                self.assertIn(K, r_message_keys)
            with self.subTest(msg="the response['message']['" + str(K) + "'] is not a string"):
                self.assertIsInstance(self.response['message'][K], str)

        r_visits = self.response['2023-01-03'][0]
        r_visits_keys = r_visits.keys()
        for K in ['id', 'total_slack']:
            with self.subTest(msg="the response['2023-01-03'][0] is missing the key: " + str(K)):
                self.assertIn(K, r_visits_keys)
            with self.subTest(msg="the response['message']['" + str(K) + "'] is not an integer"):
                self.assertIsInstance(r_visits[K], int)
        for K in ['adresse', 'tour_start_time']:
            with self.subTest(msg="the response['2023-01-03'][0] is missing the key: " + str(K)):
                self.assertIn(K, r_visits_keys)
            with self.subTest(msg="the response['message']['" + str(K) + "'] is not an string"):
                self.assertIsInstance(r_visits[K], str)
        for K in ['longitude', 'latitude', 'total_distance', 'tour_driving_time', 'total_tour_time']:
            with self.subTest(msg="the response['2023-01-03'][0] is missing the key: " + str(K)):
                self.assertIn(K, r_visits_keys)
            with self.subTest(msg="the response['message']['" + str(K) + "'] is not an string"):
                self.assertIsInstance(r_visits[K], (int, float))
        for K in ['tour_steps']:
            with self.subTest(msg="the response['2023-01-03'][0] is missing the key: " + str(K)):
                self.assertIn(K, r_visits_keys)
            with self.subTest(msg="the response['message']['" + str(K) + "'] is not an list"):
                self.assertIsInstance(r_visits[K], list)

    def test_basic_1(self) -> None:
        self.assertEqual(0, len(self.response['dropped']), 'incorrect number of dropped orders')


if __name__ == '__main__':
    unittest.main()
