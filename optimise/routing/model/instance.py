import copy
from datetime import timedelta
from optimise.routing.core.functions import get_optimizer_strategy
from optimise.routing.constants import translate
from optimise.routing.model.depot import Depot
from optimise.routing.model.home import Home
from optimise.utils.dates import datetime_to_integer
from optimise.routing.defaults import *
from optimise.utils.dates import date_from_string
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from optimise.utils.dates import convert_units
from optimise.routing.distance_matrix import get_distance_matrix_with_retry
from optimise.utils.haversine_distance import haversine_distance_matrix



"""
Instance class representing a problem instance for routing optimization.
"""
class Instance:
    """
    Initializes a new Instance with various attributes like time windows, workers, etc.
    """
    def __init__(self,
                 period_start: datetime,
                 name: str = "routing",
                 language: str = "en",
                 time_windows: Optional[List[Union[int, float]]] = None,
                 time_matrix: Optional[List[List[Union[int, float]]]] = None,
                 distance_matrix: Optional[List[List[Union[int, float]]]] = None,
                 precomputed_time_matrix: Optional[List[List[Union[int, float]]]] = None,
                 precomputed_distance_matrix: Optional[List[List[Union[int, float]]]] = None,
                 initial_routes: Optional[List['Route']] = None,  # Assuming Route is another class
                 start_at: str = "depot",
                 end_at: str = "depot",
                 time_unit: str = "minutes",
                 day_starts_at: str = "00:00:00",  # Assuming this will be converted to a datetime object later
                 day_ends_at: str = "23:59:59",  # Assuming this will be converted to a datetime object later
                 account_for_priority=False,
                 date_format="%Y-%m-%d %H:%M:%S",
                 distribute_load=True,
                 minimize_vehicles=True,
                 optimization_horizon=None,
                 optimization_target='duration',
                 distance_matrix_method='osm',
                 driving_speed_kmh=DEFAULT_DRIVING_SPEED_KMH,
                 allow_slack=1000,
                 use_walking_distances_when_possible=True,
                 walking_distances_threshold=DEFAULT_WALKING_DISTANCES_THRESHOLD,
                 randomize_response=True,
                 random_seed=None,
                 enable_neighborhood_clustering=DEFAULT_NEIGHBORHOOD_CLUSTERING_ENABLED,
                 neighborhood_clustering_distance=DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE,
                 neighborhood_clustering_penalty_factor=DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR,
                 interval_time_tolerance=DEFAULT_TIME_TOLERANCE_MINUTES,
                 max_working_time=MAX_WORKING_TIME_MINUTES,
                 max_route_distance=0,
                 time_limit=0.008,
                 result_type=DEFAULT_RESULT_TYPE, # fast, optimized or best
                 first_solution_strategy=None,
                 local_search_metaheuristic=None,
                 no_improvement_limit=None
                 ) -> None:
        self.time_windows = time_windows
        self.name = name
        self.language = language
        self._workers =  []
        self._work_orders =  []
        self.soft_time_windows = []
        self.time_matrix = time_matrix
        self.distance_matrix = distance_matrix
        self.precomputed_time_matrix = precomputed_time_matrix
        self.precomputed_distance_matrix = precomputed_distance_matrix
        self.period_start = period_start
        self.initial_routes = initial_routes if initial_routes else []
        self.depots = []
        self.depot=None
        self.start_at = start_at
        self.end_at = end_at
        self.time_unit = time_unit
        self.date_format=date_format
        self.day_starts_at=date_from_string(day_starts_at, self.date_format.split()[1]).time()
        self.day_ends_at=date_from_string(day_ends_at, self.date_format.split()[1]).time()
        self.distribute_load=distribute_load
        self.minimize_vehicles=minimize_vehicles
        self.optimization_horizon=optimization_horizon
        self.optimization_target=optimization_target
        self.distance_matrix_method=distance_matrix_method
        self.driving_speed_kmh=driving_speed_kmh
        self.optimization_start_date=period_start
        self.enable_neighborhood_clustering=enable_neighborhood_clustering
        self.current_optimization_date=None
        self.allow_slack=int(allow_slack)
        self.allow_soft_time_windows=False
        self.include_service_time=True
        self.has_pickup_delivery=False
        self.location_priorities=[]
        self.blocked_time_tol=interval_time_tolerance
        self.objective_threshold=10000
        self.starts=[]
        self.ends=[]
        self.max_working_time=int(max_working_time)
        self.max_route_distance=int(max_route_distance) if max_route_distance else 0
        self.locations=[]
        self.service_durations=[]
        self._departure_time=None
        self.penalties = [1000]
        self.errors=[]
        self.randomize_response=randomize_response
        import random
        self.random_seed = random_seed
        self._rng = random.Random(random_seed) if random_seed is not None else random.Random()
        self.time_limit=time_limit
        self.account_for_priority=account_for_priority
        # Horizon is one full day in routing resolution, independent of input time unit.
        self.horizon = convert_units(24, "hours", self.language, ROUTING_TIME_RESOLUTION) - 1
        self._first_solution_strategy=first_solution_strategy
        self._local_search_metaheuristic=local_search_metaheuristic
        self.result_type=result_type
        self.no_improvement_limit=no_improvement_limit
        self._history_parameters = []
        self.vehicle_penalty=20000
        self.neighborhood_clustering_distance=neighborhood_clustering_distance
        self.neighborhood_clustering_penalty_factor=neighborhood_clustering_penalty_factor
        self.use_walking_distances_when_possible = use_walking_distances_when_possible
        self.walking_distances_threshold=walking_distances_threshold
        self.task_dependencies = []
        self.zone_restrictions = []
        self.traffic_mode = None
        self.traffic_include_historical = False
    def __repr__(self):
        return self.name


    @property
    def workers(self):
        return [w for w in self._workers if w.is_working]
    """
    Property method.
    """
    @property
    def work_orders(self):
        return [w for w in self._work_orders if w.is_eligible]


    def add_workorder(self, wo):
        wo.instance=self
        unit = self.time_unit
        if unit in ["hour", "hours"]:
            unit = "hours"
        elif unit in ["minute", "minutes"]:
            unit = "minutes"
        else:
            raise Exception(translate("unsupported_time_unit", self.language).format(self.time_unit))
        wo.work_order_duration = convert_units(wo.work_order_duration, unit, self.language, ROUTING_TIME_RESOLUTION)
        self._work_orders.append(wo)

    def add_worker(self, worker):
        worker.instance=self
        self._workers.append(worker)
    def get_blocked_times(self):
        bt= [w.get_blocked_dates(self.current_optimization_date) for w in self.workers]
        if bt == []:
            return None
        return bt

    """
    Property method.
    """
    @property
    def can_schedule_new_orders(self):
        if self.current_optimization_date is None:
            return True
        return len(self.work_orders)>0 and len(self.workers)>0

    @property
    def has_unscheduled_orders(self):
        return len(self.work_orders)>0

    def update_strategies(self, result_type=None):
        if result_type is not None:
            strategy, self._history_parameters = get_optimizer_strategy(
                result_type,
                history=self._history_parameters,
                deterministic=not self.randomize_response,
                rng=self._rng,
            )
        else:
            strategy, self._history_parameters = get_optimizer_strategy(
                self.result_type,
                history=self._history_parameters,
                deterministic=not self.randomize_response,
                rng=self._rng,
            )

        self._first_solution_strategy = strategy['first_solution_strategy']
        self._local_search_metaheuristic = strategy['local_search_metaheuristic']

    @property
    def first_solution_strategy(self):
        return self._first_solution_strategy

    @property
    def local_search_metaheuristic(self):
        return self._local_search_metaheuristic
    @staticmethod
    def load_from_json(self, json):
        return



    """
    Property method.
    """
    @property
    def nb_depots(self):
        return len(self.depots)
    def init_instance(self, date):
        self.locations=[]
        self.starts=[]
        self.ends=[]
        self.depots=[]
        self.service_durations=[]
        self.time_windows=[]
        self.soft_time_windows=[]
        self.distance_matrix=[]
        self.time_matrix=[]
        self.penalties=[]
        self.current_optimization_date=date
        self.allow_soft_time_windows = False
        self.location_priorities=[]



        if self._local_search_metaheuristic is None or self._first_solution_strategy is None:
            self.update_strategies()

        for w in self.workers:
            w.init_worker()
        if len(self.work_orders)>0 and len(self.workers)==0:
            #there is no worker to handle these work order_or_worker
            for wo in self.work_orders:
                message=translate("NO_SKILL_MATCH",self.language).format(wo.skill)
                if message not in wo.errors:
                    wo.errors.append(message)

        if len(self.work_orders)==0 or len(self.workers)==0:
            #there is no worker to handle these work order_or_worker
            return

        if self.start_at=="depot":
            for e in self.workers:
                if not any(location.get("address") == e.depot["address"] for location in self.locations):
                    self.locations.append({"address":e.depot["address"], "latitude":e.depot["latitude"], "longitude":e.depot["longitude"]})
                    self.service_durations.append(0)
                    depot=Depot(e.depot["id"], e.depot["address"], latitude=e.depot["latitude"], longitude=e.depot["longitude"])
                    depot.instance=self
                    self.depots.append(depot)
                self.starts.append(next((index for index, location in enumerate(self.locations) if location.get("address") == e.depot["address"]), 0))
        if self.start_at=="home":
            for e in self.workers:
                if not any(location.get("address") == e.address for location in self.locations):
                    self.locations.append({"address":e.address, "latitude":e.latitude, "longitude":e.longitude})
                    self.service_durations.append(0)
                    home=Home(e.id, e.address, latitude=e.latitude, longitude=e.longitude)
                    home.instance=self
                    self.depots.append(home)
                self.starts.append(next((index for index, location in enumerate(self.locations) if location.get("address") == e.address), 0))
        if self.end_at=="depot":
            for e in self.workers:
                if not any(location.get("address") == e.depot["address"] for location in self.locations):
                    self.locations.append({"address":e.depot["address"], "latitude":e.depot["latitude"], "longitude":e.depot["longitude"]})
                    self.service_durations.append(0)
                    depot=Depot(e.id, e.depot["address"], latitude=e.depot["latitude"], longitude=e.depot["longitude"])
                    depot.instance=self
                    self.depots.append(depot)
                self.ends.append(next((index for index, location in enumerate(self.locations) if location.get("address") == e.depot["address"]), 0))
        if self.end_at=="home":
            for e in self.workers:
                if not any(location.get("address") == e.address for location in self.locations):
                    self.locations.append({"address":e.address, "latitude":e.latitude, "longitude":e.longitude})
                    self.service_durations.append(0)
                    home=Home(e.id, e.address, latitude=e.latitude, longitude=e.longitude)
                    home.instance=self
                    self.depots.append(home)
                self.ends.append(next((index for index, location in enumerate(self.locations) if location.get("address") == e.address), 0))

        self.locations.extend([{"address":r.address, "latitude":r.latitude, "longitude":r.longitude} for r in self.work_orders])
        location_latlon = [[l["latitude"], l["longitude"]] for l in self.locations]
        location_lonlat = [[l["longitude"], l["latitude"]] for l in self.locations]
        if (
            self.precomputed_distance_matrix
            and self.precomputed_time_matrix
            and len(self.precomputed_distance_matrix) == len(self.locations)
            and len(self.precomputed_time_matrix) == len(self.locations)
        ):
            self.distance_matrix = self.precomputed_distance_matrix
            self.time_matrix = self.precomputed_time_matrix
            self.haversine_distance = haversine_distance_matrix(location_latlon)
            for order in self.work_orders:
                self.service_durations.append(order.work_order_duration)
                self.penalties.append(10000)
        elif self.distance_matrix_method == "haversine":
            self.haversine_distance = haversine_distance_matrix(location_latlon)
            self.distance_matrix = self.haversine_distance
            speed_mps = (self.driving_speed_kmh * 1000) / 3600.0
            self.time_matrix = [
                [
                    int(convert_units((dist / speed_mps) if speed_mps > 0 else 0, "seconds", self.language, ROUTING_TIME_RESOLUTION))
                    for dist in row
                ]
                for row in self.distance_matrix
            ]
        else:
            # distance_data = get_distance_matrix(method=self.distance_matrix_method, destinations=tuple([(l["latitude"], l["longitude"]) for l in self.locations]), departure_time=self.departure_time,error_language=self.language)
            try:
                distance_data = get_distance_matrix_with_retry(location_lonlat)
                self.distance_matrix = distance_data["distances"]
                self.time_matrix = distance_data["durations"]
            except Exception as e:
                raise ValueError(translate("failed_to_create_distance_matrix", self.language).format(e))

            self.haversine_distance = haversine_distance_matrix(location_latlon)
            for order in self.work_orders:
                self.service_durations.append(order.work_order_duration)
                self.penalties.append(10000)

        if self.traffic_mode == "predictive" and self.time_matrix:
            multiplier = 1.05
            if self.traffic_include_historical:
                multiplier = 1.1
            self.time_matrix = [
                [int(value * multiplier) for value in row] for row in self.time_matrix
            ]

        self.time_windows = [(datetime_to_integer(str(self.day_starts_at), self.language,date_format=self.date_format.split()[1],
                                                     intra_day=True),
                                 datetime_to_integer(str(self.day_ends_at), self.language,date_format=self.date_format.split()[1],
                                                     intra_day=True)) for i in range(0, self.nb_depots)]
        self.soft_time_windows = [None for _ in range(0, self.nb_depots)]

        for order in self.work_orders:
            self.time_windows.append(order.get_time_constraint())
            preferred_window = order.get_preferred_time_constraint()
            penalty = order.soft_time_window_penalty
            if preferred_window and penalty:
                self.soft_time_windows.append(
                    (preferred_window[0], preferred_window[1], int(penalty))
                )
                self.allow_soft_time_windows = True
            else:
                self.soft_time_windows.append(None)

        for i, wo in enumerate(self.work_orders):
            self.location_priorities.append((i + self.nb_depots, wo.priority))
    """
    Returns a list of work orders that are not scheduled.
    """
    def get_dropped_nodes(self):
        return [w for w in self._work_orders if not w.is_scheduled]

    """
    Property method.
    """
    @property
    def number_of_locations(self):
        if self.time_matrix:
            return len(self.time_matrix)
        elif self.distance_matrix:
            return len(self.distance_matrix)
        else:
            raise Exception(translate("neither_time_matrix_nor_distance_matrix_defined",self.language))

    @property
    def optimisation_end_date(self):
        return self.optimization_start_date+timedelta(days=self.optimization_horizon)

    def pauses(self):
        return [(w.pause_starts_at, w.pause_ends_at) for w in self.workers]
    """
    Property method.
    """
    @property
    def num_vehicles(self):
        return len(self.starts)
    """
    Property method.
    """
    @property
    def departure_time(self):
        """
        departure time is used for traffic estimation and is set at 8 of the morning for any future computation.
        if the optimisation is stated in the same day then, the departure date is set an hour after the current time.
        """
