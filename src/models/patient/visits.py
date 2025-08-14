"""Visit data models for patient records"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from ...services.formatters.location_mapper import LocationMapper
from ...services.parsers.patient.datetime_parser import parse_datetime
from ..base.common import BaseModelExcludeNone
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

    @classmethod
    def from_location_code(cls, location_code: str, location_name: str) -> "VisitType":
        """Classify visit type based on location code and name"""
        if not location_code or not location_name:
            return cls.UNKNOWN

        location_code = location_code.upper()
        location_name = location_name.upper()

        # Surgery - check first to avoid conflicts with emergency
        if any(
            term in location_name
            for term in ["OPERATING ROOM", "SURGERY SUITE", "PREOP", "POSTOP"]
        ):
            return cls.SURGERY

        # Observation - check before emergency to avoid conflicts
        if any(term in location_name for term in ["OBSERVATION", "OBS", "SHORT STAY"]):
            return cls.OBSERVATION

        # Emergency/Urgent care - be specific to avoid conflicts
        if any(
            term in location_name
            for term in ["EMERGENCY ROOM", "ER", "URGENT CARE", "TRAUMA CENTER"]
        ):
            return cls.EMERGENCY

        # Inpatient units
        if any(
            term in location_name
            for term in ["WARD", "UNIT", "FLOOR", "ICU", "CCU", "STEPDOWN"]
        ):
            return cls.INPATIENT

        # Outpatient clinics
        if any(
            term in location_name for term in ["CLINIC", "AMBULATORY", "OUTPATIENT"]
        ):
            return cls.OUTPATIENT

        # Default to outpatient for most other cases
        return cls.OUTPATIENT


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

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing"""
        super().model_post_init(__context)

        # Auto-classify visit type if not set
        if self.visit_type == VisitType.UNKNOWN:
            # Use enhanced location mapper for better classification
            location_type = LocationMapper.get_location_type(
                self.location_code, self.location_name
            )
            try:
                self.visit_type = VisitType(location_type)
            except ValueError:
                # Fall back to original classification method
                self.visit_type = VisitType.from_location_code(
                    self.location_code, self.location_name
                )

    @property
    def is_inpatient(self) -> bool:
        """Check if this is an inpatient visit"""
        return self.visit_type == VisitType.INPATIENT

    @property
    def is_emergency(self) -> bool:
        """Check if this is an emergency visit"""
        return self.visit_type == VisitType.EMERGENCY

    @property
    def is_active(self) -> bool:
        """Check if visit is currently active (admitted but not discharged)"""
        if not self.is_inpatient:
            return False
        return bool(self.admission_date and not self.discharge_date)

    @property
    def duration_days(self) -> int | None:
        """Calculate visit duration in days"""
        if not self.admission_date:
            return None
        end_date = self.discharge_date or datetime.now(UTC)
        delta = end_date - self.admission_date
        return delta.days

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

    @property
    def location_summary(self) -> dict[str, Any]:
        """Get comprehensive location information using location mapper"""
        return LocationMapper.get_location_summary(
            self.location_code, self.location_name
        )

    @property
    def standardized_location_name(self) -> str:
        """Get standardized location name"""
        return LocationMapper.standardize_location_name(self.location_name)


class VisitSummary(BaseModelExcludeNone):
    """Summary of patient visits"""

    total_visits: int = Field(description="Total number of visits")
    last_visit: datetime | None = Field(default=None, description="Date of last visit")
    visit_types: list[VisitType] = Field(
        default_factory=list, description="Types of visits"
    )
    facilities: list[FacilityInfo] = Field(
        default_factory=list, description="Facilities visited"
    )
