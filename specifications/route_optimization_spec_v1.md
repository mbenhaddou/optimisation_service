# Route Optimization Specification - Version 1 (Foundation)
**Version:** 1.0  
**Date:** February 2026  
**Status:** Draft (Incremental Release)

## Goal
Deliver a functional optimization API with a usable portal UI for early adopters. This version focuses on core VRP capabilities, clear error handling, and a minimal but complete product loop.

## Scope Summary
Version 1 includes the core optimization endpoint, basic constraints, basic objectives, and a foundational portal UI with an API playground and a simple route planner.

## API - Version 1
### Endpoints
- `POST /v1/optimize` for synchronous optimization.
- `GET /health` and `GET /ready` for service status.
- `GET /metrics` for basic operational metrics.

### Request Model (Supported Fields)
- `problem_type` supports `tsp`, `vrp`, `vrptw`.
- `vehicles` supports `id`, `start_location`, `end_location`, `available_time_windows`, `breaks`, `max_tasks`.
- `tasks` supports `id`, `type`, `location`, `service_duration_minutes`, `time_windows`, `demand` (weight only), `priority`.
- `constraints` supports `max_route_duration_minutes`, `max_route_distance_km`, `balance_routes`, `allow_overtime`.
- `objectives` supports `primary` and `secondary` with weights for `duration`, `distance`, `cost`.
- `optimization` supports `max_computation_time_seconds` and `solution_quality`.
- `options` supports `return_detailed_metrics`, `include_route_geometry`.

### Response Model
- `status`, `computation_time_ms`, `solution_quality_score`.
- `routes` with `vehicle_id`, `total_distance_km`, `total_duration_minutes`, `stops`.
- `unassigned_tasks` with `task_id`, `reason`, `details`.
- `metrics` with totals and average utilization (weight only).
- `warnings` for tight time windows and low slack.

### Error Handling
- Standard error envelope with `code`, `message`, `details`, `request_id`, and `timestamp`.
- Supported codes: `INVALID_REQUEST`, `AUTHENTICATION_FAILED`, `AUTHORIZATION_FAILED`, `INFEASIBLE_SOLUTION`, `TIMEOUT`, `INTERNAL_ERROR`.

### Auth & Security
- API key required via `Authorization: Bearer <api_key>`.
- Basic roles: `Admin`, `Developer`.
- Rate limiting enforced with `RATE_LIMIT_EXCEEDED`.

## UI - Version 1
### Portal Navigation
- Authentication, Workspace, Dashboard, Route Planner, API Tools, Settings.

### Authentication
- Registration screen (email, password, organization).
- Login screen (email, password).
- Basic password validation and error messages.

### Workspace
- Workspace selector (single org at start).
- Workspace profile summary (name, org id).

### Dashboard
- Quick stats cards for active routes, tasks, requests, and cost.
- Recent activity feed.
- Map placeholder panel.

### Route Planner
- 3-step wizard: Problem setup, Tasks/Vehicles, Run Optimization.
- Minimal constraints toggles.
- Results view with route list and summary metrics.

### API Tools
- API Playground for `/v1/optimize`.
- JSON request editor with validation.
- Response inspector with formatted JSON.

### Settings
- Profile view.
- API key management list and create action.
 - Workspace profile details (read-only).

## Out of Scope (Deferred to V2+)
- `/v1/matrix`, `/v1/reoptimize`, `/v1/analytics/routes`.
- Multi-objective optimization beyond basic weights.
- Advanced constraints (skills, capacities beyond weight, dependencies, zones).
- Alternative solutions and carbon footprint.
- Full analytics dashboards and data management screens.

## Acceptance Criteria
- A user can submit a valid optimization request and receive routes and metrics.
- The portal can run an optimization and display results without errors.
- Errors are returned with the standardized error format.
