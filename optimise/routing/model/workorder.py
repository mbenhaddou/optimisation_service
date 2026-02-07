from typing import List, Optional, Union, Dict
import datetime
from optimise.routing.model.node import Node
from optimise.routing.model.common import IntervalTime
from optimise.routing.preprocessing.utilities import combine_date_and_time
from optimise.routing.constants import translate
from optimise.routing.defaults import VEHICULE_DROPPING_PENALTY
from optimise.utils.dates import convert_time_to_app_unit, format_time_as_hours_minutes

"""
WorkOrder class representing a work order_or_worker in the optimization model.
Inherits from the Node class.
"""
class WorkOrder(Node):
    ATTRIBUTES_LIST = [
        "instance", "priority", "skill",
        "earliest_start_datetime", "latest_end_datetime", "must_start_datetime",
        "earliest_machine_availability_datetime", "latest_machine_availability_datetime",
        "spare_part_available_date", "spare_part_available_time", "longitude", "latitude",
        "time_constraint", "assigned_worker", "slack_time", "errors", "must_end_datetime", "spare_part_available_date",
        "preferred_time_window_start_datetime", "preferred_time_window_end_datetime",
        "soft_time_window_penalty",
        "required_assignment",
    ]

    def __init__(self, **kwargs):
        super().__init__(kwargs.get("id"), kwargs.get("address"))
        self._set_attributes(kwargs)
        self.work_order_duration = kwargs.get("work_hours")
        self._visiting_hour_start = kwargs.get("visiting_hour_start")
        self._visiting_hour_end = kwargs.get("visiting_hour_end")
        self.date_format = kwargs.get("date_format", "%Y-%m-%d %H:%M:%S")
        self.errors = []
        self.is_scheduled = False
        self.has_been_scheduled = False
        self.instance = None
        visits_schedule = kwargs.get("visits_schedule", [])
        self.visits_schedule = [IntervalTime(date=b['visit_date'], start=b['visit_start'], end=b['visit_end']) for b in visits_schedule]
        if type(self.spare_part_available_date) is datetime.date and not isinstance(self.spare_part_available_date, datetime.datetime):
            self.spare_part_available_date = combine_date_and_time(self.spare_part_available_date, self.spare_part_available_time, date_format=self.date_format)
    def _set_attributes(self, attributes: Dict):
        for attribute in self.ATTRIBUTES_LIST:
            setattr(self, attribute, attributes.get(attribute, None))
    @property
    def earliest_start(self):
        if self.must_start_datetime is not None:
            return self.must_start_datetime

        valid_times = [time for time in [self.earliest_start_datetime, self.earliest_machine_availability_datetime,
                                         self.spare_part_available_date] if time is not None]

        return max(valid_times) if valid_times else None
    @property
    def latest_end(self):
        if self.must_end_datetime is not None:
            return self.must_end_datetime
        valid_times = [time for time in [self.latest_end_datetime, self.latest_machine_availability_datetime] if
                       time is not None]

        return min(valid_times) if valid_times else None

    @property
    def available_duration(self):
        if self.instance is not None:
            return (self.instance.optimisation_end_date - self.instance.current_optimization_date).days+1

    @property
    def workorder_penalty(self):
        if self.must_start_datetime is not None:
            return int(1e10)
        if getattr(self, "required_assignment", False):
            return int(1e12)

        return int(self.available_duration * VEHICULE_DROPPING_PENALTY/((self.latest_end-self.instance.current_optimization_date).days+1))

    @property
    def visiting_hour_start(self):
        day_schedule = [bt for bt in self.visits_schedule if bt.date == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].start
        return self._visiting_hour_start
    @property
    def visiting_hour_end(self):
        day_schedule = [bt for bt in self.visits_schedule if bt.date == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].end
        return self._visiting_hour_end



    @property
    def is_eligible(self):
        if self.earliest_start is None or self.latest_end is None or self.instance.current_optimization_date is None:
            return False
        is_within_date_range = self.earliest_start.date() <= self.instance.current_optimization_date.date() <= self.latest_end.date()
        if is_within_date_range:
            self.has_been_scheduled = True
        is_not_scheduled = not self.is_scheduled
        has_no_errors = not self.has_errors  # Assuming you've removed the 'has_errors' property as you mentioned earlier

        return is_within_date_range and is_not_scheduled and has_no_errors
    @property
    def has_errors(self):
        return len(self.validate_work_order_constraints())>0
    def __repr__(self) -> str:
        return str(self.id)

    def get_time_constraint(self):
        # Convert earliest_start and latest_end to minutes past midnight
        earliest_start_minutes=convert_time_to_app_unit(self.earliest_start)
        latest_end_minutes = convert_time_to_app_unit(self.latest_end)

        # Convert day_starts_at and day_ends_at to minutes past midnight
        day_starts_at_minutes = convert_time_to_app_unit(self.visiting_hour_start)
        day_ends_at_minutes = convert_time_to_app_unit(self.visiting_hour_end)

        # Calculate the time constraint bounds
        if self.earliest_start.date() == self.instance.current_optimization_date.date():
            interval_start = max(earliest_start_minutes, day_starts_at_minutes)
        else:
            interval_start = day_starts_at_minutes

        if self.latest_end.date() == self.instance.current_optimization_date.date():
            interval_end = min(latest_end_minutes, day_ends_at_minutes)
        else:
            interval_end = day_ends_at_minutes

        return (int(interval_start), int(interval_end))

    def get_preferred_time_constraint(self):
        if (
            self.preferred_time_window_start_datetime is None
            or self.preferred_time_window_end_datetime is None
            or self.instance is None
            or self.instance.current_optimization_date is None
        ):
            return None

        preferred_start = self.preferred_time_window_start_datetime
        preferred_end = self.preferred_time_window_end_datetime
        if preferred_start.date() != self.instance.current_optimization_date.date():
            return None

        preferred_start_minutes = convert_time_to_app_unit(preferred_start.time())
        preferred_end_minutes = convert_time_to_app_unit(preferred_end.time())

        day_starts_at_minutes = convert_time_to_app_unit(self.visiting_hour_start)
        day_ends_at_minutes = convert_time_to_app_unit(self.visiting_hour_end)

        interval_start = max(preferred_start_minutes, day_starts_at_minutes)
        interval_end = min(preferred_end_minutes, day_ends_at_minutes)
        if interval_start > interval_end:
            return None
        return (int(interval_start), int(interval_end))


    def validate_work_order_constraints(self):
        messages = []
        messages.extend(self._validate_time_constraints())
        messages.extend(self._validate_work_duration())
        messages.extend(self._validate_spare_part_availability())
        return messages

    def _validate_time_constraints(self):
        messages = []
        interval_start, interval_end = self.get_time_constraint()
        if interval_start > interval_end:
            messages.append(translate("TIME_CONSTRAINT_INCORRECT",self.instance.language))
        return messages

    def _validate_work_duration(self):
        messages = []
        interval_start, interval_end = self.get_time_constraint()
        if interval_end - interval_start < self.work_order_duration:
            messages.append(translate("LARGE_WORK_DURATION",self.instance.language))
        return messages

    def validate_optimization_period(self, opt_start, opt_end):
        messages = []
        if not (opt_start <= self.earliest_start <= opt_end and opt_start <= self.latest_end <= opt_end):
            messages.append(translate("OUTSIDE_OPTIMISATION_PERIOD",self.instance.language))
        return messages

    def _validate_spare_part_availability(self):
        messages = []

        if self.must_start_datetime is not None and self.must_start_datetime < self.spare_part_available_date:
            messages.append(translate("SPARE_PART_AVAILABILITY",self.instance.language))
        return messages

    def to_dict(self) -> Dict:
        obj_dict = super().to_dict()
        if self.assigned_worker:
            obj_dict["assigned_worker"] = self.assigned_worker.id
            obj_dict["slack_time"] = self.slack_time
            obj_dict["priority"] = self.priority
        return obj_dict



    def find_error_messages(self):
        self.errors = []
        if self.time_constraint[0] > self.time_constraint[1]:
            self.errors.append(translate("TIME_CONSTRAINT_INCORRECT",self.instance.language))
        if self.time_constraint[1] - self.time_constraint[0] < self.work_order_duration:
            self.errors.append(translate("LARGE_WORK_DURATION",self.instance.language))
        if self.must_start_datetime < self.spare_part_available_date:
            self.errors.append(translate("SPARE_PART_AVAILABILITY",self.instance.language))

    @property
    def service_end_time(self):
        if self._visit_start_time is None:
            return ""

        return format_time_as_hours_minutes(self._visit_start_time + int(self.work_order_duration))


    @staticmethod
    def from_dict(order_dict: Dict) -> 'WorkOrder':
        return WorkOrder(**order_dict)
