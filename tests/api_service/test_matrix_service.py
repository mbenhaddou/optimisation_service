from services.api_service.app.services.matrix_service import build_matrix


def test_build_matrix_haversine():
    coords = [[50.847, 4.355], [50.8503, 4.3517]]
    result = build_matrix(coords, method="haversine", driving_speed_kmh=30)
    assert len(result["distances"]) == 2
    assert len(result["durations"]) == 2
    assert result["distances"][0][0] == 0
    assert result["durations"][0][1] > 0
