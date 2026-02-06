from optimise.utils.dates import convert_units, datetime_to_integer, integer_to_datetime


def test_convert_units_minutes_to_seconds():
    assert convert_units(2, "minutes", "en", "seconds") == 120


def test_datetime_integer_roundtrip_seconds():
    num = datetime_to_integer(
        "2024-01-01 10:30:00",
        date_format="%Y-%m-%d %H:%M:%S",
        day_min_unit="seconds",
        intra_day=True,
    )
    dt = integer_to_datetime(
        num,
        "2024-01-01 00:00:00",
        day_min_unit="seconds",
        date_format="%Y-%m-%d %H:%M:%S",
    )
    assert dt.hour == 10
    assert dt.minute == 30
