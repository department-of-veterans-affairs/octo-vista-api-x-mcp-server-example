"""Datetime parsing utilities for healthcare data"""

import re
from datetime import UTC, date, datetime

DT_MATCHER = re.compile(
    r"^(?P<year>\d{4})(?P<month>0[1-9]|1[0-2])?(?P<day>0[1-9]|[12][0-9]|3[01])?(?P<hour>[01][0-9]|2[0-3])?(?P<minute>[0-5][0-9])?(?P<second>[0-5][0-9])?"
)


def parse_datetime(dt_value: int | str | datetime | None) -> datetime | None:
    """
    Parse datetime ISO format and YYYYMMDDHHMMSS or variants.

    Parses dates stored as integers in various formats:
    - 20240119160242 -> 2024-01-19 16:02:42 (full datetime)
    - 202401191602   -> 2024-01-19 16:02:00 (missing seconds)
    - 20240119       -> 2024-01-19 00:00:00 (date only)
    - 2002           -> 2002-01-01 00:00:00 (date only)

    Args:
        dt_value: Integer or string datetime value

    Returns:
        Parsed datetime or None if invalid

    Examples:
        >>> parse_datetime(20240119160242)
        datetime.datetime(2024, 1, 19, 16, 2, 42)

        >>> parse_datetime("202401191602")
        datetime.datetime(2024, 1, 19, 16, 2, 0)

        >>> parse_datetime(20240119)
        datetime.datetime(2024, 1, 19, 0, 0)
    """
    if dt_value is None or isinstance(dt_value, datetime):
        return dt_value

    # Convert to string and clean
    dt_str = str(dt_value).strip()

    # see if it's iso format
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.replace(tzinfo=UTC)
    except ValueError:
        pass

    # use regex to extract year, month, day, hour, minute, second, ignore .subseconds
    match = DT_MATCHER.match(dt_str)
    if not match:
        return None

    yyyy = int(year_part) if ((year_part := match.group("year")) is not None) else 1970
    mm = int(month_part) if ((month_part := match.group("month")) is not None) else 1
    dd = int(day_part) if ((day_part := match.group("day")) is not None) else 1
    hh = int(hour_part) if ((hour_part := match.group("hour")) is not None) else 0
    mins = (
        int(minute_part) if ((minute_part := match.group("minute")) is not None) else 0
    )
    secs = (
        int(second_part) if ((second_part := match.group("second")) is not None) else 0
    )
    return datetime(yyyy, mm, dd, hh, mins, secs, tzinfo=UTC)


def parse_date(date_value: int | str | None) -> date | None:
    """Pasre various VistA date formats. because this is complex, use parse_datetime and extract the date part."""
    return dt.date() if (dt := parse_datetime(date_value)) else None


def format_datetime(dt: datetime | None) -> int | None:
    """
    Format datetime to integer format.

    Args:
        dt: Python datetime or None

    Returns:
        Integer format YYYYMMDDHHMMSS or None

    Example:
        >>> format_datetime(datetime(2024, 1, 19, 16, 2, 42))
        20240119160242
    """
    if dt is None:
        return None
    return int(dt.strftime("%Y%m%d%H%M%S"))


def format_date(dt: datetime | date | None) -> int | None:
    """
    Format datetime/date to date format.

    Args:
        dt: Python datetime, date, or None

    Returns:
        Integer format YYYYMMDD or None

    Example:
        >>> format_date(datetime(2024, 1, 19))
        20240119
    """
    if dt is None:
        return None
    return int(dt.strftime("%Y%m%d"))
