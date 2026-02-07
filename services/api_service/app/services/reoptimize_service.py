from __future__ import annotations

from typing import Dict, List, Optional

from ..schemas import OptimizeRequest, ReoptimizeChanges, Task, Vehicle


def _merge_items_by_id(items: List, updates: Optional[List]) -> List:
    if not updates:
        return list(items)
    items_by_id = {item.id: item for item in items}
    for update in updates:
        items_by_id[update.id] = update
    return list(items_by_id.values())


def apply_reoptimize_changes(
    base_request: OptimizeRequest,
    changes: Optional[ReoptimizeChanges],
) -> OptimizeRequest:
    if changes is None:
        return base_request

    tasks: List[Task] = list(base_request.tasks)
    vehicles: List[Vehicle] = list(base_request.vehicles)

    if changes.removed_task_ids:
        tasks = [task for task in tasks if task.id not in changes.removed_task_ids]
    tasks = _merge_items_by_id(tasks, changes.updated_tasks)
    if changes.added_tasks:
        tasks = _merge_items_by_id(tasks, changes.added_tasks)

    if changes.removed_vehicle_ids:
        vehicles = [v for v in vehicles if v.id not in changes.removed_vehicle_ids]
    vehicles = _merge_items_by_id(vehicles, changes.updated_vehicles)
    if changes.added_vehicles:
        vehicles = _merge_items_by_id(vehicles, changes.added_vehicles)

    return OptimizeRequest(
        problem_type=base_request.problem_type,
        objectives=base_request.objectives,
        vehicles=vehicles,
        tasks=tasks,
        depots=base_request.depots,
        matrix=base_request.matrix,
        constraints=changes.constraints or base_request.constraints,
        traffic=base_request.traffic,
        optimization=changes.optimization or base_request.optimization,
        options=changes.options or base_request.options,
        routing=changes.routing or base_request.routing,
    )
