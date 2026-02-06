from typing import Any, Dict

from ..config import settings


def ensure_mapping_defaults(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.mapping_service_url:
        return payload

    # If the caller didn't specify a matrix method, prefer OSRM (mapping service)
    if "distance_matrix_method" not in payload and "distance_method" not in payload:
        payload = dict(payload)
        payload["distance_matrix_method"] = "osrm"
    return payload
