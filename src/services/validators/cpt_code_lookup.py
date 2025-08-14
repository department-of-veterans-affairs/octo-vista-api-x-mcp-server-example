"""CPT Code lookup functionality for common procedures"""

from typing import Any

from ...utils import get_logger

logger = get_logger(__name__)

# Common CPT codes database - in a real system this would be loaded from a file or database
CPT_CODE_DATABASE = {
    # Evaluation and Management
    "99201": {
        "description": "Office/outpatient visit new patient, level 1",
        "category": "evaluation",
        "complexity": "low",
    },
    "99202": {
        "description": "Office/outpatient visit new patient, level 2",
        "category": "evaluation",
        "complexity": "low",
    },
    "99203": {
        "description": "Office/outpatient visit new patient, level 3",
        "category": "evaluation",
        "complexity": "moderate",
    },
    "99204": {
        "description": "Office/outpatient visit new patient, level 4",
        "category": "evaluation",
        "complexity": "high",
    },
    "99205": {
        "description": "Office/outpatient visit new patient, level 5",
        "category": "evaluation",
        "complexity": "high",
    },
    "99211": {
        "description": "Office/outpatient visit established patient, level 1",
        "category": "evaluation",
        "complexity": "low",
    },
    "99212": {
        "description": "Office/outpatient visit established patient, level 2",
        "category": "evaluation",
        "complexity": "low",
    },
    "99213": {
        "description": "Office/outpatient visit established patient, level 3",
        "category": "evaluation",
        "complexity": "moderate",
    },
    "99214": {
        "description": "Office/outpatient visit established patient, level 4",
        "category": "evaluation",
        "complexity": "moderate",
    },
    "99215": {
        "description": "Office/outpatient visit established patient, level 5",
        "category": "evaluation",
        "complexity": "high",
    },
    # Surgery - Integumentary
    "11000": {
        "description": "Debridement of extensive eczematous or infected skin",
        "category": "surgery",
        "complexity": "low",
    },
    "11001": {
        "description": "Debridement of extensive eczematous or infected skin, each additional 10 sq cm",
        "category": "surgery",
        "complexity": "low",
    },
    "12001": {
        "description": "Simple repair of superficial wounds of scalp, neck, axillae, external genitalia, trunk and/or extremities (including hands and feet); 2.5 cm or less",
        "category": "surgery",
        "complexity": "low",
    },
    "12002": {
        "description": "Simple repair of superficial wounds; 2.6 cm to 7.5 cm",
        "category": "surgery",
        "complexity": "low",
    },
    # Radiology
    "71020": {
        "description": "Radiologic examination, chest, 2 views, frontal and lateral",
        "category": "radiology",
        "complexity": "moderate",
    },
    "71045": {
        "description": "Radiologic examination, chest; single view",
        "category": "radiology",
        "complexity": "moderate",
    },
    "73060": {
        "description": "Radiologic examination; knee, 1 or 2 views",
        "category": "radiology",
        "complexity": "moderate",
    },
    "73070": {
        "description": "Radiologic examination; ankle, 2 views",
        "category": "radiology",
        "complexity": "moderate",
    },
    "74000": {
        "description": "Radiologic examination, abdomen; single anteroposterior view",
        "category": "radiology",
        "complexity": "moderate",
    },
    "74020": {
        "description": "Radiologic examination, abdomen; complete acute abdomen series",
        "category": "radiology",
        "complexity": "moderate",
    },
    # Pathology and Laboratory
    "80053": {
        "description": "Comprehensive metabolic panel",
        "category": "pathology",
        "complexity": "low",
    },
    "80061": {
        "description": "Lipid panel",
        "category": "pathology",
        "complexity": "low",
    },
    "82950": {
        "description": "Glucose; post glucose dose",
        "category": "pathology",
        "complexity": "low",
    },
    "84132": {
        "description": "Potassium; serum, plasma or whole blood",
        "category": "pathology",
        "complexity": "low",
    },
    "84295": {
        "description": "Sodium; serum, plasma or whole blood",
        "category": "pathology",
        "complexity": "low",
    },
    "85025": {
        "description": "Blood count; complete (CBC), automated (Hgb, Hct, RBC, WBC and platelet count) and automated differential WBC count",
        "category": "pathology",
        "complexity": "low",
    },
    "85027": {
        "description": "Blood count; complete (CBC), automated (Hgb, Hct, RBC, WBC and platelet count)",
        "category": "pathology",
        "complexity": "low",
    },
    # Cardiology
    "93000": {
        "description": "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report",
        "category": "evaluation",
        "complexity": "moderate",
    },
    "93005": {
        "description": "Electrocardiogram, routine ECG with at least 12 leads; tracing only, without interpretation and report",
        "category": "evaluation",
        "complexity": "low",
    },
    "93010": {
        "description": "Electrocardiogram, routine ECG with at least 12 leads; interpretation and report only",
        "category": "evaluation",
        "complexity": "low",
    },
    # Immunizations
    "90471": {
        "description": "Immunization administration (includes percutaneous, intradermal, subcutaneous, or intramuscular injections); 1 vaccine (single or combination vaccine/toxoid)",
        "category": "therapy",
        "complexity": "low",
    },
    "90472": {
        "description": "Immunization administration; each additional vaccine",
        "category": "therapy",
        "complexity": "low",
    },
    "90686": {
        "description": "Influenza virus vaccine, quadrivalent (IIV4), split virus, preservative free, 0.25 mL dosage, for intramuscular use",
        "category": "therapy",
        "complexity": "low",
    },
    "90707": {
        "description": "Measles, mumps and rubella virus vaccine (MMR), live, for subcutaneous use",
        "category": "therapy",
        "complexity": "low",
    },
}

