# Route Optimization Specification - Version 2 (Expansion)
**Version:** 2.0  
**Date:** February 2026  
**Status:** Draft (Incremental Release)

## Goal
Add advanced constraints, re-optimization, matrix service, and deeper UI workflows. Version 2 expands the solver capabilities and makes the portal usable for daily operations.

## Scope Summary
Version 2 builds on Version 1 and introduces the matrix service, re-optimization, advanced constraints, alternative solutions, and richer portal screens.

## API - Version 2
### New Endpoints
- `POST /v1/matrix` for distance and duration matrices.
- `POST /v1/reoptimize` for real-time adjustments.

### Expanded Request Model
- `vehicles.capacity` supports `weight`, `volume`, `units`.
- `vehicles.skills` and `tasks.required_skills` enforced.
- `vehicles.team_id` groups multiple vehicles under a single team (shared depot and roster).
- `tasks.type` supports `pickup`, `delivery`, `service`, `pickup_delivery`.
- `tasks.preferred_time_windows` plus `soft_time_window_penalty` are enforced as soft constraints.
- `constraints` supports `task_dependencies`, `required_task_assignments`, `zone_restrictions`.
- `objectives` supports multi-objective weighting and `minimize_vehicles`.
- `optimization` supports `return_alternative_solutions`.
- `options` supports `calculate_carbon_footprint`.

### Expanded Response Model
- `alternative_solutions` with `quality_score` and summary fields.
- `metrics` includes carbon footprint when enabled.
- `warnings` include constraint risk flags and near-capacity alerts.

### Re-optimization
- Accepts solution ID and incremental changes.
- Supports minimizing route changes and preserving assignments.

## UI - Version 2
### Route Planner Enhancements
- Tasks tab with priority and skills.
- Vehicles tab with capacities, skills, team grouping, and cost fields.
- Constraints tab with zones and dependencies.
- Advanced options for solution quality and alternatives.
 - Soft preferred time window inputs with penalty guidance.

### Results Visualization
- Route map with per-vehicle color coding.
- Alternative solution comparison table.
- Unassigned tasks panel with reasons.

### API Tools Enhancements
- Request Builder for `/v1/optimize`, `/v1/matrix`, `/v1/reoptimize`.
- Code snippet generator for cURL, Python, and JavaScript.

### Data Management (Basic)
- Locations library list view.
- Fleet management list view.

### Live Routes (Basic)
- Active optimization list.
- Re-optimization console entry point.

### Workspace & Registration (Expanded)
- Registration and login flows polish (validation, success states).
- Workspace switcher (multi-org ready, even if limited initially).
- Basic team member list (read-only) and role labels.

## Out of Scope (Deferred to V3)
- `/v1/analytics/routes`.
- Predictive analytics and demand forecasting.
- OAuth2 and enterprise RBAC.
- Full reporting and export workflows.
- In-app help system and onboarding tours.

## Acceptance Criteria
- Users can calculate a matrix and reuse it for optimization.
- Users can reoptimize with adds/removals and see change summaries.
- Portal supports advanced constraints and displays alternative solutions.
