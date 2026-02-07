import os

import pytest
import requests


OSRM_BASE = os.getenv("OSRM_BASE", "http://localhost:5000")


def _osrm_available() -> bool:
    try:
        res = requests.get(
            f"{OSRM_BASE}/route/v1/driving/4.3561,50.8476;4.3517,50.8503?overview=false",
            timeout=3,
        )
        return res.ok
    except Exception:
        return False


@pytest.mark.integration
def test_osrm_route_returns_distance_and_geometry():
    if not _osrm_available():
        pytest.skip("OSRM not available")

    res = requests.get(
        f"{OSRM_BASE}/route/v1/driving/4.3561,50.8476;4.3517,50.8503",
        params={"overview": "full", "geometries": "geojson"},
        timeout=5,
    )
    assert res.ok
    payload = res.json()
    routes = payload.get("routes", [])
    assert routes
    route = routes[0]
    assert route.get("distance", 0) > 0
    geometry = route.get("geometry", {})
    assert geometry.get("type") == "LineString"
    coords = geometry.get("coordinates", [])
    assert len(coords) >= 2
