from __future__ import annotations

from typing import Dict, List, Optional

from optimise.routing.defaults import DEFAULT_DRIVING_SPEED_KMH
from optimise.routing.distance_matrix import get_distance_matrix_with_retry
from optimise.utils.haversine_distance import haversine_distance_matrix


def build_matrix(
    coords_latlon: List[List[float]],
    method: str = "haversine",
    driving_speed_kmh: Optional[float] = None,
    routing_engine_url: Optional[str] = None,
) -> Dict[str, List[List[float]]]:
    if not coords_latlon:
        return {"distances": [], "durations": []}

    if method == "osrm":
        coords_lonlat = [[lon, lat] for lat, lon in coords_latlon]
        previous_engine = None
        if routing_engine_url:
            import os

            previous_engine = os.environ.get("ROUTING_ENGINE")
            os.environ["ROUTING_ENGINE"] = routing_engine_url
        try:
            result = get_distance_matrix_with_retry(coords_lonlat, router_name="osrm")
        finally:
            if routing_engine_url:
                import os

                if previous_engine is None:
                    os.environ.pop("ROUTING_ENGINE", None)
                else:
                    os.environ["ROUTING_ENGINE"] = previous_engine
        return {"distances": result["distances"], "durations": result["durations"]}

    distances = haversine_distance_matrix(coords_latlon)
    speed_kmh = driving_speed_kmh or DEFAULT_DRIVING_SPEED_KMH
    speed_mps = (speed_kmh * 1000) / 3600.0 if speed_kmh else 0.0
    durations = [
        [
            (float(dist) / speed_mps if speed_mps > 0 else 0.0)
            for dist in row
        ]
        for row in distances
    ]
    return {"distances": distances, "durations": durations}
