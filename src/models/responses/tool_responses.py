"""API response models"""

from typing import Any

from pydantic import Field

from ..base import BaseVistaModel
from ..base.common import PaginationMetadata
from ..vista import LabResult, Medication, PatientSearchResult, VitalSign


class ToolResponse(BaseVistaModel):
    """Standard tool response format"""

    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def success_response(cls, data: Any, metadata: dict[str, Any] | None = None):
        """Create a success response"""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_response(cls, error: str, metadata: dict[str, Any] | None = None):
        """Create an error response"""
        return cls(success=False, error=error, metadata=metadata)


class PatientSearchResponse(ToolResponse):
    """Patient search response"""

    search_term: str | None = None
    station: str | None = None
    count: int = 0
    total_found: int = 0
    patients: list[PatientSearchResult] = Field(default_factory=list)
    pagination: PaginationMetadata | None = None


class MedicationsResponse(ToolResponse):
    """Medications response"""

    patient_dfn: str
    station: str
    count: int = 0
    medications: list[Medication] = Field(default_factory=list)


class LabResultsResponse(ToolResponse):
    """Lab results response"""

    patient_dfn: str
    station: str
    count: int = 0
    lab_results: list[LabResult] = Field(default_factory=list)


class VitalSignsResponse(ToolResponse):
    """Vital signs response"""

    patient_dfn: str
    station: str
    count: int = 0
    vital_signs: list[VitalSign] = Field(default_factory=list)


class PatientInfo(BaseVistaModel):
    """Basic patient information for responses"""

    dfn: str
    name: str
    age: int | None = None


class PatientLabsResponse(BaseVistaModel):
    """Patient labs response with pagination"""

    success: bool = True
    patient: PatientInfo
    labs: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientVitalsResponse(BaseVistaModel):
    """Patient vitals response with pagination"""

    success: bool = True
    patient: PatientInfo
    vitals: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientMedicationsResponse(BaseVistaModel):
    """Patient medications response with pagination"""

    success: bool = True
    patient: PatientInfo
    medications: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientConsultsResponse(BaseVistaModel):
    """Patient consults response with pagination"""

    success: bool = True
    patient: PatientInfo
    consults: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientOrdersResponse(BaseVistaModel):
    """Patient orders response with pagination"""

    success: bool = True
    patient: PatientInfo
    orders: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientDiagnosesResponse(BaseVistaModel):
    """Patient diagnoses response with pagination"""

    success: bool = True
    data: dict[str, Any]
    metadata: dict[str, Any]


class PatientProceduresResponse(BaseVistaModel):
    """Patient procedures response with pagination"""

    success: bool = True
    patient: PatientInfo
    procedures: Any
    summary: dict[str, Any]
    filters_applied: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]


class PatientHealthFactorsResponse(BaseVistaModel):
    """Patient health factors response with pagination"""

    success: bool = True
    data: dict[str, Any]
    metadata: dict[str, Any]


class PatientDocumentsResponse(BaseVistaModel):
    """Patient documents response with pagination"""

    success: bool = True
    patient: PatientInfo
    documents: dict[str, Any]
    pagination: PaginationMetadata
    metadata: dict[str, Any]
