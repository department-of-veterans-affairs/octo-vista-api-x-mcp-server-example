"""Clinical data validation and categorization utilities with JSON-based configuration"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


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
