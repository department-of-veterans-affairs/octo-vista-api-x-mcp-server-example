"""Unified models package"""

# Base models and enums
from .base import (
    AllergyType,
    BaseVistaModel,
    Gender,
    LabResultFlag,
    MedicationStatus,
    VprDomain,
)

# Response models
from .responses import (
    LabResultsResponse,
    MedicationsResponse,
    PatientSearchResponse,
    ToolResponse,
    VitalSignsResponse,
)

# Vista domain models
from .vista import (
    Allergy,
    Appointment,
    LabResult,
    Medication,
    PatientDemographics,
    PatientSearchResult,
    Problem,
    Provider,
    RpcParameter,
    Station,
    VitalSign,
)

__all__ = [
    # Base
    "BaseVistaModel",
    "Gender",
    "VprDomain",
    "MedicationStatus",
    "AllergyType",
    "LabResultFlag",
    # Responses
    "ToolResponse",
    "PatientSearchResponse",
    "MedicationsResponse",
    "LabResultsResponse",
    "VitalSignsResponse",
    # Vista models
    "Appointment",
    "Provider",
    "Station",
    "RpcParameter",
    "Medication",
    "LabResult",
    "VitalSign",
    "Problem",
    "Allergy",
    "PatientSearchResult",
    "PatientDemographics",
]
