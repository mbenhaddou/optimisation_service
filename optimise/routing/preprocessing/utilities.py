
from datetime import datetime, time
from typing import Union


def extract_datetime_format(datetime_format: str) -> tuple:
    """
    Extract the date and time format from a given datetime format string.

    Parameters:
    - datetime_format (str): The datetime format string (e.g., '%Y-%m-%d %H:%M:%S')

    Returns:
    - tuple: A tuple containing the extracted date format and time format.
    """
    # Split the datetime format into date and time parts based on the space
    date_format, time_format = datetime_format.split(' ', 1)

    return date_format, time_format

def combine_date_and_time(date: Union[datetime, str], time_str: Union[time, str], date_format="%Y-%m-%d") -> datetime:
    """
    Combine a datetime object with a time string.

    Parameters:
    - date (datetime): The datetime object containing the date.
    - time_str (str): The time string in "HH:MM:SS" date_format.

    Returns:
    - datetime: A new datetime object with the date from the first parameter and the time from the second.
    """

    date_format, time_format=extract_datetime_format(date_format)
    #if date is a string, convert to datetime
    if isinstance(date, str):
        date = datetime.strptime(date, date_format)

    if isinstance(time_str, time):
        new_time = time_str
    elif isinstance(time_str, str):
        # Split the time string and convert to integers
        time_parts = [int(x) for x in time_str.split(":")]

        # Create a datetime.time object
        new_time = time(time_parts[0], time_parts[1], time_parts[2])
    else:
        raise TypeError("time_str must be a string or a time object.")


    if isinstance(date, datetime):
        date = date.date()

    # Combine the date from the datetime object with the new time
    return datetime.combine(date, new_time)