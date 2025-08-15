"""API response models (typed)"""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import Field, computed_field

from ..base import BaseVistaModel
from ..patient import (
    Allergy,
    Consult,
    CPTCode,
    Diagnosis,
    Document,
    HealthFactor,
    LabResult,
    Medication,
    Order,
    POVSummary,
    PurposeOfVisit,
    Visit,
    VisitSummary,
    VitalSign,
)
from ..vista import PatientSearchResult
from .metadata import ResponseMetadata

T = TypeVar("T")


class ResponseData(BaseVistaModel):
    """Base class for response data payloads"""

    pass


class ToolResponse(BaseVistaModel, Generic[T]):
    """Standard tool response format with typed metadata and payload"""

    success: bool
    data: T | None = None
    error: str | None = None
    error_code: str | None = None
    total_item_count: int | None = None
    metadata: ResponseMetadata | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_error(self) -> bool:
        return not self.success


class BodySystem(str, Enum):
    """Body system classifications for diagnoses"""

    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    ENDOCRINE = "endocrine"
    MUSCULOSKELETAL = "musculoskeletal"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    GENITOURINARY = "genitourinary"
    MENTAL_HEALTH = "mental_health"
    INFECTIOUS = "infectious"
    NEOPLASM = "neoplasm"
    SYMPTOMS_SIGNS = "symptoms_signs"
    EXTERNAL_CAUSES = "external_causes"
    INJURY_POISONING = "injury_poisoning"
    HEALTH_SERVICES = "health_services"
    BLOOD_IMMUNE = "blood_immune"
    EYE_VISION = "eye_vision"
    EAR_HEARING = "ear_hearing"
    SKIN_SUBCUTANEOUS = "skin_subcutaneous"
    PREGNANCY_CHILDBIRTH = "pregnancy_childbirth"
    PERINATAL = "perinatal"
    OTHER = "other"
    UNCLASSIFIED = "unclassified"


class DiagnosisTrend(BaseVistaModel):
    """Trend analysis for a specific diagnosis"""

    trend: str  # "stable", "improving", "worsening", "no_data"
    count: int
    first_diagnosed: str | None = None  # ISO date string
    last_diagnosed: str | None = None  # ISO date string
    is_recurring: bool = False
    severity_progression: list[str] = Field(default_factory=list)
    current_severity: str | None = None
    is_chronic: bool = False
    body_system: BodySystem | None = None


# Response Data Models (all data models grouped together)
class PatientSearchResponseData(ResponseData):
    patients: list[PatientSearchResult]


class MedicationsResponseData(ResponseData):
    medications: list[Medication]
    refill_alerts: list[Medication] = Field(default_factory=list)


class LabResultsResponseData(ResponseData):
    abnormal_count: int = 0
    critical_count: int = 0
    by_type: dict[str, list[str]] = Field(default_factory=dict)
    labs: list[LabResult] = Field(default_factory=list)


class VitalSignsResponseData(ResponseData):
    vital_signs: list[VitalSign]
    latest_vitals: dict[str, VitalSign] = Field(default_factory=dict)


class DocumentsResponseData(ResponseData):
    completed: list[str] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)


class OrdersResponseData(ResponseData):
    active_count: int = 0
    orders: list[Order]


class ConsultsResponseData(ResponseData):
    overdue_list: list[str] = Field(default_factory=list)
    consults: list[Consult] = Field(default_factory=list)


class DiagnosesResponseData(ResponseData):
    summary: dict[str, int] = Field(default_factory=dict)
    by_body_system: dict[str, list[str]] = Field(default_factory=dict)
    primary_diagnoses: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    trending: dict[str, DiagnosisTrend] = Field(default_factory=dict)
    diagnoses: list[Diagnosis] = Field(default_factory=list)


class AllergiesResponseData(ResponseData):
    """Response data for patient allergies"""

    verified_count: int = 0
    unverified_count: int = 0
    by_product_type: dict[str, int] = Field(default_factory=dict)
    by_reaction_type: dict[str, int] = Field(default_factory=dict)
    severe_allergies: list[str] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)


class HealthFactorsResponseData(ResponseData):
    summary: dict[str, int] = Field(default_factory=dict)
    by_risk_category: dict[str, list[str]] = Field(default_factory=dict)
    high_risk_factors: list[str] = Field(default_factory=list)
    health_factors: list[HealthFactor] = Field(default_factory=list)


class ProceduresResponseData(ResponseData):
    total_procedures: int = 0
    filtered_procedures: int = 0
    surgical_procedures: int = 0
    diagnostic_procedures: int = 0
    procedures_with_modifiers: int = 0
    category_breakdown: dict[str, int] = Field(default_factory=dict)
    complexity_breakdown: dict[str, int] = Field(default_factory=dict)
    date_range: dict[str, str] | None = None
    unique_providers: int = 0
    unique_encounters: int = 0
    procedures: list[CPTCode] = Field(default_factory=list)
    filters_applied: dict[str, str | int | bool | None] = Field(default_factory=dict)


class VisitsResponseData(ResponseData):
    """Response data for patient visits"""

    patient_dfn: str
    patient_name: str | None = None
    patient_age: int | None = None
    patient_gender: str | None = None
    summary: VisitSummary
    all_visits: list[Visit] = Field(default_factory=list)
    filters: dict[str, str | bool | int] = Field(default_factory=dict)

    # API response-specific summary fields
    total_count: int = Field(default=0, description="Total count of visits")
    active_count: int = Field(default=0, description="Number of active visits")
    inpatient_count: int = Field(default=0, description="Number of inpatient visits")
    emergency_count: int = Field(default=0, description="Number of emergency visits")
    average_inpatient_duration_days: float | None = Field(
        default=None, description="Average duration of inpatient stays"
    )
    by_type: dict[str, int] = Field(
        default_factory=dict, description="Visit counts by type"
    )


# Response Models (all response models grouped together)
class PatientSearchResponse(ToolResponse[PatientSearchResponseData]):
    """Patient search response"""

    search_term: str | None = None


class MedicationsResponse(ToolResponse[MedicationsResponseData]):
    """Medications response"""

    pass


class LabResultsResponse(ToolResponse[LabResultsResponseData]):
    """Lab results response"""

    pass


class VitalSignsResponse(ToolResponse[VitalSignsResponseData]):
    """Vital signs response"""

    pass


class DocumentsResponse(ToolResponse[DocumentsResponseData]):
    """Documents response"""

    pass


class OrdersResponse(ToolResponse[OrdersResponseData]):
    """Orders response"""

    pass


class ConsultsResponse(ToolResponse[ConsultsResponseData]):
    """Consults response"""

    pass


class DiagnosesResponse(ToolResponse[DiagnosesResponseData]):
    """Diagnoses response"""

    pass


class VisitsResponse(ToolResponse[VisitsResponseData]):
    """Visits response"""

    pass


class AllergiesResponse(ToolResponse[AllergiesResponseData]):
    """Allergies response"""

    pass


class HealthFactorsResponse(ToolResponse[HealthFactorsResponseData]):
    """Health factors response"""

    pass


class ProceduresResponse(ToolResponse[ProceduresResponseData]):
    """Procedures response"""

    pass


class POVsResponseData(ResponseData):
    """POVs response data"""

    povs: list[PurposeOfVisit]
    summary: POVSummary
    by_encounter: dict[str, list[str]] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    primary_povs: list[str] = Field(default_factory=list)
    secondary_povs: list[str] = Field(default_factory=list)


class POVsResponse(ToolResponse[POVsResponseData]):
    """POVs response"""

    pass
