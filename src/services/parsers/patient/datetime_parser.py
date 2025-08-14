"""Datetime parsing utilities for healthcare data"""

from datetime import UTC, date, datetime


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

    # see if it's iso format
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.replace(tzinfo=UTC)
    except ValueError:
        pass

    # deal with numeric formats
    # Remove any decimal parts (sometimes includes subseconds)
    if "." in dt_str:
        dt_str = dt_str.split(".")[0]

    # Handle different lengths
    try:
        parsed_dt: datetime | None = None
        match len(dt_str):
            case 14:  # Full datetime YYYYMMDDHHMMSS
                parsed_dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            case 12:  # Missing seconds YYYYMMDDHHMM
                parsed_dt = datetime.strptime(dt_str + "00", "%Y%m%d%H%M%S")
            case 10:  # Missing minutes YYYYMMDDHH
                parsed_dt = datetime.strptime(dt_str + "0000", "%Y%m%d%H%M%S")
            case 8:  # Date only YYYYMMDD
                parsed_dt = datetime.strptime(dt_str, "%Y%m%d")
            case _:
                # Try to parse as-is in case it's a different format
                # This handles edge cases we haven't seen yet
                return None

        return parsed_dt.replace(tzinfo=UTC) if parsed_dt else None
    except ValueError:
        return None


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
