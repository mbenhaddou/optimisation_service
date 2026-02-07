import logging
from datetime import datetime, time, timedelta, date
from typing import Dict, Any, List

from optimise.utils.geocoding import get_geolocation, address_str
from optimise.utils.dates import date_from_string
from optimise.routing.constants import translate
from optimise.routing.defaults import DEFAULT_GEOCODING_SERVICE

logger = logging.getLogger("app")


def convert_visiting_hours_to_time(order: Dict[str, Any], request: Dict[str, Any]) -> None:
    if order.get("visiting_hour_start") in ["0", "", None]:
        order["visiting_hour_start"] = "00:00:00"
    if order.get("visiting_hour_end") in ["0", "", None]:
        order["visiting_hour_end"] = "23:59:59"
    order["visiting_hour_start"] = date_from_string(
        order["visiting_hour_start"], request["date_format"].split()[1]
    ).time()
    order["visiting_hour_end"] = date_from_string(
        order["visiting_hour_end"], request["date_format"].split()[1]
    ).time()
    visits_schedule = order.get("visits_schedule") or []
    order["visits_schedule"] = visits_schedule
    for visiting_time in visits_schedule:
        visiting_time["visit_date"] = date_from_string(
            visiting_time["visit_date"], format_string=request["date_format"].split()[0]
        ).date()
        visiting_time["visit_start"] = date_from_string(
            visiting_time["visit_start"], format_string=request["date_format"].split()[1]
        ).time()
        visiting_time["visit_end"] = date_from_string(
            visiting_time["visit_end"], request["date_format"].split()[1]
        ).time()


def set_and_geolocate_address(
    order_or_worker: Dict[str, Any],
    geolocation_service: str = DEFAULT_GEOCODING_SERVICE,
    enable_geocoding: bool = True,
) -> None:
    address_dict = {
        "street": order_or_worker.get("street", ""),
        "city": order_or_worker.get("city", ""),
        "country": order_or_worker.get("country", ""),
        "postalcode": order_or_worker.get("postal_code", ""),
    }

    if not order_or_worker.get("address"):
        order_or_worker["address"] = address_str(address_dict)
    elif not any(address_dict.values()):
        # Fall back to using the existing address string as the street
        address_dict["street"] = order_or_worker["address"]

    has_coords = isinstance(order_or_worker.get("longitude"), (float, int)) and isinstance(
        order_or_worker.get("latitude"), (float, int)
    )
    if has_coords:
        return
    if not enable_geocoding:
        raise ValueError("Missing latitude/longitude and geocoding is disabled")

    order_or_worker.update(get_geolocation(address_dict, geolocation_service))


def validate_priority(order: Dict[str, Any], error_language: str = "en") -> None:
    if not (1 <= order["priority"] <= 5):
        raise Exception(
            translate("order_priority_between", error_language).format(order["id"], order["priority"])
        )


def validate_order_fields(order: Dict[str, Any], error_language: str = "en", require_coordinates: bool = False) -> None:
    required_fields = ["street", "postal_code", "city", "country", "priority", "skill", "visits_schedule"]
    if "longitude" in order and "latitude" in order:
        required_fields = ["skill", "visits_schedule"]
    if require_coordinates:
        required_fields.append("latitude")
        required_fields.append("longitude")
    for field in required_fields:
        if field not in order:
            raise ValueError(translate("missing_order_field", error_language).format(field))


def str_to_date(date_str: str, format: str = "%Y-%m-%d") -> date:
    return datetime.strptime(date_str, format).date()


def str_to_time(time_str: str, format: str = "%H:%M:%S") -> time:
    return datetime.strptime(time_str, format).time()


def convert_str_to_date_time(
    order: Dict[str, Any], key_date: str, key_time: str, format_date: str, format_time: str
) -> None:
    if key_date in order and order[key_date] not in ["0", "", None]:
        order[key_date] = str_to_date(order[key_date], format_date)
    if key_time in order and order[key_time] not in ["0", "", None]:
        order[key_time] = str_to_time(order[key_time], format_time)


def set_default_values(
    order: Dict[str, Any], key_date: str, key_time: str, default_date: date, default_time: time
) -> None:
    if order.get(key_date) in ["0", "", None]:
        order[key_date] = default_date
    if order.get(key_time) in ["0", "", None]:
        order[key_time] = default_time


def combine_date_time(order: Dict[str, Any], key_date: str, key_time: str) -> datetime:
    return datetime.combine(order[key_date], order[key_time])


