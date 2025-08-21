"""VistA value parsing utilities"""

from typing import Any

from ..mappings import (
    extract_route,
    extract_timing,
    get_medication_mappings,
    normalize_frequency,
    validate_status,
)


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
    if not value or value in ["", "-", "N/A", "PENDING", "EXPIRED"]:
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


def parse_medication_dosage(
    dosage_str: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Parse medication dosage into strength, form, and unit.

    Examples:
        "500MG TAB" -> ("500", "MG", "TAB")
        "10MG/5ML SYRUP" -> ("10/5", "MG/ML", "SYRUP")
        "INSULIN 100UNITS/ML VIAL" -> ("100", "UNITS/ML", "VIAL")

    Args:
        dosage_str: Raw dosage string from medication name

    Returns:
        Tuple of (strength, unit, form) or None for each if not found
    """
    import re

    if not dosage_str:
        return (None, None, None)

    dosage_upper = dosage_str.upper()

    # Get medication forms from centralized mappings
    forms = get_medication_mappings()["medication_forms"]

    # Extract form
    form = None
    for f in forms:
        if f in dosage_upper:
            form = f
            break

    # Extract strength and unit with regex - handle complex patterns
    # First try compound patterns like "10MG/5ML"
    compound_pattern = r"(\d+(?:\.\d+)?)(MG|MCG|ML|GM|UNITS?|%)/(\d+(?:\.\d+)?)(ML|TAB|MG|MCG|GM|UNITS?|%)"
    compound_match = re.search(compound_pattern, dosage_upper)

    if compound_match:
        # Handle compound strengths like "10MG/5ML"
        num1 = compound_match.group(1)
        unit1 = compound_match.group(2)
        num2 = compound_match.group(3)
        unit2 = compound_match.group(4)

        strength = f"{num1}/{num2}"
        unit = f"{unit1}/{unit2}"
        return (strength, unit, form)

    # Try patterns like "100UNITS/ML" (no number after slash)
    unit_slash_pattern = (
        r"(\d+(?:\.\d+)?)(MG|MCG|ML|GM|UNITS?)/(ML|TAB|MG|MCG|GM|UNITS?|%)"
    )
    unit_slash_match = re.search(unit_slash_pattern, dosage_upper)

    if unit_slash_match:
        # Handle patterns like "100UNITS/ML"
        strength = unit_slash_match.group(1)
        unit1 = unit_slash_match.group(2)
        unit2 = unit_slash_match.group(3)
        unit = f"{unit1}/{unit2}"
        return (strength, unit, form)

    # If no compound pattern, try simple patterns like "500MG" or "100UNITS"
    simple_pattern = r"(\d+(?:\.\d+)?)(MG|MCG|ML|GM|UNITS?|%)"
    simple_match = re.search(simple_pattern, dosage_upper)

    if simple_match:
        strength = simple_match.group(1)
        unit = simple_match.group(2)
        return (strength, unit, form)

    return (None, None, form)


def extract_frequency_from_sig(sig: str) -> str | None:
    """
    Extract frequency code from SIG instructions using centralized patterns.

    This function is used by both the Medication model and other parsers
    to ensure consistent frequency extraction.

    Args:
        sig: SIG instruction string

    Returns:
        Frequency code (e.g., 'BID', 'TID', 'PRN') or None if not found
    """
    # Use centralized mapping system
    from ..mappings import MappingLoader

    loader = MappingLoader()
    return loader.extract_frequency_from_sig(sig)


def normalize_medication_frequency(frequency: str) -> str:
    """
    Normalize medication frequency to standard format using centralized mappings.

    Args:
        frequency: Raw frequency string (e.g., "BID", "twice daily", "q12h")

    Returns:
        Normalized frequency string

    Examples:
        >>> normalize_medication_frequency("BID")
        "twice daily"

        >>> normalize_medication_frequency("Q8H")
        "three times daily"

        >>> normalize_medication_frequency("PRN")
        "as needed"
    """
    return normalize_frequency(frequency)


def validate_medication_status(status: str) -> str:
    """
    Validate and normalize medication status using centralized mappings.

    Args:
        status: Raw status string

    Returns:
        Normalized status string (ACTIVE, DISCONTINUED, COMPLETED, PENDING)
    """
    return validate_status(status, "medication")


def extract_medication_instructions(sig: str) -> dict[str, str | bool | None]:
    """
    Extract structured information from SIG instructions using centralized mappings.

    Args:
        sig: Raw SIG/instructions string

    Returns:
        Dictionary with extracted information (route, frequency, timing, etc.)
    """
    if not sig:
        return {}

    from ..mappings import MappingLoader

    loader = MappingLoader()

    extracted: dict[str, str | bool | None] = {}

    # Extract route using centralized mapping
    route = extract_route(sig)
    if route:
        extracted["route"] = route

    # Extract timing using centralized mapping
    timing = extract_timing(sig)
    if timing:
        extracted["timing"] = timing

    # Extract special instructions using centralized mapping
    special_instructions = loader.extract_special_instructions(sig)
    extracted.update(special_instructions)

    return extracted


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
    Clean and standardize specimen type using centralized mappings.

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
    from ..mappings import MappingLoader

    loader = MappingLoader()
    return loader.clean_specimen_type(specimen)
