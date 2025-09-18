"""API response models (typed)"""

from datetime import date
from enum import Enum
from typing import Generic, TypeVar

from pydantic import Field, computed_field

from src.models.patient.appointment import Appointment
from src.models.patient.treatment import Treatment

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
    Problem,
    ProblemSummary,
    PurposeOfVisit,
    Visit,
    VisitSummary,
    VitalSign,
)
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
class MedicationsResponseData(ResponseData):
    medications: list[Medication]


class LabResultsResponseData(ResponseData):
    abnormal_count: int = 0
    critical_count: int = 0
    by_type: dict[str, list[str]] = Field(default_factory=dict)
    labs: list[LabResult] = Field(default_factory=list)


class VitalSignsResponseData(ResponseData):
    vital_signs: list[VitalSign]


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
    active_count: int = 0
    diagnoses: list[Diagnosis] = Field(default_factory=list)


class AllergiesResponseData(ResponseData):
    """Response data for patient allergies"""

    allergies: list[Allergy] = Field(default_factory=list)


class HealthFactorsResponseData(ResponseData):
    health_factors: list[HealthFactor] = Field(default_factory=list)


class ProceduresResponseData(ResponseData):
    total_procedures: int = 0
    filtered_procedures: int = 0
    date_range: dict[str, str] | None = None
    unique_encounters: int = 0
    procedures: list[CPTCode] = Field(default_factory=list)
    filters_applied: dict[str, str | int | bool | date | None] = Field(
        default_factory=dict
    )


class VisitsResponseData(ResponseData):
    """Response data for patient visits"""

    patient_gender: str | None = None
    summary: VisitSummary
    all_visits: list[Visit] = Field(default_factory=list)
    filters: dict[str, str | bool | int] = Field(default_factory=dict)


class AppointmentsResponseData(ResponseData):
    """Response data for patient appointments"""

    future_count: int = Field(default=0, description="Count of upcoming appointments")
    past_count: int = Field(default=0, description="Count of past appointments")
    total_count: int = Field(default=0, description="Total count of appointments")
    by_status: dict[str, int] = Field(
        default_factory=dict, description="Appointment counts by status"
    )
    by_clinic: dict[str, int] = Field(
        default_factory=dict, description="Appointment counts by clinic"
    )
    appointments: list[Appointment] = Field(default_factory=list)


# Response Models (all response models grouped together)


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


class AppointmentsResponse(ToolResponse[AppointmentsResponseData]):
    """Appointments response"""

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


class ProblemsResponseData(ResponseData):
    """Problems response data"""

    problems: list[Problem]
    summary: ProblemSummary
    by_status: dict[str, int] = Field(default_factory=dict)
    by_acuity: dict[str, int] = Field(default_factory=dict)
    active_problems: list[str] = Field(default_factory=list)
    inactive_problems: list[str] = Field(default_factory=list)
    service_connected_problems: list[str] = Field(default_factory=list)


class ProblemsResponse(ToolResponse[ProblemsResponseData]):
    """Problems response"""

    pass


class TreatmentsResponseData(ResponseData):
    """Treatments response data"""

    treatments: list[Treatment] = Field(default_factory=list)
    active_treatments: list[str] = Field(default_factory=list)
    completed_treatments: list[str] = Field(default_factory=list)
    scheduled_treatments: list[str] = Field(default_factory=list)
    by_status: dict[str, int] = Field(default_factory=dict)


class TreatmentsResponse(ToolResponse[TreatmentsResponseData]):
    """Treatments response"""

    pass
