from dataclasses import dataclass
from optimise.utils.geocoding import get_geolocation
from optimise.utils.dates import days_ahead_from_date, date_from_string
import logging, re
from optimise.routing.defaults import DEFAULT_SLACK_MINUTES, MAX_WORKING_TIME_MINUTES, DEFAULT_TIME_TOLERANCE_MINUTES, ROUTING_TIME_RESOLUTION, DEFAULT_DRIVING_SPEED_KMH
from optimise.utils.dates import convert_units
from typing import Dict, Any, List, Union
from datetime import datetime
from optimise.routing.defaults import *
from optimise.routing.preprocessing import handle_orders,handle_teams_and_workers
from optimise.routing.constants import translate
from optimise.routing.defaults import DEFAULT_GEOCODING_SERVICE
logging.basicConfig(level=logging.INFO)


def _coerce_int(value: Any, field: str, errors: List[str]) -> Any:
    if value is None:
        return value
    if isinstance(value, bool):
        errors.append(f"{field} must be an int")
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            errors.append(f"{field} must be an int")
            return None
    return None


def _coerce_float(value: Any, field: str, errors: List[str]) -> Any:
    if value is None:
        return value
    if isinstance(value, bool):
        errors.append(f"{field} must be a number")
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            errors.append(f"{field} must be a number")
            return None
    return None


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ["true", "1", "yes", "y"]:
            return True
        if value.lower() in ["false", "0", "no", "n"]:
            return False
    return value


@dataclass(frozen=True)
class NormalizedRequest:
    data: Dict[str, Any]

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], errors: List[str]) -> "NormalizedRequest":
        request = normalize_request(raw)
        coerce_request_types(request, errors)
        validate_json(request, errors)
        return cls(request)


def validate_json(input_json: Dict[str, Any], errors: List[str]) -> bool:
    required_keys = ['orders', 'teams', 'period_start', 'optimization_horizon']
    allowed_optimization_targets = ['duration', 'distance', 'haversine']

    if 'time_unit' not in input_json:
        raise ValueError(translate("time_unit_missing", input_json.get('language')))

    if input_json['time_unit'] not in ['hours', 'minutes']:
        raise ValueError(translate("unsupported_time_unit", input_json.get('language')).format(input_json['time_unit']))

    # Check if all required keys are present
    if not all(key in input_json for key in required_keys):
        logging.error("Missing required keys in JSON.")
        errors.append(translate("missing_required_keys", input_json.get('language')))
        raise ValueError(translate("missing_required_keys", input_json.get('language')))

    # Type checking
    if not isinstance(input_json['orders'], list):
        logging.error("'orders' should be a list.")
        errors.append(translate("orders_should_be_list", input_json.get('language')))
        raise ValueError(translate("orders_should_be_list", input_json.get('language')))

    if not isinstance(input_json['teams'], dict):
        logging.error("'teams' should be a dict.")
        errors.append(translate("teams_should_be_dict", input_json.get('language')))
        raise ValueError(translate("teams_should_be_dict", input_json.get('language')))

    # Range checking for optimization_horizon
    if not isinstance(input_json['optimization_horizon'], int) or input_json['optimization_horizon'] < 1:
        logging.error("'optimization_horizon' should be greater than 0.")
        errors.append(translate("optimization_horizon_greater", input_json.get('language')))
        raise ValueError(translate("optimization_horizon_greater", input_json.get('language')))

    # Enum validation for optimization_target
    if input_json['optimization_target'] not in allowed_optimization_targets:
        logging.error(f"'optimization_target' should be one of {allowed_optimization_targets}.")
        errors.append(translate("optimization_target", input_json.get('language')).format(allowed_optimization_targets))
        raise ValueError(translate("optimization_target", input_json.get('language')).format(allowed_optimization_targets))

    return True


def _normalize_postal_code(value: Dict[str, Any]) -> None:
    if "postal_code" not in value and "postalcode" in value:
        value["postal_code"] = value.pop("postalcode")


