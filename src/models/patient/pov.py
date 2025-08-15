"""Purpose of Visit (POV) models for patient records"""

from datetime import datetime
from enum import Enum

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response
from .base import BasePatientModel

logger = get_logger()


class POVType(str, Enum):
    """POV (Purpose of Visit) type enumeration"""

    PRIMARY = "P"
    SECONDARY = "S"


class PurposeOfVisit(BasePatientModel):
    """Purpose of Visit (POV) record - represents diagnoses/conditions associated with encounters"""

    uid: str
    local_id: str = Field(alias="localId")

    # POV details
    name: str  # Diagnosis/condition name
    pov_type: POVType = Field(alias="type")  # Primary or Secondary
    narrative: str | None = None  # Additional description

    # ICD Code information (if available)
    icd_code: str | None = Field(None, alias="icdCode")
    icd_name: str | None = Field(None, alias="icdName")

    # Encounter association
    encounter_name: str = Field(alias="encounterName")
    encounter_uid: str = Field(alias="encounterUid")
    entered: datetime

    # Provider information
    provider_name: str | None = Field(None, alias="providerName")
    provider_uid: str | None = Field(None, alias="providerUid")

    # Location information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    location_uid: str | None = Field(None, alias="locationUid")
    location_name: str | None = Field(None, alias="locationName")

    @field_validator("pov_type", mode="before")
    @classmethod
    def convert_pov_type(cls, v):
        """Convert string POV type to enum"""
        if isinstance(v, str):
            if v.upper() == "P":
                return POVType.PRIMARY
            elif v.upper() == "S":
                return POVType.SECONDARY
            else:
                return POVType.PRIMARY  # Default fallback
        return v

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("entered", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime field from VistA format"""
        return parse_datetime(v)

    @field_serializer("entered")
    def serialize_datetime_field(self, value: datetime | None) -> str | None:
        """Serialize datetime field to ISO format"""
        return format_datetime_for_mcp_response(value)

    @property
    def is_primary(self) -> bool:
        """Check if this is a primary diagnosis"""
        return self.pov_type == POVType.PRIMARY

    @property
    def is_secondary(self) -> bool:
        """Check if this is a secondary diagnosis"""
        return self.pov_type == POVType.SECONDARY

    @property
    def has_icd_code(self) -> bool:
        """Check if POV has an associated ICD code"""
        return self.icd_code is not None and self.icd_code.strip() != ""

    @property
    def display_name(self) -> str:
        """Get display-friendly name with type indicator"""
        type_indicator = "Primary" if self.is_primary else "Secondary"
        return f"{self.name} ({type_indicator})"


class POVSummary(BasePatientModel):
    """Summary statistics for patient POVs"""

    total_povs: int = 0
    primary_count: int = 0
    secondary_count: int = 0
    unique_encounters: int = 0
    date_range_days: int | None = None
    most_recent_pov: datetime | None = None
    facilities: list[str] = Field(default_factory=list)
    encounter_types: list[str] = Field(default_factory=list)

    @field_serializer("most_recent_pov")
    def serialize_most_recent_pov(self, value: datetime | None) -> str | None:
        """Serialize most recent POV datetime to ISO format"""
        return format_datetime_for_mcp_response(value)