# Common CPT modifiers
CPT_MODIFIERS = {
    "22": {
        "description": "Increased Procedural Services",
        "impact": "Significantly greater than usual",
    },
    "25": {
        "description": "Significant, Separately Identifiable Evaluation and Management Service",
        "impact": "Separate E&M service",
    },
    "26": {
        "description": "Professional Component",
        "impact": "Professional interpretation only",
    },
    "50": {"description": "Bilateral Procedure", "impact": "Performed on both sides"},
    "51": {
        "description": "Multiple Procedures",
        "impact": "Multiple procedures performed",
    },
    "52": {
        "description": "Reduced Services",
        "impact": "Service reduced or eliminated",
    },
    "53": {"description": "Discontinued Procedure", "impact": "Procedure terminated"},
    "59": {
        "description": "Distinct Procedural Service",
        "impact": "Separate service/procedure",
    },
    "62": {"description": "Two Surgeons", "impact": "Co-surgeons working together"},
    "76": {
        "description": "Repeat Procedure or Service by Same Physician",
        "impact": "Repeat by same provider",
    },
    "77": {
        "description": "Repeat Procedure by Another Physician",
        "impact": "Repeat by different provider",
    },
    "78": {
        "description": "Unplanned Return to the Operating/Procedure Room",
        "impact": "Unplanned return",
    },
    "79": {
        "description": "Unrelated Procedure or Service by the Same Physician",
        "impact": "Unrelated service",
    },
    "80": {"description": "Assistant Surgeon", "impact": "Assistant surgeon services"},
    "81": {
        "description": "Minimum Assistant Surgeon",
        "impact": "Minimal assistant services",
    },
    "82": {
        "description": "Assistant Surgeon (when qualified resident surgeon not available)",
        "impact": "Qualified assistant when resident unavailable",
    },
    "LT": {"description": "Left side", "impact": "Procedure performed on left side"},
    "RT": {"description": "Right side", "impact": "Procedure performed on right side"},
    "E1": {
        "description": "Upper left, eyelid",
        "impact": "Specific anatomical location",
    },
    "E2": {
        "description": "Lower left, eyelid",
        "impact": "Specific anatomical location",
    },
    "E3": {
        "description": "Upper right, eyelid",
        "impact": "Specific anatomical location",
    },
    "E4": {
        "description": "Lower right, eyelid",
        "impact": "Specific anatomical location",
    },
}


