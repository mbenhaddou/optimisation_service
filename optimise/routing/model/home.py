# from optimise.routing.model.node import Node
#
#
# """
# Home class representing a home location in the optimization model.
# Inherits from the Node class.
# """
# class Home(Node):
#     def __init__(self, id: str, address: str, latitude: float = None, longitude: float = None):
#         super().__init__(id=id, address=address, latitude=latitude, longitude=longitude)
#         self.id="Home-"+str(id)
#         self.wait_time_minutes=0
from optimise.routing.model.node import Node
from optimise.utils.dates import format_time_as_hours_minutes

"""
Home class representing a home location in the optimization model.
Inherits from the Node class.
"""
class Home(Node):
    def __init__(self, id: str, address: str, latitude: float = None, longitude: float = None):
        super().__init__(id=id, address=address, latitude=latitude, longitude=longitude)
        self.id="Home-"+str(id)
        self.wait_time_minutes=0

    """
    Calculates and returns the service end time based on wait_time_minutes.
    """

    @property
    def service_end_time(self):
        return format_time_as_hours_minutes(self._visit_start_time+int(self.wait_time_minutes))


