"""VistA value parsing utilities"""

from typing import Any


def parse_numeric_result(value: Any) -> float | None:
    """
    Parse mixed numeric/string results from VistA.

    VistA lab results and vitals can be:
    - Numbers: 180, 98.7, 1.5
    - Strings: "180", "98.7", ".9", ">100", "<0.5"
    - Special values that should return None

    Args:
        value: Raw value from VistA

    Returns:
        Parsed float value or None if not numeric

    Examples:
        >>> parse_numeric_result(180)
        180.0

        >>> parse_numeric_result("98.7")
        98.7

        >>> parse_numeric_result(".9")
        0.9

        >>> parse_numeric_result(">100")
        100.0

        >>> parse_numeric_result("PENDING")
        None
    """
    if value is None:
        return None

    # Already a number
    if isinstance(value, int | float):
        return float(value)

    # Convert to string and clean
    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    # Empty or non-numeric indicators
    if not value or value in ["", "-", "N/A", "PENDING", "CANCELLED"]:
        return None

    # Remove comparison operators
    cleaned = value.lstrip(">").lstrip("<").lstrip("=").strip()

    # Handle leading decimal point
    if cleaned.startswith("."):
        cleaned = "0" + cleaned

    # Try to parse
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


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


def parse_reference_range(high: Any, low: Any) -> tuple[float | None, float | None]:
    """
    Parse reference range values from VistA.

    Reference ranges can be:
    - Numbers: high=110, low=60
    - Strings: high="110", low="60"
    - Blood pressure format: high="140/90", low="90/60"
    - Missing/invalid: returns None

    Args:
        high: High reference value
        low: Low reference value

    Returns:
        Tuple of (high, low) as floats, or None for each if invalid

    Examples:
        >>> parse_reference_range(110, 60)
        (110.0, 60.0)

        >>> parse_reference_range("110", "60")
        (110.0, 60.0)

        >>> parse_reference_range("140/90", "90/60")
        (None, None)
    """
    high_val = parse_numeric_result(high)
    low_val = parse_numeric_result(low)

    # Special handling for blood pressure ranges
    if high and "/" in str(high):
        high_val = None
    if low and "/" in str(low):
        low_val = None

    return (high_val, low_val)


def is_value_abnormal(
    value: float, high: float | None, low: float | None
) -> str | None:
    """
    Determine if a value is abnormal based on reference range.

    Args:
        value: The numeric value to check
        high: High reference limit
        low: Low reference limit

    Returns:
        'H' if high, 'L' if low, None if normal or no range

    Examples:
        >>> is_value_abnormal(180, 110, 60)
        'H'

        >>> is_value_abnormal(50, 110, 60)
        'L'

        >>> is_value_abnormal(90, 110, 60)
        None
    """
    if high is not None and value > high:
        return "H"
    if low is not None and value < low:
        return "L"
    return None


def clean_specimen_type(specimen: Any) -> str | None:
    """
    Clean and standardize specimen type.

    Args:
        specimen: Raw specimen value from VistA

    Returns:
        Cleaned specimen type or None

    Examples:
        >>> clean_specimen_type("SERUM")
        'SERUM'

        >>> clean_specimen_type("BLOOD  ")
        'BLOOD'

        >>> clean_specimen_type("")
        None
    """
    if not specimen:
        return None

    cleaned = str(specimen).strip().upper()

    if cleaned in ["", "-", "N/A"]:
        return None

    return cleaned
