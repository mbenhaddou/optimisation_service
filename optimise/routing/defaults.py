import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None else value


def _env_csv(name: str, default: list) -> list:
    value = os.getenv(name)
    if value is None:
        return default
    parts = [item.strip() for item in value.split(",")]
    return [item for item in parts if item]


SOLVER_LOG_SEARCH_PROGRESS = _env_bool("SOLVER_LOG_SEARCH_PROGRESS", True)
SOLVER_MAX_SEARCH_TIME_IN_SECONDS = _env_int("SOLVER_MAX_SEARCH_TIME_IN_SECONDS", -1)

# NUMBER OF PARALLEL WORKERS FOR RUNNING SOLVER. USUALLY THIS EQUAL TO NUMBER OF CPU
SEARCH_WORKERS = _env_int("SEARCH_WORKERS", -1)
ROUTING_TIME_RESOLUTION = _env_str("ROUTING_TIME_RESOLUTION", "seconds")
DEFAULT_SLACK_MINUTES = _env_int("DEFAULT_SLACK_MINUTES", 120)
DEFAULT_TIME_TOLERANCE_MINUTES = _env_int("DEFAULT_TIME_TOLERANCE_MINUTES", 15)
MAX_WORKING_TIME_MINUTES = _env_int("MAX_WORKING_TIME_MINUTES", 24 * 60)
DEFAULT_FIRST_SOLUTION_STRATEGY = _env_str("DEFAULT_FIRST_SOLUTION_STRATEGY", "PATH_CHEAPEST_ARC")
DEFAULT_LOCAL_SEARCH_METAHEURISTIC = _env_str("DEFAULT_LOCAL_SEARCH_METAHEURISTIC", "GREEDY_DESCENT")
DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES = _env_int("DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES", 60)
DEFAULT_RESULT_TYPE = _env_str("DEFAULT_RESULT_TYPE", "fast")  # fast, optimized or best
NUM_RUNS_FOR_BEST_RESULT_TYPE = _env_int("NUM_RUNS_FOR_BEST_RESULT_TYPE", 5)
MAX_NUM_WORKERS = _env_int("MAX_NUM_WORKERS", 20)
DEFAULT_NO_IMPROVEMENT_LIMIT = _env_int("DEFAULT_NO_IMPROVEMENT_LIMIT", 100)
DISTANCE_MATRIX_DIMENSION_PER_REQUEST = _env_int("DISTANCE_MATRIX_DIMENSION_PER_REQUEST", 50)
VEHICULE_DROPPING_PENALTY = _env_int("VEHICULE_DROPPING_PENALTY", 1000000)
DEFAULT_NEIGHBORHOOD_CLUSTERING_ENABLED = _env_bool(
    "DEFAULT_NEIGHBORHOOD_CLUSTERING_ENABLED", True
)
DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE = _env_str(
    "DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE", "haversine"
)
DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR = _env_int(
    "DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR", 10
)
ENABLE_DISTANCE_MATRIX_CACHE = _env_bool("ENABLE_DISTANCE_MATRIX_CACHE", False)
ENABLE_GEOCODING_CACHE = _env_bool("ENABLE_GEOCODING_CACHE", True)
GEOLOC_CACHE_BACKEND = os.getenv("GEOLOC_CACHE_BACKEND", "db")  # "db" or "local"
GEOLOC_LOCAL_CACHE_DIR = os.getenv("GEOLOC_LOCAL_CACHE_DIR", "cache/geolocations")
DISTANCE_MATRIX_CACHE_DIR = os.getenv("DISTANCE_MATRIX_CACHE_DIR", "cache/distance_matrix")
DEFAULT_WALKING_DISTANCES_THRESHOLD = _env_float("DEFAULT_WALKING_DISTANCES_THRESHOLD", 200)
DEFAULT_DRIVING_SPEED_KMH = _env_float("DEFAULT_DRIVING_SPEED_KMH", 40)
FAST_FIRST_SOLUTIONS = _env_csv(
    "FAST_FIRST_SOLUTIONS",
    ["UNSET", "PARALLEL_CHEAPEST_INSERTION"],
)
FAST_METAHEURISTIC_SEARCH = _env_csv(
    "FAST_METAHEURISTIC_SEARCH",
    ["GUIDED_LOCAL_SEARCH", "UNSET", "GREEDY_DESCENT"],
)
DEFAULT_GEOCODING_SERVICE = os.getenv("DEFAULT_GEOCODING_SERVICE", "google")
USE_NEW_SOLVER = _env_bool("USE_NEW_SOLVER", False)

OPTIMIZED_FIRST_SOLUTIONS = _env_csv(
    "OPTIMIZED_FIRST_SOLUTIONS",
    ["LOCAL_CHEAPEST_ARC", "BEST_INSERTION", "GLOBAL_CHEAPEST_ARC"],
)
OPTIMIZED_METAHEURISTIC_SEARCH = _env_csv(
    "OPTIMIZED_METAHEURISTIC_SEARCH",
    ["SIMULATED_ANNEALING", "GENERIC_TABU_SEARCH"],
)
