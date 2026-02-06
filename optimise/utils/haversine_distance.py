
from haversine import haversine_vector, Unit
import json


def haversine_distance_matrix(origines, destinations=None):
	if origines is None or len(origines) == 0:
		return []
	if destinations is None:
		return haversine_vector(origines, origines, Unit.METERS, comb=True)
	return haversine_vector(origines,destinations, Unit.METERS, comb=True)
