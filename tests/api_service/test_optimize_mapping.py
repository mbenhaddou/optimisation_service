from datetime import datetime

from services.api_service.app.schemas import (
    Depot,
    Location,
    OptimizeRequest,
    Objectives,
    PrecomputedMatrix,
    Task,
    TimeWindow,
    Vehicle,
)
from services.api_service.app.services.optimize_service import build_legacy_request


def test_build_legacy_request_with_depot_and_skills():
    start = datetime(2024, 1, 1, 8, 0, 0)
    end = datetime(2024, 1, 1, 17, 0, 0)

    request = OptimizeRequest(
        problem_type="vrptw",
        objectives=Objectives(primary="minimize_total_duration"),
        depots=[
            Depot(
                id="brussels_depot",
                location=Location(lat=50.8476, lng=4.3561, address="Depot"),
                time_windows=[TimeWindow(start=start, end=end)],
            )
        ],
        vehicles=[
            Vehicle(
                id="van_1",
                start_location=Location(lat=50.8476, lng=4.3561),
                available_time_windows=[TimeWindow(start=start, end=end)],
                skills=["delivery"],
                depot_id="brussels_depot",
            )
        ],
        tasks=[
            Task(
                id="task_1",
                location=Location(lat=50.8503, lng=4.3517),
                service_duration_minutes=15,
                required_skills=["delivery"],
            )
        ],
    )

    legacy = build_legacy_request(request)
    assert legacy.legacy_request["distance_matrix_method"] in {"haversine", "osrm"}
    assert legacy.legacy_request["depot"]["id"] == "brussels_depot"
    assert legacy.legacy_request["orders"][0]["skill"] == "delivery"


def test_build_legacy_request_groups_vehicles_by_team():
    start = datetime(2024, 1, 1, 8, 0, 0)
    end = datetime(2024, 1, 1, 17, 0, 0)

    request = OptimizeRequest(
        problem_type="vrptw",
        objectives=Objectives(primary="minimize_total_duration"),
        vehicles=[
            Vehicle(
                id="van_1",
                start_location=Location(lat=50.8476, lng=4.3561),
                available_time_windows=[TimeWindow(start=start, end=end)],
                team_id="alpha",
            ),
            Vehicle(
                id="van_2",
                start_location=Location(lat=50.8476, lng=4.3561),
                available_time_windows=[TimeWindow(start=start, end=end)],
                team_id="alpha",
            ),
        ],
        tasks=[
            Task(
                id="task_1",
                location=Location(lat=50.8503, lng=4.3517),
                service_duration_minutes=15,
            )
        ],
    )

    legacy = build_legacy_request(request)
    teams = legacy.legacy_request["teams"]
    assert len(teams) == 1
    team = next(iter(teams.values()))
    assert len(team["workers"]) == 2


def test_build_legacy_request_includes_preferred_window_penalty():
    start = datetime(2024, 1, 1, 8, 0, 0)
    end = datetime(2024, 1, 1, 17, 0, 0)
    preferred_start = datetime(2024, 1, 1, 10, 0, 0)
    preferred_end = datetime(2024, 1, 1, 12, 0, 0)

    request = OptimizeRequest(
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
                time_windows=[TimeWindow(start=start, end=end)],
                preferred_time_windows=[
                    TimeWindow(start=preferred_start, end=preferred_end)
                ],
                soft_time_window_penalty=12.5,
            )
        ],
    )

    legacy = build_legacy_request(request)
    order = legacy.legacy_request["orders"][0]
    assert order["preferred_time_window_start"].startswith("2024-01-01")
    assert order["soft_time_window_penalty"] == 12.5


def test_build_legacy_request_includes_precomputed_matrix():
    request = OptimizeRequest(
        problem_type="vrptw",
        objectives=Objectives(primary="minimize_total_duration"),
        vehicles=[
            Vehicle(
                id="van_1",
                start_location=Location(lat=50.8476, lng=4.3561),
            )
        ],
        tasks=[
            Task(
                id="task_1",
                location=Location(lat=50.8503, lng=4.3517),
                service_duration_minutes=15,
            )
        ],
        matrix=PrecomputedMatrix(
            distances_m=[[0, 100], [100, 0]],
            durations_s=[[0, 60], [60, 0]],
        ),
    )

    legacy = build_legacy_request(request)
    assert legacy.legacy_request["precomputed_distance_matrix"] == [[0, 100], [100, 0]]
    assert legacy.legacy_request["precomputed_time_matrix"] == [[0, 60], [60, 0]]
