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


def format_lab_type(type_name: str) -> str:
    """Convert lab type name to snake_case.

    Args:
        type_name: The lab type name from VistA

    Returns:
        Formatted lab type in snake_case
    """
    if not type_name:
        return "unknown"

    # Common lab types that need special formatting
    lab_type_map = {
        "GLUCOSE": "glucose",
        "HEMOGLOBIN": "hemoglobin",
        "HEMATOCRIT": "hematocrit",
        "WBC": "wbc",
        "RBC": "rbc",
        "PLATELET COUNT": "platelet_count",
        "SODIUM": "sodium",
        "POTASSIUM": "potassium",
        "CHLORIDE": "chloride",
        "CO2": "co2",
        "BUN": "bun",
        "CREATININE": "creatinine",
        "CALCIUM": "calcium",
        "TOTAL PROTEIN": "total_protein",
        "ALBUMIN": "albumin",
        "BILIRUBIN": "bilirubin",
        "ALT": "alt",
        "AST": "ast",
        "CHOLESTEROL": "cholesterol",
        "TRIGLYCERIDES": "triglycerides",
        "HDL": "hdl",
        "LDL": "ldl",
        "TSH": "tsh",
        "T4": "t4",
        "T3": "t3",
        "HBA1C": "hba1c",
        "PSA": "psa",
        "INR": "inr",
        "PT": "pt",
        "PTT": "ptt",
    }

    # Check if we have a specific mapping
    normalized = type_name.upper()
    if normalized in lab_type_map:
        return lab_type_map[normalized]

    # Otherwise, convert to snake_case
    return type_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")


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
