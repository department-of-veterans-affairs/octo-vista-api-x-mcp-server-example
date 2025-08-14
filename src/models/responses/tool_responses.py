"""API response models"""

from typing import Any

from pydantic import Field

from ..base import BaseVistaModel
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
    patients: list[PatientSearchResult] = Field(default_factory=list)


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
