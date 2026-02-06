
# Configuration Parameters – Detailed Explanation

This document provides a comprehensive explanation of the key routing engine parameters from `defaults.py`.

## Solver Control

- `SOLVER_LOG_SEARCH_PROGRESS = True`  
  Enables verbose logging from OR-Tools during search. Useful for debugging convergence or stagnation.

- `SOLVER_MAX_SEARCH_TIME_IN_SECONDS = -1`  
  Maximum time (in seconds) allowed for solving. A value of -1 disables this limit.

## Parallelism & Resource Usage

- `SEARCH_WORKERS = -1`  
  Number of parallel workers. `-1` uses all available CPU cores.

- `MAX_NUM_WORKERS = 20`  
  Caps the number of logical worker agents for routing.

## Time Settings

- `ROUTING_TIME_RESOLUTION = "seconds"`  
  Base unit of all internal time calculations.

- `DEFAULT_SLACK_MINUTES = 120`  
  Default max wait time for a worker at a location (if no tighter constraint specified).

- `DEFAULT_TIME_TOLERANCE_MINUTES = 15`  
  Allowed violation of time window constraints before incurring penalties.

- `MAX_WORKING_TIME_MINUTES = 24*60`  
  Hard constraint on how long a worker can be assigned work during a day.

## Solver Strategies

- `DEFAULT_FIRST_SOLUTION_STRATEGY = 'PATH_CHEAPEST_ARC'`  
  OR-Tools strategy to generate the first solution using a greedy heuristic.

- `DEFAULT_LOCAL_SEARCH_METAHEURISTIC = 'GREEDY_DESCENT'`  
  Strategy to improve the solution. `GREEDY_DESCENT` stops when no improvement is found.

- `DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES = 60`  
  Default maximum solving time per instance.

- `DEFAULT_RESULT_TYPE = "fast"`  
  Selects between `fast`, `optimized`, and `best` run profiles.

- `NUM_RUNS_FOR_BEST_RESULT_TYPE = 5`  
  Number of independent solver runs to try when result type is `"best"`.

## Optimization Constraints

- `DEFAULT_NO_IMPROVEMENT_LIMIT = 100`  
  Stops optimization if no improvement has been found after this many iterations.

- `VEHICULE_DROPPING_PENALTY = 1000000`  
  High penalty applied if a worker (vehicle) is left unused.

## Clustering Heuristics

- `DEFAULT_NEIGHBORHOOD_CLUSTERING_ENABLED = True`  
  Activates a pre-processing step to cluster nearby work orders.

- `DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE = "haversine"`  
  Metric used for clustering (great-circle distance).

- `DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR = 10`  
  Extra cost multiplier applied between clusters to encourage intra-cluster assignment.

## API and Caching

- `ENABLE_DISTANCE_MATRIX_CACHE = False`  
  Enables persistent caching of routing matrices (e.g., OSRM responses).

- `ENABLE_GEOCODING_CACHE = True`  
  Enables persistent caching of geocoding results.

- `DEFAULT_GEOCODING_SERVICE = "google"`  
  Default service used for address geocoding.

## Walking Mode

- `DEFAULT_WALKING_DISTANCES_THRESHOLD = 200`  
  If the distance is below this value (meters), walking mode is used instead of driving.

## Strategy Profiles

- `FAST_FIRST_SOLUTIONS = ['UNSET', 'PARALLEL_CHEAPEST_INSERTION']`  
  Preferred heuristics for the `fast` profile.

- `FAST_METAHEURISTIC_SEARCH = ['GUIDED_LOCAL_SEARCH', 'UNSET', 'GREEDY_DESCENT']`  
  Local search methods used in fast profile.

- `OPTIMIZED_FIRST_SOLUTIONS = ['LOCAL_CHEAPEST_ARC', 'BEST_INSERTION', 'GLOBAL_CHEAPEST_ARC']`  
  First solution strategies for optimized profile.

- `OPTIMIZED_METAHEURISTIC_SEARCH = ['SIMULATED_ANNEALING', 'GENERIC_TABU_SEARCH']`  
  Advanced metaheuristics for full-scale search.

---
