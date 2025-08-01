"""Clinical data validation and categorization utilities with JSON-based configuration"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# =============================================================================
# HEALTH FACTOR VALIDATION FUNCTIONS
# =============================================================================


# Cache the config to avoid repeated file reads
@lru_cache(maxsize=1)
def _load_health_factor_config() -> dict[str, Any]:
    """Load health factor configuration from JSON file."""
    config_path = Path(__file__).parent / "health_factor_config.json"
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to minimal config if file not found
        return {
            "categories": {"other": {"keywords": [], "priority": 999}},
            "severity": {"unknown": {"keywords": [], "multiplier": 1.0}},
            "risk_scoring": {"moderate": {"keywords": [], "base_score": 5}},
            "modifiable_indicators": [],
            "monitoring_indicators": [],
        }


def parse_boolean(value: Any) -> bool:
    """Parse various boolean representations.

    Args:
        value: Value to parse as boolean

    Returns:
        Boolean representation of the value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.upper() in ["TRUE", "YES", "Y", "1", "ON"]
    return bool(value)


def categorize_health_factor(category: str, factor_name: str) -> str:
    """
    Categorize health factor by type using JSON configuration.

    Args:
        category: The category name from VistA (e.g., "VA-COVID-19 [C]")
        factor_name: The factor name (e.g., "VA-COVID-19 SUSPECTED")

    Returns:
        Category type: "lifestyle", "environmental", "genetic", "medical", "screening", "other"
    """
    if not category and not factor_name:
        return "unknown"

    config = _load_health_factor_config()
    combined_text = f"{category} {factor_name}".lower()

    # Sort categories by priority (lower number = higher priority)
    categories = sorted(
        config["categories"].items(), key=lambda x: x[1].get("priority", 999)
    )

    # Check each category in priority order
    for category_name, category_config in categories:
        keywords = category_config.get("keywords", [])
        if any(keyword in combined_text for keyword in keywords):
            return category_name

    return "other"


def normalize_health_factor_severity(
    category: str, factor_name: str, severity: str | None
) -> str:
    """
    Normalize health factor severity using JSON configuration.

    Args:
        category: The category name from VistA
        factor_name: The factor name
        severity: Current severity (may be None)

    Returns:
        Normalized severity: "mild", "moderate", "severe", "unknown"
    """
    config = _load_health_factor_config()

    # First check if explicit severity is provided
    if severity:
        severity_lower = severity.lower()
        for level_name, _level_config in config["severity"].items():
            if level_name in severity_lower:
                return level_name

    # Infer severity from factor name/category
    combined_text = f"{category} {factor_name}".lower()

    # Check severity levels in order: severe, moderate, mild
    severity_order = ["severe", "moderate", "mild"]
    for level_name in severity_order:
        if level_name in config["severity"]:
            keywords = config["severity"][level_name].get("keywords", [])
            if any(keyword in combined_text for keyword in keywords):
                return level_name

    return "unknown"


def calculate_health_factor_risk_score(
    category: str, factor_name: str, severity: str
) -> int:
    """
    Calculate risk score using JSON configuration.

    Args:
        category: The category name from VistA
        factor_name: The factor name
        severity: Normalized severity level

    Returns:
        Risk score from 0 (no risk) to 10 (highest risk)
    """
    config = _load_health_factor_config()
    combined_text = f"{category} {factor_name}".lower()

    # Default base score
    base_score = 5

    # Determine base score from risk categories (high -> moderate -> low priority)
    risk_order = ["high", "moderate", "low"]
    for risk_level in risk_order:
        if risk_level in config["risk_scoring"]:
            keywords = config["risk_scoring"][risk_level].get("keywords", [])
            if any(keyword in combined_text for keyword in keywords):
                base_score = config["risk_scoring"][risk_level].get("base_score", 5)
                break

    # Apply severity multiplier
    severity_multiplier = 1.0
    if severity in config["severity"]:
        severity_multiplier = config["severity"][severity].get("multiplier", 1.0)

    final_score = int(base_score * severity_multiplier)

    # Ensure score is within bounds
    return max(0, min(10, final_score))


def is_modifiable_health_factor(
    risk_category: str, factor_name: str, category: str
) -> bool:
    """
    Check if health factor is modifiable using JSON configuration.

    Args:
        risk_category: The computed risk category
        factor_name: The factor name
        category: The original category from VistA

    Returns:
        True if the factor is modifiable
    """
    config = _load_health_factor_config()
    indicators = config.get("modifiable_indicators", [])

    combined_text = f"{risk_category} {factor_name} {category}".lower()
    return any(indicator in combined_text for indicator in indicators)


