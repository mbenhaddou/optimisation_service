"""Useful things to do with dates"""
import logging
from datetime import datetime, timedelta, time
import math
from dateutil.parser import parse
logger = logging.getLogger("app")
from optimise.routing.defaults import ROUTING_TIME_RESOLUTION
from optimise.routing.constants import translate


conversion_factors = {
    'seconds': 1,
    'minutes': 60,
    'hours': 3600,
    # Add more predefined units if needed
}

def add_custom_time_unit(unit_name, seconds_per_unit):
    """ Adds a custom time unit to the conversion_factors dictionary. """
    conversion_factors[unit_name] = seconds_per_unit

def convert_units(value, from_unit, error_language:str='en',to_unit=ROUTING_TIME_RESOLUTION):
    """ Converts a time value from one unit to another. """
    if from_unit not in conversion_factors or to_unit not in conversion_factors:
        raise ValueError(translate("invalid_time_unit", error_language).format(from_unit, to_unit))


    # Convert to base unit (seconds) first
    value_in_seconds = value * conversion_factors[from_unit]

    # Convert from base unit to target unit
    return int(value_in_seconds / conversion_factors[to_unit])


def convert_time_to_app_unit(t: time) -> int:
    """
    Converts a time given in hours, minutes, and seconds to the application's time unit.
    """
    # Convert hours, minutes, and seconds to seconds

    hours, minutes, seconds = t.hour, t.minute, t.second

    total_seconds = hours * 3600 + minutes * 60 + seconds

    # Now convert the total seconds to the application's time unit
    return convert_units(total_seconds, 'seconds', 'en', ROUTING_TIME_RESOLUTION)




def format_time_as_hours_minutes(time_value, time_unit=ROUTING_TIME_RESOLUTION):
    """
    Formats a given time value in a specified unit to a 'hours:minutes' format.
    """
    # Convert the time value to minutes
    #TODO add language
    minutes = convert_units(time_value, time_unit, 'en',"minutes")

    # Extract hours and remaining minutes
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)

    # Format and return the time in 'hours:minutes' format
    return "{:02d}:{:02d}".format(hours, remaining_minutes)



def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def date_from_string(string, format_string=None,return_datetime=True ):
    """Runs through a few common string formats for datetimes,
    and attempts to coerce them into a datetime. Alternatively,
    format_string can provide either a single string to attempt
    or an iterable of strings to attempt."""
    formats_string = [
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]
    if isinstance(format_string, str):
        formats_string.insert(0, format_string)






    for format in formats_string:
        try:
            if return_datetime:
                return datetime.strptime(string, format)
            else:
                return datetime.strptime(string, format).date()
        except ValueError:
            try:
                parsed = parse(string)
                return parsed if return_datetime else parsed.date()
            except ValueError:
                continue

    raise ValueError("Could not produce date from string: {}".format(string))


def to_datetime(plain_date, hours=0, minutes=0, seconds=0, ms=0):
    """given a datetime.date, gives back a datetime"""
    # don't mess with datetimes
    if isinstance(plain_date, datetime):
        return plain_date
    return datetime(
        plain_date.year,
        plain_date.month,
        plain_date.day,
        hours,
        minutes,
        seconds,
        ms,
    )


def days_ago(days, give_datetime=True):
    delta = timedelta(days=days)
    dt = datetime.now() - delta
    if give_datetime:
        return dt
    else:
        return dt.date()


def days_ahead(days, give_datetime=True):
    delta = timedelta(days=days)
    dt = datetime.now() + delta
    if give_datetime:
        return dt
    else:
        return dt.date()


def days_ahead_from_date(date, days, date_format, give_datetime=True):
    date_t=date
    if isinstance(date, str):
        date_t=date_from_string(date, date_format)
    elif not isinstance(date, datetime):
        raise Exception("the given date parameter is not a string of a datetime")
    delta = timedelta(days=days)
    dt = date_t + delta
    if give_datetime:
        return dt
    else:
        return dt.date()