def lookup_cpt_code(cpt_code: str) -> dict[str, Any] | None:
    """
    Look up CPT code information

    Args:
        cpt_code: The CPT code to look up

    Returns:
        Dictionary with CPT code information or None if not found
    """
    if not cpt_code:
        return None

    # Normalize code
    code = str(cpt_code).strip().upper()

    # Look up in database
    code_info = CPT_CODE_DATABASE.get(code)

    if code_info:
        return {"cpt_code": code, "found": True, **code_info}

    return {
        "cpt_code": code,
        "found": False,
        "description": "Code not found in lookup database",
        "category": "unknown",
        "complexity": "unknown",
    }


def lookup_cpt_modifier(modifier: str) -> dict[str, Any] | None:
    """
    Look up CPT modifier information

    Args:
        modifier: The CPT modifier to look up

    Returns:
        Dictionary with modifier information or None if not found
    """
    if not modifier:
        return None

    # Normalize modifier
    mod = str(modifier).strip().upper()

    # Look up in database
    modifier_info = CPT_MODIFIERS.get(mod)

    if modifier_info:
        return {"modifier": mod, "found": True, **modifier_info}

    return {
        "modifier": mod,
        "found": False,
        "description": "Modifier not found in lookup database",
        "impact": "Unknown impact",
    }


def search_cpt_codes(
    query: str,
    category: str | None = None,
    complexity: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search CPT codes by description or code

    Args:
        query: Search query (partial code or description)
        category: Filter by category
        complexity: Filter by complexity
        limit: Maximum results to return

    Returns:
        List of matching CPT codes
    """
    if not query:
        return []

    query_lower = query.strip().lower()
    results = []

    for code, info in CPT_CODE_DATABASE.items():
        # Check if query matches code or description
        if query_lower in code.lower() or query_lower in info["description"].lower():
            # Apply filters
            if category and info["category"] != category.lower():
                continue

            if complexity and info["complexity"] != complexity.lower():
                continue

            results.append({"cpt_code": code, **info})

            if len(results) >= limit:
                break

    return results


def get_codes_by_category(category: str) -> list[dict[str, Any]]:
    """
    Get all CPT codes in a specific category

    Args:
        category: Category to filter by

    Returns:
        List of CPT codes in the category
    """
    if not category:
        return []

    category_lower = category.strip().lower()
    results = []

    for code, info in CPT_CODE_DATABASE.items():
        if info["category"] == category_lower:
            results.append({"cpt_code": code, **info})

    return results


def get_available_categories() -> list[str]:
    """
    Get list of available CPT code categories

    Returns:
        List of category names
    """
    categories = set()

    for info in CPT_CODE_DATABASE.values():
        categories.add(info["category"])

    return sorted(categories)


def get_available_modifiers() -> list[dict[str, Any]]:
    """
    Get list of available CPT modifiers

    Returns:
        List of modifier information
    """
    return [{"modifier": mod, **info} for mod, info in CPT_MODIFIERS.items()]


def validate_code_modifier_combination(
    cpt_code: str, modifiers: list[str]
) -> dict[str, Any]:
    """
    Validate CPT code and modifier combination

    Args:
        cpt_code: The CPT code
        modifiers: List of modifiers

    Returns:
        Validation results
    """
    code_info = lookup_cpt_code(cpt_code)
    results: dict[str, Any] = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "code_info": code_info,
        "modifier_info": [],
    }

    # Validate code
    if code_info and not code_info["found"]:
        results["warnings"].append(f"CPT code {cpt_code} not found in lookup database")

    # Validate modifiers
    for modifier in modifiers or []:
        mod_info = lookup_cpt_modifier(modifier)
        results["modifier_info"].append(mod_info)

        if mod_info and not mod_info["found"]:
            results["warnings"].append(
                f"Modifier {modifier} not found in lookup database"
            )

    # Check for conflicting modifiers
    if modifiers:
        if "LT" in modifiers and "RT" in modifiers:
            results["errors"].append(
                "Cannot use both LT (left) and RT (right) modifiers"
            )
            results["valid"] = False

        if "50" in modifiers and ("LT" in modifiers or "RT" in modifiers):
            results["warnings"].append(
                "Bilateral modifier (50) with side-specific modifier may be redundant"
            )

    return results
