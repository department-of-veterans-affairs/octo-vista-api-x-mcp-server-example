"""Patient model exports for backwards compatibility"""

from .base import (
    BasePatientModel,
    ConsultStatus,
    FacilityInfo,
    Gender,
    InterpretationCode,
    ProvisionalDx,
    Urgency,
)
from .clinical import (
    Consult,
    LabResult,
    VitalSign,
)
from .collection import PatientDataCollection
from .demographics import (
    PatientAddress,
    PatientDemographics,
    PatientFlag,
    PatientSupport,
    PatientTelecom,
    VeteranInfo,
)
from .visits import (
    Visit,
    VisitType,
)

__all__ = [
    # Base types
    "BasePatientModel",
    "Gender",
    "InterpretationCode",
    "ConsultStatus",
    "Urgency",
    "FacilityInfo",
    "ProvisionalDx",
    # Demographics
    "PatientAddress",
    "PatientTelecom",
    "PatientSupport",
    "VeteranInfo",
    "PatientFlag",
    "PatientDemographics",
    # Clinical
    "VitalSign",
    "LabResult",
    "Consult",
    "Visit",
    "VisitType",
    # Collection
    "PatientDataCollection",
]
