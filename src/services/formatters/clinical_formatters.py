"""Formatters for clinical data types."""


def format_vital_type(type_name: str) -> str:
    """Convert vital type name to snake_case.

    Args:
        type_name: The vital type name from VistA

    Returns:
        Formatted vital type in snake_case
    """
    vital_type_map = {
        "BLOOD PRESSURE": "blood_pressure",
        "PULSE OXIMETRY": "pulse_oximetry",
        "TEMPERATURE": "temperature",
        "RESPIRATION": "respiration",
        "PULSE": "pulse",
        "WEIGHT": "weight",
        "HEIGHT": "height",
        "PAIN": "pain",
        "BMI": "bmi",
    }
    return vital_type_map.get(type_name.upper(), type_name.lower().replace(" ", "_"))


def format_service_name(service: str) -> str:
    """Convert service name to proper case.

    Args:
        service: The service name from VistA

    Returns:
        Formatted service name in proper case
    """
    if not service:
        return "unknown"

    # Special cases that need specific formatting
    service_map = {
        "CARDIOLOGY": "Cardiology",
        "COM-CARE CARDIOLOGY": "Community Care Cardiology",
        "AUDIOLOGY OUTPATIENT": "Audiology Outpatient",
        "AUDIOLOGY": "Audiology",
        "DERMATOLOGY": "Dermatology",
        "ENDOCRINOLOGY": "Endocrinology",
        "GASTROENTEROLOGY": "Gastroenterology",
        "HEMATOLOGY": "Hematology",
        "INFECTIOUS DISEASE": "Infectious Disease",
        "NEPHROLOGY": "Nephrology",
        "NEUROLOGY": "Neurology",
        "ONCOLOGY": "Oncology",
        "OPHTHALMOLOGY": "Ophthalmology",
        "ORTHOPEDICS": "Orthopedics",
        "PSYCHIATRY": "Psychiatry",
        "PULMONARY": "Pulmonary",
        "RHEUMATOLOGY": "Rheumatology",
        "UROLOGY": "Urology",
    }

    # Check if we have a specific mapping
    normalized = service.upper()
    if normalized in service_map:
        return service_map[normalized]

    # Otherwise, convert to title case
    return " ".join(word.capitalize() for word in service.split())
