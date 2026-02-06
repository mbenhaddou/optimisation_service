from collections import namedtuple


#from optimise.routing.defaults import UNITS_PER_HOUR_MODEL
IntervalTime = namedtuple('IntervalTime', ['date', 'start', 'end'])
TwoIntervalTime = namedtuple('TwoIntervalTime', ['date', 'start_day', 'end_day', 'start_pause', 'end_pause', 'pause_optional'])
TourStep=namedtuple("TourStep", ["node", "distance_so_far", "travel_time_so_far", "slack_time_so_far"])





