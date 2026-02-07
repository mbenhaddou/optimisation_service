from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SolverInput:
    """
    Pure, numeric input for the routing solver. This should not reference domain
    objects or external services. All units are expected to be normalized
    before construction (time in routing time resolution, distances in meters).
    """

    time_matrix: List[List[int]]
    distance_matrix: List[List[float]]
    time_windows: List[Tuple[int, int]]
    service_durations: List[int]
    num_vehicles: int
    starts: List[int]
    ends: List[int]
    breaks: List[List[Tuple[int, int, bool]]] = field(default_factory=list)
    soft_time_windows: List[Optional[Tuple[int, int, int]]] = field(default_factory=list)
    precedence_constraints: List[Tuple[int, int]] = field(default_factory=list)
    allowed_vehicles_by_node: Dict[int, List[int]] = field(default_factory=dict)

    # Capacity / working time
    max_working_time: int = 0
    max_route_distance: int = 0

    # Time dimension
    allow_slack: int = 0
    horizon: int = 0

    # Penalties and priorities
    penalties: List[int] = field(default_factory=list)
    location_priorities: List[Tuple[int, int]] = field(default_factory=list)

    # Feature flags
    distribute_load: bool = False
    minimize_vehicles: bool = False
    account_for_priority: bool = False
    enable_neighborhood_clustering: bool = False

    # Clustering options
    neighborhood_clustering_distance: Optional[str] = None
    neighborhood_clustering_penalty_factor: Optional[int] = None

    # Optional distance overlays
    haversine_distance: Optional[List[List[float]]] = None
    use_walking_distances_when_possible: bool = False
    walking_distances_threshold: Optional[int] = None

    # Solver parameters (can be overridden by SolveProfile)
    first_solution_strategy: Optional[str] = None
    local_search_metaheuristic: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    no_improvement_limit: Optional[int] = None

    # Objective
    objective: Optional[str] = None

    # Depot and penalty metadata
    num_depots: Optional[int] = None
    vehicle_penalty: Optional[int] = None

    # Time window and break tolerances (in routing time resolution)
    time_window_tolerance: int = 0
    break_time_tolerance: int = 0
    break_day_end: Optional[int] = None

    # Metadata
    meta: Dict[str, Any] = field(default_factory=dict)
