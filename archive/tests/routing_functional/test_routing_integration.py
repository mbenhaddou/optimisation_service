import unittest
import json
from optimise.routing.preprocessing.preprocess_request import validate_json, handle_time_and_date
from datetime import datetime
import os

dirname = os.path.dirname(__file__)
os.environ['TEST_ENVIRONMENT'] = 'True'

class ValidatePreProcessing(unittest.TestCase):

    def setUp(self) -> None:
        with open(os.path.join(dirname, "inputs/basic_1.json"), 'r', encoding='utf8') as f:
            self.this_input = json.load(f)

    def test_validate_json_general(self):
        # test with no modification that the input is in a valid format
        one_input = self.this_input.copy()
        self.assertEqual(True, validate_json(one_input, []), "the basic_1 input is NOT validated by validate_json")

    @unittest.skip("need to re-work validate_json, use config files to make it more manageable ?")
    def test_validate_json_missing_required_keys(self):
        for K in ['teams', 'orders', 'period_start', 'optimization_horizon', 'depot',
                  'start_at', 'end_at', 'time_unit', 'date_format', 'optimization_target',
                  'distance_method', 'time_limit', 'distribute_load', 'minimize_vehicles', 'account_for_priority']:
            wrong_input = {k: self.this_input[k] for k in self.this_input.keys() if k != K}
            with self.subTest(msg="validate_json does not catch when " + str(K) + " is missing"):
                self.assertEqual(False, validate_json(wrong_input, []))

    def test_handle_time_and_date(self):
        input_hours = self.this_input.copy()
        r = handle_time_and_date(input_hours, [])
        with self.subTest(msg="problem with handle_time_and_date and period_start"):
            self.assertEqual(datetime(2023, 1, 3, 0, 0), r['period_start'])
        with self.subTest(msg="problem with handle_time_and_date and optimization_horizon_end_date"):
            # the expected result is the period_start +2 days
            # because two days in horizon AND optimization_horizon_end_date is a STRICT upper bound (apparently)
            self.assertEqual(datetime(2023, 1, 5, 0, 0), r['optimization_horizon_end_date'])

        self.skipTest("There is a 'pass' in the code for 'time_unit' = 'minutes' , skipping test at the moment")
        # test if changing 'time_unit' from 'hours' to 'minutes' has an impact
        input_minutes = self.this_input.copy()
        input_minutes['time_unit'] = 'minutes'
        r_minutes = handle_time_and_date(input_minutes, [])
        test_minutes = []
        for k in r_minutes.keys():
            if k != 'time_unit':
                test_minutes.append(r_minutes[k] == r[k])
        with self.subTest(msg="handle_time_and_date is not changing anything if 'time_unit' is 'minutes'"):
            self.assertFalse(all(test_minutes))

        # def test_handle_orders(self):
        #     # 2023-09-07 : handle_orders modify 'request' from inside AND returns request['orders'] !!
        #     input_orders = self.this_input.copy()
        #     new_orders = handle_orders(input_orders, errors)


if __name__ == '__main__':
    unittest.main()
