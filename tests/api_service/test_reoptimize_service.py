from datetime import datetime

from services.api_service.app.schemas import (
    Location,
    Objectives,
    OptimizeRequest,
    ReoptimizeChanges,
    Task,
    TimeWindow,
    Vehicle,
)
from services.api_service.app.services.reoptimize_service import apply_reoptimize_changes


def test_apply_reoptimize_changes_updates_tasks_and_vehicles():
    start = datetime(2024, 1, 1, 8, 0, 0)
    end = datetime(2024, 1, 1, 17, 0, 0)

    base = OptimizeRequest(
        problem_type="vrptw",
        objectives=Objectives(primary="minimize_total_duration"),
        vehicles=[
            Vehicle(
                id="van_1",
                start_location=Location(lat=50.8476, lng=4.3561),
                available_time_windows=[TimeWindow(start=start, end=end)],
            )
        ],
        tasks=[
            Task(
                id="task_1",
                location=Location(lat=50.8503, lng=4.3517),
                service_duration_minutes=15,
            )
        ],
    )

    changes = ReoptimizeChanges(
        removed_task_ids=["task_1"],
        added_tasks=[
            Task(
                id="task_2",
                location=Location(lat=50.8466, lng=4.3528),
                service_duration_minutes=10,
            )
        ],
        added_vehicles=[
            Vehicle(
                id="van_2",
                start_location=Location(lat=50.8476, lng=4.3561),
                available_time_windows=[TimeWindow(start=start, end=end)],
            )
        ],
    )

    updated = apply_reoptimize_changes(base, changes)
    task_ids = {task.id for task in updated.tasks}
    vehicle_ids = {vehicle.id for vehicle in updated.vehicles}

    assert task_ids == {"task_2"}
    assert vehicle_ids == {"van_1", "van_2"}