def datetime_to_integer(date_time, error_language:str='en', date_format='%d-%m-%Y %H:%M:%S', day_min_unit=ROUTING_TIME_RESOLUTION, intra_day=False):
    if day_min_unit == 'hours':
        intra_day_intervals = 24
    elif day_min_unit == 'minutes':
        intra_day_intervals = 24 * 60
    elif day_min_unit == 'seconds':
        intra_day_intervals = 86400
    else:
        raise ValueError(translate("unsupported_day_min_unit", error_language).format(",".join(['hours', 'minutes','seconds']),day_min_unit))
    if isinstance(date_time, str):
        dt = datetime.strptime(date_time, date_format)
    elif isinstance(date_time, datetime):
        dt = date_time
    else:
        raise ValueError(translate("date_value_should_be_datetime_or_string", error_language))
    year = dt.year
    month = dt.month
    day = dt.day

    remaining_day = (dt.minute * 60 + dt.hour * 60 * 60 + dt.second) / 86400.0

    weekday = 0
    if not intra_day:
        weekday = datetime(year, month, day).date().weekday()

    if intra_day_intervals is None:
        return weekday
    else:
        return int((weekday + remaining_day) * intra_day_intervals)

def integer_to_datetime(num_integer, reference_date, day_min_unit=ROUTING_TIME_RESOLUTION, date_format='%d-%m-%Y %H:%M:%S'):
    """Convert integer return from solver to readable date for logging or visualization.

    Args:
        num_integer (_type_): _description_
        within_day (bool, optional): _description_. Defaults to True.
        num_hours_per_day (_type_, optional): _description_. Defaults to HOURS_PER_DAY_MODEL.
        start_hour_of_day (int, optional): _description_. Defaults to 0.

    Returns:
        string: _description_
    """

    if day_min_unit=='minutes':
        day_units=24*60
    elif day_min_unit=='hours':
        day_units=24
    elif day_min_unit=='seconds':
        day_units=86400
    day = math.floor(num_integer / day_units)
    plus_number = num_integer % day_units


    if day_min_unit=='minutes':
        plus_number=plus_number*60
    elif day_min_unit=='hours':
        plus_number=plus_number*60*60


    minutes, seconds = divmod(plus_number, 60)

    hours, minutes = divmod(minutes, 60)





    new_date= date_from_string(reference_date, date_format)
    new_date = new_date + timedelta(days=day, hours=hours, minutes=minutes,seconds=seconds)


    return new_date


def minutes_to_date_elements(num_minutes):
    days = 0
    hours = 0
    mins = 0

    time = num_minutes
    days = math.floor(time / 1440)
    leftover_minutes = time % 1440
    hours, mins = divmod(leftover_minutes, 60)
#    mins = time - (days * 1440) - (hours * 60)
    return days, hours, mins

def check_time_interval(start: int, end: int, error_language:str='en'):
    """Check if a time interval is valid."""
    if start > end:
        raise ValueError(translate("error_in_time_interval", error_language).format(start, end))

def add_time_with_max_end_of_day(original_time, additional_seconds=0):

    arbitrary_date = datetime(2000, 1, 1)
    # Convert time to datetime
    original_datetime = datetime.combine(arbitrary_date, original_time)

    # Add the duration
    new_datetime = original_datetime + timedelta(seconds=additional_seconds)

    # Check if the new datetime exceeds the end of the day
    if new_datetime.date() == arbitrary_date.date():
        return new_datetime.time()
    else:
        return time(23, 59, 59)


def time_to_integer(dt: time, error_language:str='en',date_format='%H:%M:%S', day_min_unit="minutes", intra_day=False,) -> int:
    if day_min_unit == 'minutes':
        return dt.hour * 60 + dt.minute
    elif day_min_unit == 'seconds':
        return dt.hour * 60 * 60 + dt.minute * 60 + dt.second
    # Add more units if needed
    else:
        raise ValueError(translate("unsupported_day_min_unit", error_language).format(",".join(['minutes','seconds']),day_min_unit))
if __name__ == "__main__":
    num=days_ahead_from_date("02-09-2022 16:20:00", 4, date_format='%d-%m-%Y %H:%M:%S')
    print(num)
    s=time_to_integer(time(16,20,0), "fr", day_min_unit='hours')
    print(s)
#    print(integer_to_datetime(num, reference_date="29-08-2022 00:00:00", day_min_unit='hours'))
