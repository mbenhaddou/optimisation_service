from optimise.routing.model.common import IntervalTime, TourStep, TwoIntervalTime
from optimise.routing.model.node import Node
from typing import Dict, Any
import copy
from optimise.routing.constants import translate
#from optimise.routing.defaults import UNITS_PER_HOUR_MODEL
from optimise.routing.defaults import ROUTING_TIME_RESOLUTION
from optimise.utils.dates import check_time_interval, time_to_integer, convert_time_to_app_unit, convert_units

"""
Worker class representing a worker in the routing optimization model.
"""
class Worker:
    """
    Initializes a new Worker instance.
    """
    def __init__(self, id: str, skills: list, date_format: str, depot=None, adresse: str = None, longitude: float = None, latitude: float = None, blocked_times: list = None, shifts: list = None, day_starts_at=None, day_ends_at=None, pause_starts_at=None, pause_ends_at=None) -> None:
        if blocked_times is None:
            blocked_times = []
        if shifts is None:
            shifts = []
        self.id=id
        self.skills=skills
        self.blocked_times=[IntervalTime(date=b['blocked_date'], start=b['blocked_start'], end=b['blocked_end']) for b in blocked_times]
        self.address=adresse
        self.longitude=longitude
        self.latitude=latitude
        self.date_format=date_format
        self.tour_steps=[]
        self.shifts=[TwoIntervalTime(date=b['shift_date'], start_day=b['shift_start'], end_day=b['shift_end'], start_pause=b['pause_start'], end_pause=b['pause_end'], pause_optional=b['optional']) for b in shifts]
        self.total_distance = 0
        self.tour_driving_time = 0
        self.total_tour_time = 0
        self.tour_start_time=0
        self.tour_end_time=0
        self.total_slack=0
        self.instance=None
        self.depot=depot
        self._day_starts_at=day_starts_at
        self._day_ends_at=day_ends_at
        self._pause_starts_at=pause_starts_at
        self._pause_ends_at= pause_ends_at
        self._pause_optional=False

    def __repr__(self):
        return str(self.id)
    """
    Adds a work order_or_worker to the worker's schedule.
    """
    def add_work_order(self, node:Node, slack_time):
        node.assigned_worker=self
        self.total_distance += node.travel_distance
        self.tour_driving_time += node.travel_time
        self.total_slack += slack_time
        self.total_tour_time += node.travel_time + (node.work_order_duration if hasattr(node, "work_order_duration") else node.wait_time_minutes)+slack_time

        self.tour_end_time=node.service_end_time
        self.tour_steps.append(TourStep(node=copy.copy(node), distance_so_far=copy.copy(self.total_distance), travel_time_so_far=copy.copy(self.tour_driving_time), slack_time_so_far=copy.copy(self.total_slack)))


    def get_shift_times(self, date):
        date_shift = [shift for shift in self.shifts if shift.date == date]
        return (convert_time_to_app_unit(date_shift[0].start_day), convert_time_to_app_unit(date_shift[0].end_day)) if date_shift else (convert_time_to_app_unit(self.day_starts_at), convert_time_to_app_unit(self.day_ends_at))
    """
    Returns the worker's schedule by considering blocked times.
    """

    def get_schedule(self):
        """
        Get the blocked times for the worker during a particular date.

        Returns:
        - A list of tuples, where each tuple consists of the start and duration of a blocked period.
        """

        blocked_times_ret = []

        # Worker can't work until their shift starts
        start, end = 0, time_to_integer(self.day_starts_at,self.instance.language, day_min_unit=ROUTING_TIME_RESOLUTION)
        check_time_interval(start, end,self.instance.language)
        blocked_times_ret.append((start, end - start, False)) #start, duration, optional

        try:
            # Pause period during which worker can't work
            start, end = time_to_integer(self.pause_starts_at,self.instance.language,day_min_unit=ROUTING_TIME_RESOLUTION), time_to_integer(self.pause_ends_at,self.instance.language,day_min_unit=ROUTING_TIME_RESOLUTION)
            check_time_interval(start, end,self.instance.language)
            if end -start > 0:
                blocked_times_ret.append((start, end - start, self.pause_optional))
        except Exception as e:
            print(e)
        for bt in self.blocked_times:
            if bt.date != self.instance.current_optimization_date:
                continue
            start, end = time_to_integer(bt.start, self.instance.language,day_min_unit=ROUTING_TIME_RESOLUTION), time_to_integer(bt.end, self.instance.language,day_min_unit=ROUTING_TIME_RESOLUTION)
            check_time_interval(start, end,self.instance.language)
            blocked_times_ret.append((start, end - start, False))
        # Worker can't work after their shift ends
        start, end=convert_time_to_app_unit(self.day_ends_at), convert_units(24, "hours",self.instance.language)-1

        check_time_interval(start, end,self.instance.language)
        blocked_times_ret.append((start, end - start, False))

        return blocked_times_ret


    def init_worker(self):
        self.tour_steps=[]
        self.total_distance = 0
        self.tour_driving_time = 0
        self.total_tour_time = 0
        self.tour_start_time=0
        self.tour_end_time=0
        self.total_slack=0



    @property
    def total_working_time(self):
        return self.total_tour_time - self.tour_driving_time

    @property
    def is_working(self):
        return  [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()] or len(self.shifts)==0

    @property
    def day_starts_at(self):
        day_schedule= [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].start_day
        return self._day_starts_at
    @property
    def day_ends_at(self):
        day_schedule= [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].end_day

        return self._day_ends_at

    @property
    def pause_starts_at(self):
        day_schedule= [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].start_pause
        return self._pause_starts_at
    @property
    def pause_ends_at(self):
        day_schedule= [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].end_pause
        return self._pause_ends_at
    @property
    def pause_optional(self):
        day_schedule= [bt for bt in self.shifts if bt.date.date() == self.instance.current_optimization_date.date()]
        if day_schedule:
            return day_schedule[0].pause_optional
        return self._pause_optional

    @property
    def day_starts_at_integer(self):
        return time_to_integer(self.day_starts_at,self.instance.language, day_min_unit=ROUTING_TIME_RESOLUTION)
    @property
    def day_ends_at_integer(self):
        return time_to_integer(self.day_ends_at,self.instance.language, day_min_unit=ROUTING_TIME_RESOLUTION)

    @property
    def pause_starts_at_integer(self):
        return time_to_integer(self.pause_starts_at,self.instance.language, day_min_unit=ROUTING_TIME_RESOLUTION)
    @property
    def pause_ends_at_integer(self):
        return time_to_integer(self.pause_ends_at, self.instance.language,day_min_unit=ROUTING_TIME_RESOLUTION)

    @classmethod
    def from_dict(cls, worker_dict: Dict[str, Any], request: Dict[str, Any]):
        try:
            id = worker_dict['e_id']
            skills = worker_dict['skills']
            date_format = request['date_format']
            depot = worker_dict.get('depot', request['depot'])
            address = worker_dict['address']
            latitude = worker_dict['latitude']
            longitude = worker_dict['longitude']
            blocked_times = worker_dict['blocked_times']
            day_starts_at = worker_dict['day_starts_at']
            day_ends_at = worker_dict['day_ends_at']
            pause_starts_at = worker_dict['pause_starts_at']
            pause_ends_at = worker_dict['pause_ends_at']
            shifts = worker_dict['shifts']

            return cls(id, skills, date_format, depot, address,  longitude, latitude, blocked_times, shifts, day_starts_at, day_ends_at, pause_starts_at, pause_ends_at)
        except KeyError as e:
            raise ValueError(translate("missing_key_in_worker_dict", request.get("language")).format(e))

    def __repr__(self):
        return f"Worker(id={self.id}, skills={self.skills}, depot={self.depot})"

    def validate_worker(self):
        if not self.skills:
            raise ValueError(translate("worker_has_no_skills", self.instance.language))
        if not self.depot:
            raise ValueError(translate("worker_has_no_depot", self.instance.language))
        # Add more validation as needed


    def to_dict(self):
        obj_dict={}
        obj_dict["id"]=self.id
        obj_dict["adresse"]=self.address
        obj_dict["longitude"]=self.longitude
        obj_dict["latitude"] = self.latitude
        obj_dict["total_distance"]= self.total_distance
        obj_dict["tour_driving_time"]= self.tour_driving_time
        obj_dict["total_tour_time"]= self.total_tour_time
        obj_dict["tour_start_time"]= self.tour_start_time
        obj_dict["tour_end_time"]= self.tour_end_time
        obj_dict["total_slack"]= self.total_slack
        obj_dict["tour_steps"]=[]
        for step in self.tour_steps:
            step_dict={}
            step_dict["node"]=step.node.to_dict()
            step_dict["distance_so_far"]=step.distance_so_far
            step_dict["travel_time_so_far"]=step.travel_time_so_far
            step_dict["slack_time_so_far"]=step.slack_time_so_far
            obj_dict["tour_steps"].append(step_dict)
        return obj_dict
