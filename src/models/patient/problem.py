"""Patient Problem models for VistA records"""

from datetime import datetime
from enum import Enum

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response
from .base import BasePatientModel

logger = get_logger()


class ProblemStatus(str, Enum):
    """Problem status enumeration"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ProblemAcuity(str, Enum):
    """Problem acuity enumeration"""

    ACUTE = "acute"
    CHRONIC = "chronic"
    UNKNOWN = "unknown"


class ProblemComment(BasePatientModel):
    """Problem comment model"""

    comment: str
    entered: datetime
    entered_by_code: str = Field(alias="enteredByCode")
    entered_by_name: str = Field(alias="enteredByName")

    @field_validator("entered", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime field from VistA format"""
        return parse_datetime(v)

    @field_serializer("entered")
    def serialize_datetime_field(self, value: datetime | None) -> str | None:
        """Serialize datetime field to ISO format"""
        return format_datetime_for_mcp_response(value)


class Problem(BasePatientModel):
    """Patient Problem record - represents active and inactive medical problems"""

    uid: str
    local_id: str = Field(alias="localId")

    # Problem details
    problem_text: str = Field(alias="problemText")

    # ICD Code information
    icd_code: str | None = Field(None, alias="icdCode")
    icd_name: str | None = Field(None, alias="icdName")

    # Status and acuity
    status_code: str = Field(alias="statusCode")
    status_name: ProblemStatus = Field(alias="statusName")
    acuity_code: str | None = Field(None, alias="acuityCode")
    acuity_name: ProblemAcuity | None = Field(None, alias="acuityName")

    # Dates
    entered: datetime
    onset: datetime | None = None
    updated: datetime

    # Provider information
    provider_name: str | None = Field(None, alias="providerName")
    provider_uid: str | None = Field(None, alias="providerUid")

    # Location information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    location_uid: str | None = Field(None, alias="locationUid")
    location_name: str | None = Field(None, alias="locationName")

    # Service information
    service: str | None = None

    # Service connection
    service_connected: bool | None = Field(None, alias="serviceConnected")
    service_connection_percent: int | None = Field(
        None, alias="serviceConnectionPercent"
    )

    # Flags
    removed: bool = False
    unverified: bool = False

    # Comments
    comments: list[ProblemComment] = Field(default_factory=list)

    @field_validator("status_name", mode="before")
    @classmethod
    def convert_status_name(cls, v):
        """Convert string status to enum"""
        if isinstance(v, str):
            return ProblemStatus(v.upper())
        return v

    @field_validator("acuity_name", mode="before")
    @classmethod
    def convert_acuity_name(cls, v):
        """Convert string acuity to enum"""
        if v is not None and isinstance(v, str):
            try:
                v = ProblemAcuity(v.lower())
            except ValueError:
                v = ProblemAcuity.UNKNOWN
        return v

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("entered", "onset", "updated", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime field from VistA format"""
        if v is None:
            return None
        return parse_datetime(v)

    @field_serializer("entered", "onset", "updated")
    def serialize_datetime_field(self, value: datetime | None) -> str | None:
        """Serialize datetime field to ISO format"""
        return format_datetime_for_mcp_response(value)

    @property
    def is_active(self) -> bool:
        """Check if this problem is active"""
        return self.status_name == ProblemStatus.ACTIVE

    @property
    def is_inactive(self) -> bool:
        """Check if this problem is inactive"""
        return self.status_name == ProblemStatus.INACTIVE

    @property
    def is_chronic(self) -> bool:
        """Check if this problem is chronic"""
        return self.acuity_name == ProblemAcuity.CHRONIC

    @property
    def is_acute(self) -> bool:
        """Check if this problem is acute"""
        return self.acuity_name == ProblemAcuity.ACUTE

    @property
    def has_icd_code(self) -> bool:
        """Check if problem has an associated ICD code"""
        return self.icd_code is not None and self.icd_code.strip() != ""

    @property
    def is_service_connected(self) -> bool:
        """Check if this problem is service connected"""
        return self.service_connected is True

    @property
    def display_name(self) -> str:
        """Get display-friendly name with status indicator"""
        status_indicator = self.status_name.value
        return f"{self.problem_text} ({status_indicator})"


class ProblemSummary(BasePatientModel):
    """Summary statistics for patient problems"""

    total_problems: int = 0
    active_count: int = 0
    inactive_count: int = 0
    chronic_count: int = 0
    acute_count: int = 0
    service_connected_count: int = 0
    date_range_days: int | None = None
    most_recent_problem: datetime | None = None
    facilities: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    icd_codes: list[str] = Field(default_factory=list)

    @field_serializer("most_recent_problem")
    def serialize_most_recent_problem(self, value: datetime | None) -> str | None:
        """Serialize most recent problem datetime to ISO format"""
        return format_datetime_for_mcp_response(value)