def requires_monitoring(factor_name: str, category: str) -> bool:
    """
    Check if health factor requires monitoring using JSON configuration.

    Args:
        factor_name: The factor name
        category: The category from VistA

    Returns:
        True if the factor requires monitoring
    """
    config = _load_health_factor_config()
    indicators = config.get("monitoring_indicators", [])

    combined_text = f"{factor_name} {category}".lower()
    return any(indicator in combined_text for indicator in indicators)


def get_health_factor_trends(
    health_factors: list[Any], factor_name: str
) -> dict[str, Any]:
    """
    Analyze trends for a specific health factor over time.

    Args:
        health_factors: List of HealthFactor objects
        factor_name: Name of the factor to analyze

    Returns:
        Dictionary with trend analysis
    """
    matching_factors = [
        f for f in health_factors if factor_name.lower() in f.factor_name.lower()
    ]

    if not matching_factors:
        return {"trend": "no_data", "count": 0}

    # Sort by date
    matching_factors.sort(key=lambda f: f.recorded_date)

    # Basic trend analysis
    count = len(matching_factors)
    first_date = matching_factors[0].recorded_date
    last_date = matching_factors[-1].recorded_date

    # Check if it's recurring (multiple entries)
    is_recurring = count > 1

    # Check severity progression using risk scores
    severity_scores = [f.risk_score for f in matching_factors]
    trend = "stable"

    if len(severity_scores) > 1:
        if severity_scores[-1] > severity_scores[0]:
            trend = "worsening"
        elif severity_scores[-1] < severity_scores[0]:
            trend = "improving"

    return {
        "trend": trend,
        "count": count,
        "first_recorded": first_date.isoformat(),
        "last_recorded": last_date.isoformat(),
        "is_recurring": is_recurring,
        "severity_progression": severity_scores,
        "current_severity": matching_factors[-1].severity_level,
        "current_risk_score": matching_factors[-1].risk_score,
    }


def get_available_categories() -> list[str]:
    """Get list of available health factor categories from configuration."""
    config = _load_health_factor_config()
    return list(config.get("categories", {}).keys())


def get_available_severity_levels() -> list[str]:
    """Get list of available severity levels from configuration."""
    config = _load_health_factor_config()
    return list(config.get("severity", {}).keys())


def add_custom_keywords(category_type: str, level: str, keywords: list[str]) -> None:
    """
    Runtime method to extend keywords (for future extensibility).
    Note: This would require more sophisticated config management for persistence.

    Args:
        category_type: Type of category ("categories", "severity", "risk_scoring")
        level: Specific level within the category type
        keywords: List of keywords to add
    """
    # This is a placeholder for future dynamic keyword management
    # Would require config persistence mechanism
    pass


# =============================================================================
# DIAGNOSIS-SPECIFIC VALIDATION FUNCTIONS
# =============================================================================


def validate_icd_code(icd_code: str, icd_version: str) -> bool:
    """
    Validate ICD code format (ICD-9 or ICD-10).

    Args:
        icd_code: The ICD code to validate
        icd_version: "ICD-9" or "ICD-10"

    Returns:
        True if code format is valid
    """
    import re

    if not icd_code or not icd_version:
        return False

    icd_code = icd_code.strip().upper()

    if icd_version.upper() == "ICD-10":
        # ICD-10 format: Letter + 2-3 digits + optional decimal + alphanumeric extensions
        # Examples: A01, B95.1, C78.00, Z51.11, W21.00XD, S72.001A
        pattern = r"^[A-Z]\d{2,3}(\.[0-9A-Z]{1,4})?$"
        return re.match(pattern, icd_code) is not None

    elif icd_version.upper() == "ICD-9":
        # ICD-9 format: 3-5 digits with optional decimal, or V/E codes with 2-5 digits
        # Examples: 250, 250.0, 401.9, V58.69 (V + 2 digits), E879.3 (E + 3 digits)
        pattern = r"^([VE]\d{2,5}|\d{3,5})(\.\d{1,2})?$"
        return re.match(pattern, icd_code) is not None

    return False


