"""Treatment validation and categorization functions"""

import re
from typing import Any

from ...utils import get_logger

logger = get_logger()


class TreatmentComplexity:
    """Treatment complexity levels"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


def calculate_treatment_complexity(
    treatment_type: str | None, treatment_name: str | None, location: str | None
) -> str:
    """Calculate treatment complexity based on type, name, and location"""
    if not treatment_type and not treatment_name:
        return TreatmentComplexity.LOW

    # Combine all available text for analysis
    text_to_analyze = " ".join(
        filter(None, [treatment_type or "", treatment_name or "", location or ""])
    ).lower()

    # High complexity indicators
    high_complexity_patterns = [
        r"surgery|surgical|operation|transplant|bypass|resection",
        r"intensive care|icu|critical care|emergency",
        r"major|complex|advanced|specialized",
        r"anesthesia|operative|post-operative",
        r"cardiac|heart|brain|neurological",
        r"oncology|cancer|chemotherapy|radiation",
    ]

    for pattern in high_complexity_patterns:
        if re.search(pattern, text_to_analyze):
            return TreatmentComplexity.HIGH

    # Moderate complexity indicators
    moderate_complexity_patterns = [
        r"procedure|therapy|treatment|intervention",
        r"endoscopy|biopsy|injection|infusion",
        r"physical therapy|occupational therapy",
        r"diagnostic|imaging|scan",
        r"minor surgical|outpatient surgery",
    ]

    for pattern in moderate_complexity_patterns:
        if re.search(pattern, text_to_analyze):
            return TreatmentComplexity.MODERATE

    return TreatmentComplexity.LOW


def get_treatment_specialty(
    treatment_type: str | None, treatment_name: str | None
) -> str | None:
    """Determine medical specialty based on treatment type and name"""
    if not treatment_type and not treatment_name:
        return None

    text_to_analyze = " ".join(
        filter(None, [treatment_type or "", treatment_name or ""])
    ).lower()

    specialty_patterns = {
        "Cardiology": [
            r"cardiac|heart|cardiovascular|ecg|ekg|stress test",
            r"angioplasty|stent|bypass|pacemaker",
        ],
        "Orthopedics": [
            r"orthopedic|bone|joint|fracture|arthroscopy",
            r"hip|knee|shoulder|spine|back",
        ],
        "Gastroenterology": [
            r"gastro|endoscopy|colonoscopy|gi|digestive",
            r"stomach|intestine|colon|liver",
        ],
        "Neurology": [
            r"neuro|brain|nervous|seizure|stroke",
            r"mri brain|ct head|neurological",
        ],
        "Oncology": [
            r"oncology|cancer|tumor|chemotherapy|radiation",
            r"biopsy|malignant|benign|metastasis",
        ],
        "Pulmonology": [
            r"pulmonary|lung|respiratory|breathing",
            r"copd|asthma|pneumonia|chest",
        ],
        "Dermatology": [
            r"dermatology|skin|rash|lesion|mole",
            r"biopsy skin|dermatitis",
        ],
        "Psychiatry": [
            r"psychiatric|mental health|depression|anxiety",
            r"therapy|counseling|behavioral",
        ],
        "Physical Medicine": [
            r"physical therapy|occupational therapy|rehabilitation",
            r"pt|ot|rehab|mobility",
        ],
    }

    for specialty, patterns in specialty_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_to_analyze):
                return specialty

    return "General Medicine"


def get_treatment_duration_category(
    treatment_type: str | None, treatment_name: str | None
) -> str:
    """Categorize treatment duration based on type and name"""
    if not treatment_type and not treatment_name:
        return "acute"

    text_to_analyze = " ".join(
        filter(None, [treatment_type or "", treatment_name or ""])
    ).lower()

    # Chronic duration indicators
    chronic_patterns = [
        r"chronic|ongoing|maintenance|long-term|permanent",
        r"dialysis|insulin|lifelong|continuous",
    ]

    for pattern in chronic_patterns:
        if re.search(pattern, text_to_analyze):
            return "chronic"

    # Long-term duration indicators
    long_term_patterns = [
        r"rehabilitation|recovery|healing|therapy course",
        r"post-operative care|follow-up treatment",
    ]

    for pattern in long_term_patterns:
        if re.search(pattern, text_to_analyze):
            return "long_term"

    # Short-term duration indicators
    short_term_patterns = [
        r"antibiotic|medication course|short-term",
        r"post-op|immediate|temporary",
    ]

    for pattern in short_term_patterns:
        if re.search(pattern, text_to_analyze):
            return "short_term"

    return "acute"  # Default


def is_inpatient_treatment(
    treatment_type: str | None, treatment_name: str | None, location: str | None
) -> bool:
    """Determine if treatment is inpatient based on type, name, and location"""
    if not treatment_type and not treatment_name and not location:
        return False

    text_to_analyze = " ".join(
        filter(None, [treatment_type or "", treatment_name or "", location or ""])
    ).lower()

    inpatient_patterns = [
        r"surgery|surgical|operation|major",
        r"intensive care|icu|critical care",
        r"hospital admission|inpatient|ward",
        r"post-operative|recovery room",
        r"transplant|bypass|resection",
    ]

    return any(re.search(pattern, text_to_analyze) for pattern in inpatient_patterns)


def validate_treatment_outcome(outcome: Any) -> bool:
    """Validate treatment outcome text"""
    if not isinstance(outcome, str):
        return False

    if not outcome or not outcome.strip():
        return False

    # Must be at least 3 characters after stripping
    return not len(outcome.strip()) < 3


def get_treatment_effectiveness_indicators(
    treatment_type: str | None, outcome: str | None
) -> dict[str, bool]:
    """Analyze treatment outcome for effectiveness indicators"""
    indicators = {
        "has_outcome": False,
        "outcome_positive": False,
        "outcome_negative": False,
        "requires_followup": False,
        "has_complications": False,
    }

    if not outcome or not outcome.strip():
        return indicators

    indicators["has_outcome"] = True
    outcome_lower = outcome.lower()

    # Positive outcome indicators
    positive_patterns = [
        r"successful|improved|effective|recovered|healed",
        r"no complications|stable|good response|well tolerated",
        r"complete|resolved|satisfactory",
    ]

    for pattern in positive_patterns:
        if re.search(pattern, outcome_lower):
            indicators["outcome_positive"] = True
            break

    # Negative outcome indicators
    negative_patterns = [
        r"failed|unsuccessful|worsened|deteriorated",
        r"adverse|reaction|complication|infection",
        r"discontinued|stopped|intolerant",
    ]

    for pattern in negative_patterns:
        if re.search(pattern, outcome_lower):
            indicators["outcome_negative"] = True
            break

    # Follow-up indicators
    followup_patterns = [
        r"continue|follow-up|monitor|reassess|ongoing",
        r"next appointment|return|check|evaluate",
    ]

    for pattern in followup_patterns:
        if re.search(pattern, outcome_lower):
            indicators["requires_followup"] = True
            break

    # Complication indicators
    complication_patterns = [
        r"complication|adverse|side effect|bleeding",
        r"infection|reaction|problem|issue",
    ]

    for pattern in complication_patterns:
        if re.search(pattern, outcome_lower):
            indicators["has_complications"] = True
            break

    return indicators
