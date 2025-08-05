"""CPT Code data models for patient records"""

from datetime import datetime

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from .base import BasePatientModel

logger = get_logger()


class CPTCode(BasePatientModel):
    """Patient CPT procedure code from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # CPT Code identification
    cpt_code: str = Field(alias="cptCode")
    description: str = Field(alias="name", default="")
    category: str | None = Field(None, alias="categoryName")

    # Procedure details
    procedure_date: datetime = Field(alias="dateTime")
    provider: str | None = Field(None, alias="providerName")
    provider_uid: str | None = Field(None, alias="providerUid")
    quantity: int = Field(default=1)
    modifiers: list[str] | None = Field(default=None)

    # Associated visit/encounter
    associated_visit_uid: str | None = Field(None, alias="encounterUid")
    encounter_name: str | None = Field(None, alias="encounterName")

    # Location information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    location_name: str | None = Field(None, alias="locationName")
    location_uid: str | None = Field(None, alias="locationUid")

    # Status and type
    status: str = Field(default="completed")
    kind: str = Field(default="Procedure")

    # Additional context
    comments: str | None = Field(None, alias="comment")
    summary: str | None = None

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("procedure_date", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @field_validator("cpt_code", mode="before")
    @classmethod
    def normalize_cpt_code(cls, v):
        """Extract CPT code from URN format"""
        if not v:
            return ""
        # Handle URN format: "urn:cpt:82950" -> "82950"
        if isinstance(v, str) and v.startswith("urn:cpt:"):
            return v.split(":")[-1]
        return str(v)

    @field_validator("modifiers", mode="before")
    @classmethod
    def parse_modifiers(cls, v):
        """Parse CPT modifiers from various formats"""
        if v is None:
            return None
        if isinstance(v, str):
            # Handle comma-separated or space-separated modifiers
            modifiers = [m.strip() for m in v.replace(",", " ").split() if m.strip()]
            return modifiers if modifiers else None
        if isinstance(v, list):
            return [str(m).strip() for m in v if str(m).strip()]
        return None

    @property
    def procedure_category(self) -> str:
        """Categorize procedure by CPT code range"""
        from ...services.validators.cpt_validators import categorize_cpt_code

        return categorize_cpt_code(self.cpt_code, self.description)

    @property
    def is_surgical(self) -> bool:
        """Check if this is a surgical procedure"""
        return self.procedure_category in ["surgery", "surgical"]

    @property
    def is_diagnostic(self) -> bool:
        """Check if this is a diagnostic procedure"""
        return self.procedure_category in ["diagnostic", "radiology", "pathology"]

    @property
    def display_name(self) -> str:
        """Get display-friendly procedure name"""
        if self.description:
            return f"{self.cpt_code} - {self.description}"
        return self.cpt_code

    @property
    def has_modifiers(self) -> bool:
        """Check if procedure has modifiers"""
        return bool(self.modifiers and len(self.modifiers) > 0)
