"""Parsers for converting Vista RPC responses to structured data"""

import logging
from datetime import datetime

from ....models.vista.admin import User

logger = logging.getLogger(__name__)


def parse_fileman_date(fm_date: str) -> str | None:
    """
    Convert FileMan date to ISO 8601 format

    FileMan format: YYYMMDD.HHMMSS where YYY = Year - 1700

    Args:
        fm_date: FileMan date string

    Returns:
        ISO 8601 formatted date string or None if invalid
    """
    if not fm_date or fm_date == "0":
        return None

    try:
        # Handle date with time
        if "." in fm_date:
            date_part, time_part = fm_date.split(".", 1)
        else:
            date_part = fm_date
            time_part = "000000"

        # Parse date
        if len(date_part) >= 7:
            year = int(date_part[:3]) + 1700
            month = int(date_part[3:5])
            day = int(date_part[5:7])

            # Parse time
            hour = int(time_part[:2]) if len(time_part) >= 2 else 0
            minute = int(time_part[2:4]) if len(time_part) >= 4 else 0
            second = int(time_part[4:6]) if len(time_part) >= 6 else 0

            dt = datetime(year, month, day, hour, minute, second)
            return dt.isoformat()

    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse FileMan date '{fm_date}': {e}")

    return None


def parse_user_info(result: str | dict, duz: str) -> User | None:
    """
    Parse user information from various RPCs

    Handles both JSON and delimited formats
    """
    if not result:
        return None

    # Handle JSON response
    if isinstance(result, dict):
        return User(
            duz=result.get("duz", duz),
            name=result.get("name", ""),
            title=result.get("title"),
            service=result.get("service"),
            phone=result.get("phone"),
            email=result.get("email"),
            role=result.get("role"),
            station=result.get("station"),
        )

    # Handle delimited response (ORWU USERINFO format)
    # Format: DUZ^NAME^TITLE^SERVICE^PHONE
    elif isinstance(result, str):
        parts = result.strip().split("^")
        if len(parts) >= 2:
            return User(
                duz=parts[0] if parts[0] else duz,
                name=parts[1],
                title=parts[2] if len(parts) > 2 else None,
                service=parts[3] if len(parts) > 3 else None,
                phone=parts[4] if len(parts) > 4 else None,
            )

    return None
