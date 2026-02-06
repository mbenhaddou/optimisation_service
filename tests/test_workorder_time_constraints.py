from datetime import datetime, time

from optimise.routing.model.workorder import WorkOrder


class DummyInstance:
    def __init__(self, current_date):
        self.current_optimization_date = current_date
        self.language = "en"


def test_workorder_time_constraint_respects_visiting_hours():
    order = WorkOrder(
        id="wo-1",
        address="street 1",
        work_hours=3600,
        earliest_start_datetime=datetime(2024, 1, 1, 8, 0, 0),
        latest_end_datetime=datetime(2024, 1, 1, 17, 0, 0),
        visiting_hour_start=time(9, 0, 0),
        visiting_hour_end=time(18, 0, 0),
        date_format="%Y-%m-%d %H:%M:%S",
    )
    order.instance = DummyInstance(datetime(2024, 1, 1, 0, 0, 0))

    start, end = order.get_time_constraint()
    assert start == 9 * 3600
    assert end == 17 * 3600


def test_workorder_validation_flags_invalid_window():
    order = WorkOrder(
        id="wo-2",
        address="street 2",
        work_hours=7200,
        earliest_start_datetime=datetime(2024, 1, 1, 9, 0, 0),
        latest_end_datetime=datetime(2024, 1, 1, 10, 0, 0),
        visiting_hour_start=time(9, 0, 0),
        visiting_hour_end=time(8, 0, 0),
        date_format="%Y-%m-%d %H:%M:%S",
    )
    order.instance = DummyInstance(datetime(2024, 1, 1, 0, 0, 0))

    messages = order.validate_work_order_constraints()
    assert messages