def classify_diagnosis_body_system(icd_code: str, description: str) -> str:
    """
    Classify diagnosis by body system using ICD ranges and keywords.

    Args:
        icd_code: The ICD code
        description: The diagnosis description

    Returns:
        Body system classification
    """
    config = _load_health_factor_config()
    body_systems = config.get("diagnosis_body_systems", {})

    if not icd_code and not description:
        return "unclassified"

    # First check for strong keyword matches in description (prioritize clear clinical descriptions)
    combined_text = f"{icd_code} {description}".lower()
    strong_keyword_systems = []

    for system_name, system_config in body_systems.items():
        keywords = system_config.get("keywords", [])
        # Count how many keywords match for this system
        matches = sum(1 for keyword in keywords if keyword in combined_text)
        if matches > 0:
            strong_keyword_systems.append((system_name, matches))

    # If we have strong keyword matches, use the one with most matches
    if strong_keyword_systems:
        # Sort by number of matches (descending)
        strong_keyword_systems.sort(key=lambda x: x[1], reverse=True)
        best_match = strong_keyword_systems[0]
        # If the best match has 2+ keywords or is clearly medical, use it
        if best_match[1] >= 2 or any(
            keyword in combined_text
            for keyword in [
                "heart",
                "cardiac",
                "myocardial",
                "diabetes",
                "depression",
                "anxiety",
            ]
        ):
            return best_match[0]

    # Then try to match by ICD code ranges
    for system_name, system_config in body_systems.items():
        icd_ranges = system_config.get("icd_ranges", [])

        for icd_range in icd_ranges:
            if _is_icd_in_range(icd_code, icd_range):
                return system_name

    # Fall back to any keyword matching
    for system_name, system_config in body_systems.items():
        keywords = system_config.get("keywords", [])
        if any(keyword in combined_text for keyword in keywords):
            return system_name

    return "other"


def _is_icd_in_range(icd_code: str, icd_range: str) -> bool:
    """
    Check if ICD code falls within a specified range.

    Args:
        icd_code: The ICD code to check
        icd_range: Range like "I00-I99" or "390-459" or "C00-D49"

    Returns:
        True if code is in range
    """
    if not icd_code or not icd_range:
        return False

    # Determine if this is an ICD-10 code (starts with letter) or ICD-9 (numeric/V/E)
    is_icd10_code = len(icd_code) > 0 and icd_code[0].isalpha()
    is_icd10_range = any(c.isalpha() for c in icd_range)

    # Only match ICD-10 codes with ICD-10 ranges, and ICD-9 codes with ICD-9 ranges
    if is_icd10_code != is_icd10_range:
        return False

    try:
        # Handle ICD-10 ranges (letter + numbers)
        if is_icd10_range and "-" in icd_range:
            start_code, end_code = icd_range.split("-")
            start_letter = start_code[0]
            end_letter = end_code[0]

            if not is_icd10_code:
                return False

            # Skip invalid patterns like "XXX.XX" (not valid ICD-10 format)
            if len(icd_code) > 1 and not icd_code[1].isdigit():
                return False

            code_letter = icd_code[0]

            # Check if letter is in range
            if start_letter <= code_letter <= end_letter:
                # Extract the numeric parts for more precise checking
                # For ICD-10, we need to handle the full code comparison
                code_parts = icd_code[1:].split(".")
                code_base = code_parts[0]

                start_base = start_code[1:]
                end_base = end_code[1:]

                # If same letter, compare numeric parts directly
                if start_letter == end_letter == code_letter:
                    code_num = int(code_base) if code_base.isdigit() else 0
                    start_num = int(start_base) if start_base.isdigit() else 0
                    end_num = int(end_base) if end_base.isdigit() else 999
                    return start_num <= code_num <= end_num

                # For cross-letter ranges (like C00-D49), check boundaries
                elif start_letter < code_letter < end_letter:
                    return True  # Any code in between letters is included
                elif code_letter == start_letter:
                    # Check if >= start numeric part
                    code_num = int(code_base) if code_base.isdigit() else 0
                    start_num = int(start_base) if start_base.isdigit() else 0
                    return code_num >= start_num
                elif code_letter == end_letter:
                    # Check if <= end numeric part
                    code_num = int(code_base) if code_base.isdigit() else 0
                    end_num = int(end_base) if end_base.isdigit() else 999
                    return code_num <= end_num

        # Handle ICD-9 ranges (numeric only)
        elif not is_icd10_range and "-" in icd_range:
            if is_icd10_code:  # ICD-10 code shouldn't match ICD-9 range
                return False

            start_num, end_num = map(int, icd_range.split("-"))
            # For ICD-9, extract all digits before decimal
            code_parts = icd_code.split(".")
            # Handle V and E codes by extracting just the numeric part
            numeric_part = "".join(filter(str.isdigit, code_parts[0]))
            if numeric_part:
                code_num = int(numeric_part)
                return start_num <= code_num <= end_num

    except (ValueError, IndexError):
        pass

    return False


