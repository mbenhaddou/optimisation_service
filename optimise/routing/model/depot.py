from optimise.utils.dates import format_time_as_hours_minutes

from optimise.routing.model.node import Node
from typing import Any, Dict
from optimise.routing.constants import translate

"""
Depot class representing a depot in the routing optimization model.
Inherits from the Node class.
"""
class Depot(Node):
    """
    Initializes a new Depot instance.
    """
    def __init__(self, id: str, address: str, latitude: float = None, longitude: float = None):
        super().__init__(id=id,address=address, latitude=latitude, longitude=longitude)
        self.wait_time_minutes=0
    @property
    def service_end_time(self):
        return format_time_as_hours_minutes(self._visit_start_time+int(self.wait_time_minutes))

    """
    Converts the Depot object to a dictionary.
    """
    def to_dict(self):
        obj_dict=super().to_dict()
        obj_dict["wait_time"]=self.wait_time_minutes
        return obj_dict


    @classmethod
    def from_dict(cls, depot_dict: Dict[str, Any]) -> "Depot":
        try:
            id = depot_dict['id']
            address = depot_dict['address']
            latitude = depot_dict.get('latitude')
            longitude = depot_dict.get('longitude')
            return cls(id=id, address=address, latitude=latitude, longitude=longitude)
        except KeyError as e:
            #TODO error in request language
            raise ValueError(f"Missing key in depot dictionary: {e}")
