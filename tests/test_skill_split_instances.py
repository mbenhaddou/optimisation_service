from optimise.routing.data_model import get_optimisation_instances
from optimise.routing.preprocessing.preprocess_request import preprocess_request


def _skill_payload():
    return {
        "language": "en",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "time_unit": "minutes",
        "optimization_target": "duration",
        "optimization_horizon": 1,
        "period_start": "2024-01-01 08:00:00",
        "enable_geocoding": False,
        "distance_matrix_method": "haversine",
        "orders": [
            {
                "id": "WO-A",
                "skill": "A",
                "priority": 1,
                "latitude": 50.0,
                "longitude": 4.0,
                "visits_schedule": [],
                "visiting_hour_start": "08:00:00",
                "visiting_hour_end": "17:00:00",
                "work_hours": 30,
                "street": "Street 1",
                "postal_code": "1000",
                "city": "City",
                "country": "BE",
                "earliest_start_date": "2024-01-01",
                "earliest_start_time": "08:00:00",
                "latest_end_date": "2024-01-01",
                "latest_end_time": "17:00:00",
                "earliest_machine_availability_date": "2024-01-01",
                "earliest_machine_availability_time": "08:00:00",
                "latest_machine_availability_date": "2024-01-01",
                "latest_machine_availability_time": "17:00:00",
                "spare_part_available_date": "2024-01-01",
                "spare_part_available_time": "08:00:00",
                "must_start_date": "",
                "must_start_time": "",
                "must_end_date": "",
                "must_end_time": "",
            },
            {
                "id": "WO-B",
                "skill": "B",
                "priority": 1,
                "latitude": 50.001,
                "longitude": 4.001,
                "visits_schedule": [],
                "visiting_hour_start": "08:00:00",
                "visiting_hour_end": "17:00:00",
                "work_hours": 30,
                "street": "Street 2",
                "postal_code": "1000",
                "city": "City",
                "country": "BE",
                "earliest_start_date": "2024-01-01",
                "earliest_start_time": "08:00:00",
                "latest_end_date": "2024-01-01",
                "latest_end_time": "17:00:00",
                "earliest_machine_availability_date": "2024-01-01",
                "earliest_machine_availability_time": "08:00:00",
                "latest_machine_availability_date": "2024-01-01",
                "latest_machine_availability_time": "17:00:00",
                "spare_part_available_date": "2024-01-01",
                "spare_part_available_time": "08:00:00",
                "must_start_date": "",
                "must_start_time": "",
                "must_end_date": "",
                "must_end_time": "",
            },
        ],
        "teams": {
            "TeamA": {
                "depot": {
                    "id": "DEPOT-1",
                    "street": "Depot",
                    "postal_code": "1000",
                    "city": "City",
                    "country": "BE",
                    "latitude": 50.0,
                    "longitude": 4.0,
                },
                "workers": [
                    {
                        "e_id": "W-A",
                        "skills": ["A"],
                        "street": "Worker A",
                        "postal_code": "1000",
                        "city": "City",
                        "country": "BE",
                        "latitude": 50.0,
                        "longitude": 4.0,
                        "blocked_times": [],
                        "shifts": [],
                        "day_starts_at": "08:00:00",
                        "day_ends_at": "17:00:00",
                        "pause_starts_at": "12:00:00",
                        "pause_ends_at": "12:30:00",
                    }
                ],
            },
            "TeamB": {
                "depot": {
                    "id": "DEPOT-1",
                    "street": "Depot",
                    "postal_code": "1000",
                    "city": "City",
                    "country": "BE",
                    "latitude": 50.0,
                    "longitude": 4.0,
                },
                "workers": [
                    {
                        "e_id": "W-B",
                        "skills": ["B"],
                        "street": "Worker B",
                        "postal_code": "1000",
                        "city": "City",
                        "country": "BE",
                        "latitude": 50.0,
                        "longitude": 4.0,
                        "blocked_times": [],
                        "shifts": [],
                        "day_starts_at": "08:00:00",
                        "day_ends_at": "17:00:00",
                        "pause_starts_at": "12:00:00",
                        "pause_ends_at": "12:30:00",
                    }
                ],
            },
        },
        "depot": {
            "id": "DEPOT-1",
            "street": "Depot",
            "postal_code": "1000",
            "city": "City",
            "country": "BE",
            "latitude": 50.0,
            "longitude": 4.0,
        },
    }


def test_instances_split_by_skill():
    errors = []
    request = preprocess_request(_skill_payload(), errors)
    instances = get_optimisation_instances(request)

    assert errors == []
    assert len(instances) == 2

    for instance in instances:
        instance.init_instance(instance.period_start)
        assert all(wo.skill == instance.name for wo in instance.work_orders)
        assert all(instance.name in worker.skills for worker in instance.workers)
