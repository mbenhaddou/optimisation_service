from optimise.utils.dates import format_time_as_hours_minutes

"""
Node class serving as a base class for other classes like WorkOrder, Home, etc.
"""
class Node:
    """
    Initializes a new Node instance.
    """
    def __init__(self, id: str, address: str, latitude: float = None, longitude: float = None):
        self.id = id
        self.step_number=None
        self.address=address
        self.latitude=latitude
        self.longitude=longitude
        self.date=None
        self.travel_distance=None
        self.travel_time=None
        self._visit_start_time=None
        self.reason_for_not_scheduling=None
        self.instance=None

    """
    Property method.
    """
    @property
    def service_end_time(self):
        raise NotImplementedError

    """
    Property method.
    """
    @property
    def service_start_time(self):
        if self._visit_start_time is None:
            return ""
        return format_time_as_hours_minutes(self._visit_start_time)



    """
    Converts the Node object to a dictionary.
    """
    def to_dict(self):
        obj_dict={}
        obj_dict["id"]= self.id
        obj_dict["step_number"]=self.step_number
        obj_dict["address"] = self.address
        obj_dict["latitude"] = self.latitude
        obj_dict["longitude"] = self.longitude
        obj_dict["date"]= self.date
        obj_dict["traveled_distance_from_last_node"]=self.travel_distance
        obj_dict["service_end_time"]=self.service_end_time
        obj_dict["travel_time_from_last_node"]=self.travel_time
        obj_dict["service_start_time"]=self.service_start_time
        if self.reason_for_not_scheduling is not None:
            obj_dict["reason_for_not_scheduling"]=self.reason_for_not_scheduling
        return obj_dict
