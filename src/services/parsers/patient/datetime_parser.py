"""Datetime parsing utilities for healthcare data"""

from datetime import date, datetime


def parse_datetime(dt_value: int | str | None) -> datetime | None:
    """
    Parse datetime format YYYYMMDDHHMMSS or variants.

    Parses dates stored as integers in various formats:
    - 20240119160242 -> 2024-01-19 16:02:42 (full datetime)
    - 202401191602   -> 2024-01-19 16:02:00 (missing seconds)
    - 20240119       -> 2024-01-19 00:00:00 (date only)

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
    if dt_value is None:
        return None

    # Convert to string and clean
    dt_str = str(dt_value).strip()

    # Remove any decimal parts (sometimes includes subseconds)
    if "." in dt_str:
        dt_str = dt_str.split(".")[0]

    # Handle different lengths
    try:
        if len(dt_str) == 14:  # Full datetime YYYYMMDDHHMMSS
            return datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        elif len(dt_str) == 12:  # Missing seconds YYYYMMDDHHMM
            return datetime.strptime(dt_str + "00", "%Y%m%d%H%M%S")
        elif len(dt_str) == 10:  # Missing minutes YYYYMMDDHH
            return datetime.strptime(dt_str + "0000", "%Y%m%d%H%M%S")
        elif len(dt_str) == 8:  # Date only YYYYMMDD
            return datetime.strptime(dt_str, "%Y%m%d")
        else:
            # Try to parse as-is in case it's a different format
            # This handles edge cases we haven't seen yet
            return None
    except ValueError:
        return None


def parse_date(date_value: int | str | None) -> date | None:
    """
    Parse date format YYYYMMDD.

    This is a simpler version specifically for date-only fields.

    Args:
        date_value: Integer or string date value

    Returns:
        Parsed date or None if invalid

    Examples:
        >>> parse_date(20240119)
        datetime.date(2024, 1, 19)

        >>> parse_date("19500407")
        datetime.date(1950, 4, 7)
    """
    if date_value is None:
        return None

    date_str = str(date_value).strip()

    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d").date()
        else:
            # Might be a datetime, try the full parser
            dt = parse_datetime(date_value)
            return dt.date() if dt else None
    except ValueError:
        return None


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
