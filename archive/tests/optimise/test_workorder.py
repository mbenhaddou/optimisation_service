import unittest
from optimise.routing.model.workorder import WorkOrder  # Replace 'your_module_path' with the actual module path
import pandas as pd
from optimise.routing.model import Instance
from optimise.routing.defaults import ROUTING_TIME_RESOLUTION
import os
from optimise.utils.dates import convert_units
dirname = os.path.dirname(__file__)

os.environ['TEST_ENVIRONMENT'] = 'True'
class TestWorkOrder(unittest.TestCase):

    def setUp(self):
        # Read the DataFrame from a CSV file or create it manually
        self.df = pd.read_excel(
            os.path.join(dirname, 'dates_test.xlsx'))  # Replace 'your_test_data.csv' with the actual file path
        self.df.replace({pd.NaT: None}, inplace=True)

    def test_work_orders(self):
        for index, row in self.df.iterrows():
            # Convert DataFrame row to a dictionary
            test_data = row.to_dict()
            print(index)
            # Create a WorkOrder object using the test data
            work_order = WorkOrder(
                id=index,
                address="Test Address",
                earliest_start_datetime=pd.to_datetime(test_data['earliest_start_datetime']),
                latest_end_datetime=pd.to_datetime(test_data['latest_end_datetime']),
                must_start_datetime=pd.to_datetime(test_data['must_start_datetime']),
                earliest_machine_availability_datetime=pd.to_datetime(
                    test_data['earliest_machine_availability_datetime']),
                latest_machine_availability_datetime=pd.to_datetime(test_data['latest_machine_availability_datetime']),
                spare_part_available_date=pd.to_datetime(test_data['spare_part_available_datetime']),
                visiting_hour_start=test_data['day_starts_at'],
                visiting_hour_end=test_data['day_ends_at'],
                work_hours=convert_units(test_data['task_duration'], "minutes","en"),
            )
            instance = Instance(period_start="2023-10-01", day_starts_at="00:00:00", day_ends_at="23:59:59")
            instance.current_optimization_date = test_data['current_date']
            work_order.instance = instance
            # Perform your tests here
            self.assertTrue(work_order.get_time_constraint()[0] <= work_order.get_time_constraint()[1])
            #            self.assertTrue(work_order.get_time_constraint()[1] - work_order.get_time_constraint()[0] >= work_order.work_order_duration)
            self.assertTrue(work_order.earliest_start == test_data['early_start'])
            self.assertTrue(work_order.latest_end == test_data['lastest_end'])
            self.assertTrue(work_order.get_time_constraint()[0] == convert_units(test_data['early_start_min'], "minutes","en"))
            self.assertTrue(work_order.get_time_constraint()[1] == convert_units(test_data['lastest_end_min'], "minutes","en"))
            self.assertTrue((len(work_order._validate_work_duration()) == 0) == test_data['is_eligible'])
            # Add more tests based on the DataFrame columns and WorkOrder methods


if __name__ == '__main__':
    unittest.main()