def handle_order_datetime_operations(order: Dict[str, Any], request: Dict[str, Any], errors=None) -> None:
    if errors is None:
        errors = []

    period_start = request["period_start"]
    optimization_horizon = request["optimization_horizon"]
    date_format = request["date_format"].split()[0]
    time_format = request["date_format"].split()[1]

    for key in [
        "latest_end",
        "latest_machine_availability",
        "earliest_machine_availability",
        "earliest_start",
        "spare_part_available",
        "must_start",
        "must_end",
    ]:
        convert_str_to_date_time(order, f"{key}_date", f"{key}_time", date_format, time_format)

    future_date = period_start + timedelta(days=optimization_horizon)

    set_default_values(order, "latest_end_date", "latest_end_time", future_date, time(23, 59, 59))
    set_default_values(
        order,
        "latest_machine_availability_date",
        "latest_machine_availability_time",
        future_date,
        time(23, 59, 59),
    )
    set_default_values(
        order,
        "earliest_machine_availability_date",
        "earliest_machine_availability_time",
        period_start,
        time(0, 0, 0),
    )
    set_default_values(order, "earliest_start_date", "earliest_start_time", period_start, time(0, 0, 0))
    set_default_values(
        order,
        "spare_part_available_date",
        "spare_part_available_time",
        period_start,
        time(0, 0, 0),
    )

    order["earliest_start_datetime"] = combine_date_time(order, "earliest_start_date", "earliest_start_time")
    order["latest_end_datetime"] = combine_date_time(order, "latest_end_date", "latest_end_time")
    order["earliest_machine_availability_datetime"] = combine_date_time(
        order, "earliest_machine_availability_date", "earliest_machine_availability_time"
    )
    order["latest_machine_availability_datetime"] = combine_date_time(
        order, "latest_machine_availability_date", "latest_machine_availability_time"
    )

    order["must_start_datetime"] = (
        None
        if order.get("must_start_date") in ["0", "", None]
        else combine_date_time(order, "must_start_date", "must_start_time")
    )
    order["must_end_datetime"] = (
        None
        if order.get("must_end_date") in ["0", "", None]
        else combine_date_time(order, "must_end_date", "must_end_time")
    )

    preferred_start = order.get("preferred_time_window_start")
    preferred_end = order.get("preferred_time_window_end")
    if isinstance(preferred_start, datetime):
        order["preferred_time_window_start_datetime"] = preferred_start
    elif preferred_start not in ["0", "", None]:
        order["preferred_time_window_start_datetime"] = date_from_string(
            preferred_start, request["date_format"]
        )

    if isinstance(preferred_end, datetime):
        order["preferred_time_window_end_datetime"] = preferred_end
    elif preferred_end not in ["0", "", None]:
        order["preferred_time_window_end_datetime"] = date_from_string(
            preferred_end, request["date_format"]
        )

    if order["latest_end_datetime"] < order["earliest_start_datetime"]:
        order["latest_end_datetime"] = order["earliest_start_datetime"]

    try:
        if order["must_start_datetime"] and order["must_start_datetime"] > order["latest_end_datetime"]:
            raise ValueError(translate("must_start_datetime_conflict", request.get("language")))
    except Exception as e:
        logger.error("Error processing order %s: %s", order.get("id", "unknown"), str(e))
        errors.append(
            translate("error_processing_order", request.get("language")).format(order.get("id", "unknown"), str(e))
        )
        raise


def handle_orders(request: Dict[str, Any], errors=None, enable_geocoding: bool = True) -> List[Dict[str, Any]]:
    if errors is None:
        errors = []

    order_skills = set()
    for order in request["orders"]:
        if request.get("account_for_priority"):
            validate_priority(order, error_language=request.get("language"))
        try:
            validate_order_fields(
                order,
                error_language=request.get("language"),
                require_coordinates=not enable_geocoding,
            )
        except Exception as e:
            errors.append(
                translate("error_processing_order", request.get("language")).format(order.get("id", "unknown"), str(e))
            )
            continue
        if order.get("preferred_time_windows") and not order.get("preferred_time_window_start"):
            preferred_window = order["preferred_time_windows"][0]
            order["preferred_time_window_start"] = preferred_window.get("start")
            order["preferred_time_window_end"] = preferred_window.get("end")
        convert_visiting_hours_to_time(order, request)
        set_and_geolocate_address(
            order,
            request.get("geocoding_service", DEFAULT_GEOCODING_SERVICE),
            enable_geocoding=enable_geocoding,
        )
        try:
            handle_order_datetime_operations(order, request, errors)
            order_skills.add(order["skill"])
        except Exception:
            raise

    request["orders_skills"] = order_skills
    return request["orders"]
