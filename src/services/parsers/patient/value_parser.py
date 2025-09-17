"""VistA value parsing utilities"""

from typing import Any


def parse_blood_pressure(
    bp_string: str | Any,
) -> tuple[int | None, int | None]:
    """
    Parse blood pressure format "135/100" to (systolic, diastolic).

    Args:
        bp_string: Blood pressure string like "135/100"

    Returns:
        Tuple of (systolic, diastolic) or (None, None) if invalid

    Examples:
        >>> parse_blood_pressure("135/100")
        (135, 100)

        >>> parse_blood_pressure("120/80")
        (120, 80)

        >>> parse_blood_pressure("invalid")
        (None, None)
    """
    if not bp_string:
        return (None, None)

    bp_str = str(bp_string).strip()

    if "/" not in bp_str:
        return (None, None)

    parts = bp_str.split("/")
    if len(parts) != 2:
        return (None, None)

    try:
        systolic = int(parts[0].strip())
        diastolic = int(parts[1].strip())
        return (systolic, diastolic)
    except (ValueError, TypeError):
        return (None, None)
