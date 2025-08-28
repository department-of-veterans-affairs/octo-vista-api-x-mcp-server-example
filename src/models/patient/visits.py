"""Visit data models for patient records"""

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ..base.common import BaseVistaModel
from .base import BasePatientModel, FacilityInfo


class VisitType(str, Enum):
    """Visit type classification"""

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    OBSERVATION = "observation"
    SURGERY = "surgery"
    CONSULTATION = "consultation"
    UNKNOWN = "unknown"


class Visit(BasePatientModel):
    """Patient visit/encounter record"""

    uid: str
    local_id: str = Field(alias="localId")

    # Visit identification
    visit_date: datetime | None = Field(None, alias="visitDate")
    location_code: str = Field(alias="locationCode")
    location_name: str = Field(alias="locationName")
    visit_type: VisitType = Field(default=VisitType.UNKNOWN, alias="visitType")

    # Provider information
    provider_uid: str | None = Field(None, alias="providerUid")
    provider_name: str | None = Field(None, alias="providerName")
    attending_provider: str | None = Field(None, alias="attendingProvider")

    # Clinical information
    chief_complaint: str | None = Field(None, alias="chiefComplaint")
    diagnosis: str | None = None
    discharge_diagnosis: str | None = Field(None, alias="dischargeDiagnosis")

    # Dates
    admission_date: datetime | None = Field(None, alias="admissionDate")
    discharge_date: datetime | None = Field(None, alias="dischargeDate")
    scheduled_date: datetime | None = Field(None, alias="scheduledDate")

    # Status
    status_code: str = Field(alias="statusCode")
    status_name: str = Field(alias="statusName")

    # Location details
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    ward: str | None = None
    room: str | None = None
    bed: str | None = None

    # Related orders and treatments
    order_uids: list[str] = Field(default_factory=list, alias="orderUids")
    treatment_uids: list[str] = Field(default_factory=list, alias="treatmentUids")

    # Additional metadata
    visit_number: str | None = Field(None, alias="visitNumber")
    encounter_type: str | None = Field(None, alias="encounterType")
    insurance: str | None = None
    notes: str | None = None

    @field_validator("local_id", "facility_code", "location_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator(
        "visit_date",
        "admission_date",
        "discharge_date",
        "scheduled_date",
        mode="before",
    )
    @classmethod
    def parse_datetime_field(cls, v):
        return parse_datetime(v)

    @field_validator("visit_type", mode="before")
    @classmethod
    def parse_visit_type(cls, v):
        """Parse visit type"""
        if isinstance(v, VisitType):
            return v
        if isinstance(v, str):
            try:
                return VisitType(v.lower())
            except ValueError:
                return VisitType.UNKNOWN
        return VisitType.UNKNOWN

    @property
    def display_location(self) -> str:
        """Get display-friendly location name"""
        if self.ward and self.room:
            return f"{self.location_name} - {self.ward} Room {self.room}"
        elif self.ward:
            return f"{self.location_name} - {self.ward}"
        return self.location_name

    @property
    def display_dates(self) -> str:
        """Get display-friendly date range"""
        if self.admission_date and self.discharge_date:
            return f"{self.admission_date.strftime('%Y-%m-%d')} to {self.discharge_date.strftime('%Y-%m-%d')}"
        elif self.admission_date:
            return f"Since {self.admission_date.strftime('%Y-%m-%d')}"
        elif self.visit_date:
            return self.visit_date.strftime("%Y-%m-%d")
        return "Unknown date"


class VisitSummary(BaseVistaModel):
    """Summary of patient visits"""

    total_visits: int = Field(description="Total number of visits")
    last_visit: datetime | None = Field(default=None, description="Date of last visit")
    visit_types: list[VisitType] = Field(
        default_factory=list, description="Types of visits"
    )
    facilities: list[FacilityInfo] = Field(
        default_factory=list, description="Facilities visited"
    )
