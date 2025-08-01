"""Document models for patient records"""

from datetime import datetime
from enum import Enum

from pydantic import Field, computed_field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..vista.clinical import Clinician
from .base import BasePatientModel

logger = get_logger()


class DocumentTitle(BasePatientModel):
    """National document title information"""

    title: str
    vuid: str


class DocumentTitleRole(BasePatientModel):
    """National document title role information"""

    role: str
    vuid: str


class DocumentTitleSubject(BasePatientModel):
    """National document title subject information"""

    subject: str
    vuid: str


class DocumentTitleType(BasePatientModel):
    """National document title type information"""

    type: str
    vuid: str


class DocumentText(BasePatientModel):
    """Document text content with clinician information"""

    uid: str
    content: str
    date_time: datetime = Field(alias="dateTime")
    status: str
    clinicians: list[Clinician] = Field(default_factory=list)

    @field_validator("date_time", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)


class Document(BasePatientModel):
    """Document - represents a clinical document in VistA"""

    class DocumentClass(str, Enum):
        PROGRESS_NOTES = "PROGRESS NOTES"
        DISCHARGE_SUMMARY = "DISCHARGE SUMMARY"
        CONSULT = "CONSULT"
        PROCEDURE = "PROCEDURE"
        UNKNOWN = "UNKNOWN"

    uid: str
    local_id: str | None = Field(default=None, alias="localId")
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Document classification
    document_class: str = Field(alias="documentClass")
    document_type_code: str = Field(alias="documentTypeCode")
    document_type_name: str = Field(alias="documentTypeName")

    # Titles and metadata
    local_title: str | None = Field(default=None, alias="localTitle")
    national_title: DocumentTitle | None = Field(default=None, alias="nationalTitle")
    national_title_role: DocumentTitleRole | None = Field(
        default=None, alias="nationalTitleRole"
    )
    national_title_subject: DocumentTitleSubject | None = Field(
        default=None, alias="nationalTitleSubject"
    )
    national_title_type: DocumentTitleType | None = Field(
        default=None, alias="nationalTitleType"
    )

    # Encounter information
    encounter_name: str | None = Field(default=None, alias="encounterName")
    encounter_uid: str | None = Field(default=None, alias="encounterUid")

    # Timestamps
    entered: datetime | None = None  # When document was entered
    reference_date_time: datetime | None = Field(
        default=None, alias="referenceDateTime"
    )

    # Status
    status_name: str = Field(alias="statusName")

    # Document content
    text: list[DocumentText] = Field(default_factory=list)

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("entered", "reference_date_time", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_completed(self) -> bool:
        """Check if document is completed"""
        return bool(self.status_name and self.status_name.upper() == "COMPLETED")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def document_type(self) -> DocumentClass:
        """Get document class as enum"""
        match self.document_class.upper():
            case "PROGRESS NOTES":
                return self.DocumentClass.PROGRESS_NOTES
            case "DISCHARGE SUMMARY":
                return self.DocumentClass.DISCHARGE_SUMMARY
            case "CONSULT":
                return self.DocumentClass.CONSULT
            case "PROCEDURE":
                return self.DocumentClass.PROCEDURE
            case _:
                return self.DocumentClass.UNKNOWN

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_signature(self) -> bool:
        """Check if document has been signed"""
        for text_item in self.text:
            for clinician in text_item.clinicians:
                if clinician.role == "S" and hasattr(clinician, "signature"):
                    return True
        return False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def primary_author(self) -> str | None:
        """Get the primary author of the document"""
        for text_item in self.text:
            for clinician in text_item.clinicians:
                if clinician.role == "A":  # Author role
                    return clinician.name
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def content_summary(self) -> str:
        """Get a summary of the document content"""
        if not self.text:
            return ""

        # Combine all content from text items
        content_parts = []
        for text_item in self.text:
            if text_item.content:
                # Take first 200 characters as summary
                content = text_item.content.strip()
                if len(content) > 200:
                    content = content[:200] + "..."
                content_parts.append(content)

        return " | ".join(content_parts)

    @property
    def is_progress_note(self) -> bool:
        """Check if this is a progress note"""
        return self.document_type == self.DocumentClass.PROGRESS_NOTES

    @property
    def is_consult_note(self) -> bool:
        """Check if this is a consult note"""
        return self.document_type == self.DocumentClass.CONSULT