#        if self.period_start + timedelta(hours=8) < datetime.now():
 #           return datetime.now() + timedelta(hours=1)
        return self.period_start + timedelta(hours=8)

    @classmethod
    def from_dict(cls, instance_data: Dict[str, Any]) -> 'Instance':
        try:
            # Extract or set default values for all instance attributes from instance_data
            name = instance_data.get('name')
            language = instance_data.get('language', 'en')
            period_start = instance_data.get('period_start')
#            depot = Depot.from_dict(instance_data.get('depot'))
            start_at = instance_data.get('start_at', 'depot')
            end_at = instance_data.get('end_at', 'depot')
            account_for_priority = instance_data.get('account_for_priority', False)
            time_unit = instance_data.get('time_unit', 'minutes')
            date_format = instance_data.get('date_format', '%Y-%m-%d %H:%M:%S')
            distribute_load = instance_data.get('distribute_load', False)
            minimize_vehicles = instance_data.get('minimize_vehicles', False)
            optimization_horizon = instance_data.get('optimization_horizon', None)
            optimization_target = instance_data.get('optimization_target', 'duration')
            distance_matrix_method = instance_data.get('distance_matrix_method', instance_data.get('distance_method', 'osm'))
            driving_speed_kmh = instance_data.get('driving_speed_kmh', DEFAULT_DRIVING_SPEED_KMH)
            allow_slack = instance_data.get('allow_slack')
            max_working_time=instance_data.get("max_working_time")
            max_route_distance=instance_data.get("max_route_distance", 0)
            interval_time_tolerance=instance_data.get("time_interval_tolerance",None)
            time_limit = instance_data.get('time_limit')
            first_solution_strategy = instance_data.get('first_solution_strategy', None)
            local_search_metaheuristic= instance_data.get('local_search_metaheuristic', None)
            randomize_response=instance_data.get('randomize_response', True)
            random_seed=instance_data.get('random_seed')
            enable_neighborhood_clustering=instance_data.get('enable_neighborhood_clustering', True)
            result_type = instance_data.get('result_type', DEFAULT_RESULT_TYPE)
            use_walking_distances_when_possible = instance_data.get('use_walking_distances_when_possible', True)
            walking_distances_threshold= instance_data.get('walking_distances_threshold', DEFAULT_WALKING_DISTANCES_THRESHOLD)
            no_improvement_limit = instance_data.get('no_improvement_limit', DEFAULT_NO_IMPROVEMENT_LIMIT)
            neighborhood_clustering_distance = instance_data.get('neighborhood_clustering_distance', DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE)
            neighborhood_clustering_penalty_factor = instance_data.get('neighborhood_clustering_penalty_factor', DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR)

            # Create Instance object
            instance = cls(
                name=name,
                language=language,
                period_start=period_start,
#                depot=depot,
                start_at=start_at,
                end_at=end_at,
                account_for_priority=account_for_priority,
                time_unit=time_unit,
                date_format=date_format,
                distribute_load=distribute_load,
                minimize_vehicles=minimize_vehicles,
                optimization_horizon=optimization_horizon,
                optimization_target=optimization_target,
                enable_neighborhood_clustering=enable_neighborhood_clustering,
                distance_matrix_method=distance_matrix_method,
                driving_speed_kmh=driving_speed_kmh,
                allow_slack=allow_slack,
                max_working_time=int(max_working_time),
                max_route_distance=int(max_route_distance) if max_route_distance else 0,
                interval_time_tolerance=interval_time_tolerance,
                time_limit=int(time_limit),
                randomize_response=randomize_response,
                random_seed=random_seed,
                first_solution_strategy=first_solution_strategy,
                local_search_metaheuristic=local_search_metaheuristic,
                result_type=result_type,
                no_improvement_limit=no_improvement_limit,
                neighborhood_clustering_distance=neighborhood_clustering_distance,
                neighborhood_clustering_penalty_factor=neighborhood_clustering_penalty_factor,
                use_walking_distances_when_possible=use_walking_distances_when_possible,
                walking_distances_threshold=walking_distances_threshold
            )
            instance.precomputed_distance_matrix = instance_data.get(
                "precomputed_distance_matrix"
            )
            instance.precomputed_time_matrix = instance_data.get(
                "precomputed_time_matrix"
            )
            instance.task_dependencies = instance_data.get("task_dependencies", [])
            instance.zone_restrictions = instance_data.get("zone_restrictions", [])
            instance.traffic_mode = instance_data.get("traffic_mode")
            instance.traffic_include_historical = bool(
                instance_data.get("traffic_include_historical", False)
            )

            return instance
        except Exception as e:
            raise ValueError(translate("failed_to_create_instance_from_dict", instance_data.get('language')).format(e))