def normalize_request(input_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the request in-place to prevent KeyErrors later in preprocessing.
    This does not perform validation or geocoding; it only standardizes keys
    and sets safe defaults.
    """
    if not isinstance(input_json, dict):
        raise ValueError("Request must be a dict")

    request = input_json
    request.setdefault("language", "en")
    request.setdefault("date_format", "%Y-%m-%d %H:%M:%S")
    if " " not in request["date_format"]:
        request["date_format"] = f"{request['date_format']} %H:%M:%S"

    if isinstance(request.get("period_start"), str) and " " not in request["period_start"]:
        request["period_start"] = f"{request['period_start']} 00:00:00"

    # Normalize time unit to plural forms
    if "time_unit" in request:
        if request["time_unit"] in ["hour", "hours"]:
            request["time_unit"] = "hours"
        elif request["time_unit"] in ["minute", "minutes"]:
            request["time_unit"] = "minutes"

    request.setdefault("orders", [])
    request.setdefault("teams", {})
    request.setdefault("optimization_target", "duration")
    request.setdefault("account_for_priority", False)
    request.setdefault("enable_geocoding", True)
    request.setdefault("distance_matrix_method", request.get("distance_method", "osm"))
    if "deterministic" not in request and "randomize_response" not in request:
        request["deterministic"] = True
    request.setdefault("random_seed", None)
    request.setdefault("use_walking_distances_when_possible", True)
    request.setdefault("driving_speed_kmh", DEFAULT_DRIVING_SPEED_KMH)

    # Normalize depot and teams
    if "depot" in request and isinstance(request["depot"], dict):
        _normalize_postal_code(request["depot"])
    for _, team in request.get("teams", {}).items():
        if not isinstance(team, dict):
            continue
        team.setdefault("workers", [])
        if "depot" not in team:
            team["depot"] = request.get("depot", {})
        if isinstance(team.get("depot"), dict):
            _normalize_postal_code(team["depot"])

        for worker in team.get("workers", []):
            if not isinstance(worker, dict):
                continue
            _normalize_postal_code(worker)
            worker.setdefault("blocked_times", [])
            worker.setdefault("shifts", [])
            worker.setdefault("day_starts_at", "00:00:00")
            worker.setdefault("day_ends_at", "23:59:59")
            worker.setdefault("pause_starts_at", "00:00:00")
            worker.setdefault("pause_ends_at", "00:00:00")

    # Normalize orders
    for order in request.get("orders", []):
        if not isinstance(order, dict):
            continue
        _normalize_postal_code(order)
        order.setdefault("visits_schedule", [])
        order.setdefault("visiting_hour_start", "00:00:00")
        order.setdefault("visiting_hour_end", "23:59:59")
        order.setdefault("required_assignment", False)

    return request


def coerce_request_types(request: Dict[str, Any], errors: List[str]) -> None:
    request["account_for_priority"] = _coerce_bool(request.get("account_for_priority"))
    request["enable_geocoding"] = _coerce_bool(request.get("enable_geocoding"))
    if "deterministic" in request:
        request["deterministic"] = _coerce_bool(request.get("deterministic"))
    request["use_walking_distances_when_possible"] = _coerce_bool(
        request.get("use_walking_distances_when_possible")
    )
    if "randomize_response" in request:
        request["randomize_response"] = _coerce_bool(request.get("randomize_response"))
    request["max_route_distance"] = _coerce_int(
        request.get("max_route_distance"), "max_route_distance", errors
    )

    request["optimization_horizon"] = _coerce_int(request.get("optimization_horizon"), "optimization_horizon", errors)
    request["time_limit"] = _coerce_int(request.get("time_limit"), "time_limit", errors)
    request["allow_slack"] = _coerce_int(request.get("allow_slack"), "allow_slack", errors)
    request["max_working_time"] = _coerce_int(request.get("max_working_time"), "max_working_time", errors)
    request["time_interval_tolerance"] = _coerce_int(
        request.get("time_interval_tolerance"), "time_interval_tolerance", errors
    )
    request["walking_distances_threshold"] = _coerce_int(
        request.get("walking_distances_threshold"), "walking_distances_threshold", errors
    )
    request["driving_speed_kmh"] = _coerce_float(
        request.get("driving_speed_kmh"), "driving_speed_kmh", errors
    )


def process_time_settings(request, setting_name, default_value, units_per_hour):
    """
    Processes time-related settings in the request dictionary.

    :param request: The request dictionary containing the settings.
    :param setting_name: The name of the setting to process (e.g., 'allow_slack').
    :param default_value: The default value for the setting if not present in the request.
    :param units_per_hour: The conversion factor for units per hour.
    :return: None, the request dictionary is modified in place.
    """
    if setting_name not in request or request[setting_name] is None:
        request[setting_name] = convert_units(default_value, "minutes",request.get('language'), ROUTING_TIME_RESOLUTION)
    else:
        request[setting_name]=convert_units(request[setting_name], units_per_hour,request.get('language'), ROUTING_TIME_RESOLUTION)


def datetime_from_string(date_str: Union[str, datetime], time_str: str, format_string: str) -> datetime:
    """Convert a date string or datetime object and a time string into a datetime object."""
    if isinstance(date_str, datetime):
        date_str = date_str.strftime('%Y-%m-%d')  # Convert datetime object to string

    return datetime.strptime(f"{date_str} {time_str}", format_string)



def handle_time_and_date(request: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    # Converting period_start to datetime
    request['period_start'] = date_from_string(request['period_start'], format_string=request['date_format'])

    # Calculating optimization_horizon_end_date
    request['optimization_horizon_end_date'] = days_ahead_from_date(
        request['period_start'],
        request['optimization_horizon'],
        date_format=request['date_format'],
        give_datetime=True
    )

    process_time_settings(request, 'allow_slack', DEFAULT_SLACK_MINUTES, request['time_unit'])
    process_time_settings(request, 'max_working_time', MAX_WORKING_TIME_MINUTES, request['time_unit'])
    process_time_settings(request, 'time_interval_tolerance', DEFAULT_TIME_TOLERANCE_MINUTES, request['time_unit'])
    process_time_settings(request, 'time_limit', DEFAULT_OPTIMIZATION_TIME_LIMIT_MINUTES, request['time_unit'])

    if "time_limit" in request and request['time_limit'] == 0:
        request['time_limit'] = int(1e10)
        pass
    return request



def preprocess_request(request: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    """
    Main function to preprocess the optimization request JSON.
    """
    # Step 0: Normalize + coerce types + validate
    normalized = NormalizedRequest.from_raw(request, errors)
    request = normalized.data

    if "deterministic" in request:
        request["randomize_response"] = not bool(request.get("deterministic"))
    else:
        request["deterministic"] = not bool(request.get("randomize_response", False))

    if "geocoding_service" not in request:
        request["geocoding_service"] = DEFAULT_GEOCODING_SERVICE

    if 'enable_neighborhood_clustering'  not in request:
        request['enable_neighborhood_clustering'] = DEFAULT_NEIGHBORHOOD_CLUSTERING_ENABLED
    if 'neighborhood_clustering_distance' not in request:
        request['neighborhood_clustering_distance'] = DEFAULT_NEIGHBORHOOD_CLUSTERING_DISTANCE
    if 'neighborhood_clustering_penalty_factor' not in request:
        request['neighborhood_clustering_penalty_factor'] = DEFAULT_NEIGHBORHOOD_CLUSTERING_PENALTY_FACTOR

    # Step 2: Handle time and date fields in the request
    request = handle_time_and_date(request, errors)

    request['orders']=order_by_adress(request['orders'])
    # Step 3: Process Orders
    request['orders'] = handle_orders(request, errors, enable_geocoding=request.get("enable_geocoding", True))

    # Step 4: Process Workers
    request['workers'] = handle_teams_and_workers(request, errors, enable_geocoding=request.get("enable_geocoding", True))

    request['depot']['address'] = request['depot']['address'] = f"{request['depot']['street']}, {request['depot']['postal_code']} {request['depot']['city']}, {request['depot']['country']}"

    # Optionally, you can include more preprocessing steps here

    return request


def order_by_adress(list_of_orders):

    def pad_numbers(text, length):
        pattern = r'\b\d+\b'
        replacement = lambda match: str(int(match.group(0))).zfill(length)
        return re.sub(pattern, replacement, text)


    # Pad numbers in addresses for comparison

    for order in list_of_orders:
        try:
            order['padded_address'] = pad_numbers(order['street'], 4)
        except:
            return list_of_orders

    # Sort the addresses by the padded versions
    sorted_orders = sorted(list_of_orders, key=lambda x: x['padded_address'])

    for order in sorted_orders:
        del order['padded_address']

    return sorted_orders
