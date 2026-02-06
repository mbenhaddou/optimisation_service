#!/usr/bin/env python3
"""Print active configuration values with optional secret masking."""

import argparse
import re
from typing import Any, Dict

import config.defaults as app_config
from optimise.routing import defaults as routing_defaults


SENSITIVE_TOKENS = ("KEY", "PASSWORD", "SECRET", "TOKEN")


def _is_sensitive(name: str) -> bool:
    return any(token in name.upper() for token in SENSITIVE_TOKENS)


def _mask_value(value: Any) -> Any:
    if value is None:
        return None
    s = str(value)
    if len(s) <= 4:
        return "*" * len(s)
    return f"{s[:2]}{'*' * (len(s) - 4)}{s[-2:]}"


def _sanitize_uri(value: str) -> str:
    if value is None:
        return value
    # Mask password in URI like mysql://user:pass@host/db
    return re.sub(r"://([^:]+):([^@]+)@", r"://\\1:****@", value)


def _build_app_config(show_secrets: bool) -> Dict[str, Any]:
    data = {
        "ROUTING_ENGINE": app_config.ROUTING_ENGINE,
        "GEOLOC_NOMINATIM_USER_AGENT": app_config.GEOLOC_NOMINATIM_USER_AGENT,
        "GOOGLE_API_KEY": app_config.GOOGLE_API_KEY,
        "GEOLOC_OPENCAGE_API_KEY": app_config.GEOLOC_OPENCAGE_API_KEY,
        "MAPBOX_OSRM_API_KEYS": app_config.MAPBOX_OSRM_API_KEYS,
        "ORS_API_KEYS": app_config.ORS_API_KEYS,
        "GRAPHHOPPER_API_KEYS": app_config.GRAPHHOPPER_API_KEYS,
        "RATE_LIMIT": app_config.RATE_LIMIT,
        "MYSQL_SERVER": app_config.MYSQL_SERVER,
        "MYSQL_USER": app_config.MYSQL_USER,
        "MYSQL_PASSWORD": app_config.MYSQL_PASSWORD,
        "MYSQL_DB": app_config.MYSQL_DB,
        "SQLALCHEMY_DATABASE_URI": app_config.SQLALCHEMY_DATABASE_URI,
        "SOLUTION_ROUTING_STATUS_DESC": app_config.SOLUTION_ROUTING_STATUS_DESC,
        "SOLUTION_ROUTING_FROM_DATE_DESC": app_config.SOLUTION_ROUTING_FROM_DATE_DESC,
        "SOLUTION_ROUTING_TO_DATE_DESC": app_config.SOLUTION_ROUTING_TO_DATE_DESC,
        "SOLUTION_ROUTING_INCLUDE_REQUEST_DESC": app_config.SOLUTION_ROUTING_INCLUDE_REQUEST_DESC,
        "SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC": app_config.SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC,
    }

    if show_secrets:
        return data

    masked = {}
    for key, value in data.items():
        if key == "SQLALCHEMY_DATABASE_URI":
            masked[key] = _sanitize_uri(value)
        elif _is_sensitive(key):
            masked[key] = _mask_value(value)
        else:
            masked[key] = value
    return masked


def _build_routing_config() -> Dict[str, Any]:
    return {
        "ENABLE_DISTANCE_MATRIX_CACHE": routing_defaults.ENABLE_DISTANCE_MATRIX_CACHE,
        "DISTANCE_MATRIX_CACHE_DIR": routing_defaults.DISTANCE_MATRIX_CACHE_DIR,
        "ENABLE_GEOCODING_CACHE": routing_defaults.ENABLE_GEOCODING_CACHE,
        "GEOLOC_CACHE_BACKEND": routing_defaults.GEOLOC_CACHE_BACKEND,
        "GEOLOC_LOCAL_CACHE_DIR": routing_defaults.GEOLOC_LOCAL_CACHE_DIR,
        "DEFAULT_DRIVING_SPEED_KMH": routing_defaults.DEFAULT_DRIVING_SPEED_KMH,
        "DEFAULT_WALKING_DISTANCES_THRESHOLD": routing_defaults.DEFAULT_WALKING_DISTANCES_THRESHOLD,
        "DEFAULT_GEOCODING_SERVICE": routing_defaults.DEFAULT_GEOCODING_SERVICE,
        "USE_NEW_SOLVER": routing_defaults.USE_NEW_SOLVER,
        "SOLVER_LOG_SEARCH_PROGRESS": routing_defaults.SOLVER_LOG_SEARCH_PROGRESS,
        "SOLVER_MAX_SEARCH_TIME_IN_SECONDS": routing_defaults.SOLVER_MAX_SEARCH_TIME_IN_SECONDS,
        "SEARCH_WORKERS": routing_defaults.SEARCH_WORKERS,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Print active configuration values.")
    parser.add_argument("--show-secrets", action="store_true", help="Print secrets in full.")
    args = parser.parse_args()

    print("APP CONFIG")
    for k, v in _build_app_config(args.show_secrets).items():
        print(f"{k}={v}")

    print("\nROUTING CONFIG")
    for k, v in _build_routing_config().items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
