# Technical Documentation – Routing Optimization Solution

## 1. Technical Architecture of the Solution (Diagrams, Data Flow, Interactions, ...)

### 1.1 Architecture Diagram

- Python backend using Google OR-Tools for optimization
- Key modules:
  - `data_model.py`: input parsing and instance creation
  - `base_routing.py`: core OR-Tools optimization engine
  - `functions.py`: evaluators and constraints
  - `parallel_routing.py`: multi-day and multi-run orchestration
- Integration with:
  - External services (Google Maps, OSRM, etc.)
  - Database (SolutionRouting persistence layer)
- 📌 See the attached UML diagram for class-level architecture and interactions.

### 1.2 Data Flow

1. JSON input specifying orders, workers, schedules, and constraints
2. Instance creation based on required skillsets
3. Optimization run using OR-Tools
4. Output generation and conversion to serializable `Solution` object
5. Result aggregation per day and per worker

### 1.3 Main Interactions

- `data_model.py`: Validates request and builds instances
- `functions.py`: Adds constraints and evaluators to OR-Tools
- `monitoring.py`: Detects stagnation or cycling during optimization
- `parallel_routing.py`: Handles orchestration and strategy control

---

## 2. API Documentation

| API               | Purpose                  | Protocol | API Key Required |
| ----------------- | ------------------------ | -------- | ---------------- |
| OSRM              | Duration/Distance matrix | HTTP     | No               |
| Google Maps       | Geocoding and durations  | HTTP     | Yes              |
| GraphHopper / ORS | Fallback routing APIs    | HTTP     | Yes              |

- Retry logic handled via `backoff`
- Caching layer via `diskcache`

---

## 3. Source Code Structure

### Main Components

- `RoutingOptimizer`: Core class wrapping the OR-Tools solver
- `create_time_evaluator()`: Callback that defines cost function
- `add_capacity_constraints()`: Adds time-based constraints
- `add_time_window_constraints()`: Adds time windows
- `NoImprovementMonitor`: Early stopping mechanism

### Logical Flow

- One `Instance` per skill
- Supports multiple parallel runs
- Handles multi-day scheduling

---

## 4. Configuration and Parameters

### Configuration Files

- `defaults.py`: Solver strategies, limits, penalties
- `.env`: API credentials

### Key Parameters

- `DEFAULT_FIRST_SOLUTION_STRATEGY`
- `DEFAULT_LOCAL_SEARCH_METAHEURISTIC`
- `DEFAULT_TIME_TOLERANCE_MINUTES`
- `NUM_RUNS_FOR_BEST_RESULT_TYPE`

---

## 5. Heuristic Algorithm Overview

- **Initial Solution**: `PATH_CHEAPEST_ARC`, `PARALLEL_CHEAPEST_INSERTION`
- **Local Search**: `GUIDED_LOCAL_SEARCH`, `SIMULATED_ANNEALING`
- **Soft Constraints**: priority penalties, flexible time bounds
- **Penalties**: dropped jobs, unused vehicles

---

## 6. Geolocation Handling

- Hybrid routing matrix with walking + driving: `create_combined_time_matrix()`
- Threshold: `DEFAULT_WALKING_DISTANCES_THRESHOLD`
- Walking time calculated using 5km/h default
- Otherwise uses standard driving matrix

---

## 7. Database Structure

### Main Entities

- `WorkOrder`: task ID, priority, time window, skill required
- `Worker`: ID, skillset, schedule, depot
- `Instance`: container for optimization problem
- `SolutionRouting`: persisted result per run

> ✅ An ERD diagram can be generated if needed.

---

## 8. Error & Alert Handling

- Messages defined in `constants.py` (multi-language)
- Central dispatcher: `translate(code, language)`
- Handles:
  - Missing fields
  - Time window inconsistencies
  - API or router initialization failures
  - Invalid depot or skills

---

## 9. Development Environment

### Tools & Libraries

- Python 3.10+
- Google OR-Tools
- `requests`, `backoff`, `numpy`, `diskcache`

### Config Files

- `.env`: API keys
- `defaults.py`

### Build Instructions

```bash
pip install -r requirements.txt
python -m optimise.routing.parallel_routing
```

---

## 10. Third-Party Integrations

| Service           | Role                 | Documentation                                                            |
| ----------------- | -------------------- | ------------------------------------------------------------------------ |
| Google Maps       | Geocoding & Duration | [https://developers.google.com/maps](https://developers.google.com/maps) |
| OSRM              | Local routing server | [https://project-osrm.org/docs](https://project-osrm.org/docs)           |
| GraphHopper / ORS | Alternative routers  | [https://graphhopper.com/api/](https://graphhopper.com/api/)             |

- Automatic fallback logic
- Router priority configured dynamically

---