def is_chronic_diagnosis(icd_code: str, description: str) -> bool:
    """
    Determine if diagnosis represents a chronic condition.

    Args:
        icd_code: The ICD code
        description: The diagnosis description

    Returns:
        True if condition is chronic
    """
    config = _load_health_factor_config()
    chronic_conditions = config.get("chronic_conditions", [])

    combined_text = f"{icd_code} {description}".lower()

    # Check against known chronic conditions
    for condition in chronic_conditions:
        if condition.lower() in combined_text:
            return True

    # Additional keyword-based checks
    chronic_keywords = [
        "chronic",
        "diabetes",
        "hypertension",
        "heart failure",
        "copd",
        "asthma",
        "arthritis",
        "depression",
        "anxiety",
        "cancer",
        "kidney disease",
        "liver disease",
        "dementia",
        "alzheimer",
    ]

    return any(keyword in combined_text for keyword in chronic_keywords)


def assess_diagnosis_severity(
    icd_code: str, description: str, diagnosis_type: str
) -> str:
    """
    Assess severity level of diagnosis.

    Args:
        icd_code: The ICD code
        description: The diagnosis description
        diagnosis_type: primary, secondary, etc.

    Returns:
        Severity level: "mild", "moderate", "severe"
    """
    combined_text = f"{icd_code} {description}".lower()

    # High severity indicators
    severe_keywords = [
        "acute",
        "severe",
        "critical",
        "emergency",
        "malignant",
        "metastatic",
        "failure",
        "arrest",
        "stroke",
        "infarction",
        "sepsis",
        "shock",
        "exacerbation",
    ]

    # Moderate severity indicators
    moderate_keywords = [
        "chronic",
        "moderate",
        "uncontrolled",
        "complicated",
        "secondary",
        "progressive",
        "active",
        "copd",
        "diabetes",
        "hypertension",
    ]

    # Low severity indicators
    mild_keywords = [
        "mild",
        "controlled",
        "stable",
        "resolved",
        "history",
        "screening",
        "routine",
        "preventive",
    ]

    # Check severity based on keywords (order matters - check severe first)
    if any(keyword in combined_text for keyword in severe_keywords):
        return "severe"
    elif any(keyword in combined_text for keyword in moderate_keywords):
        return "moderate"
    elif any(keyword in combined_text for keyword in mild_keywords):
        return "mild"

    # Default based on diagnosis type
    if diagnosis_type.lower() == "primary":
        return "moderate"  # Primary diagnoses are typically more significant
    else:
        return "mild"  # Secondary diagnoses are typically less severe


def get_diagnosis_trends(diagnoses: list[Any], icd_code: str) -> dict[str, Any]:
    """
    Analyze trends for a specific diagnosis over time.

    Args:
        diagnoses: List of Diagnosis objects
        icd_code: ICD code to analyze

    Returns:
        Dictionary with trend analysis
    """
    matching_diagnoses = [
        d for d in diagnoses if d.icd_code.upper() == icd_code.upper()
    ]

    if not matching_diagnoses:
        return {"trend": "no_data", "count": 0}

    # Sort by date
    matching_diagnoses.sort(key=lambda d: d.diagnosis_date)

    # Basic trend analysis
    count = len(matching_diagnoses)
    first_date = matching_diagnoses[0].diagnosis_date
    last_date = matching_diagnoses[-1].diagnosis_date

    # Check if it's recurring
    is_recurring = count > 1

    # Analyze severity progression
    severity_levels = [d.severity_level for d in matching_diagnoses]
    severity_scores = {"mild": 1, "moderate": 2, "severe": 3}
    numeric_progression = [severity_scores.get(s, 2) for s in severity_levels]

    trend = "stable"
    if len(numeric_progression) > 1:
        if numeric_progression[-1] > numeric_progression[0]:
            trend = "worsening"
        elif numeric_progression[-1] < numeric_progression[0]:
            trend = "improving"

    return {
        "trend": trend,
        "count": count,
        "first_diagnosed": first_date.isoformat(),
        "last_diagnosed": last_date.isoformat(),
        "is_recurring": is_recurring,
        "severity_progression": severity_levels,
        "current_severity": matching_diagnoses[-1].severity_level,
        "is_chronic": matching_diagnoses[-1].is_chronic,
        "body_system": matching_diagnoses[-1].body_system,
    }
