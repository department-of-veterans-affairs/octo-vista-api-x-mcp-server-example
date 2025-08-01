"""Order models for patient records"""

from datetime import datetime
from enum import Enum

from pydantic import Field, computed_field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..vista.clinical import Clinician
from .base import BasePatientModel

logger = get_logger()


class Order(BasePatientModel):
    """Order - represents a clinical order in VistA"""

    class OrderType(str, Enum):
        CONSULT = "CONSULT"
        MEDICATION = "MEDICATION"
        PROCEDURE = "PROCEDURE"
        LAB = "LAB"
        UNKNOWN = "UNKNOWN"

    uid: str
    local_id: str | None = Field(default=None, alias="localId")
    facility_code: str = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    entered: datetime | None  # Timestamp when order was entered
    service: str  # Service type (e.g., "LR", "GMRC", "PSO", "PSH")
    status_code: str = Field(alias="statusCode")  # e.g., "urn:va:order-status:comp"
    status: str = Field(alias="statusName")  # e.g., "COMPLETE", "ACTIVE"
    status_vuid: str = Field(alias="statusVuid")  # e.g., "urn:va:vuid:4501088"
    display_group: str = Field(alias="displayGroup")  # e.g., "CH", "CSLT", "O RX"
    content: str | None = None  # Order content/description
    name: str | None = None  # Order name
    oi_code: str | None = Field(
        default=None, alias="oiCode"
    )  # Orderable item code, e.g., "urn:va:oi:375"
    oi_name: str | None = Field(default=None, alias="oiName")  # Orderable item name
    oi_package_ref: str | None = Field(
        default=None, alias="oiPackageRef"
    )  # Package reference
    provider_name: str | None = Field(default=None, alias="providerName")
    provider_uid: str | None = Field(default=None, alias="providerUid")
    results: list[dict[str, str]] = Field(default_factory=list)  # Array of result UIDs
    start: datetime | None = None  # Start date/time (format varies)
    stop: datetime | None = None  # Stop date/time (can be empty)
    location_name: str | None = Field(default=None, alias="locationName")
    location_uid: str | None = Field(default=None, alias="locationUid")
    clinicians: list[Clinician] = Field(default_factory=list)
    successor: str | None = Field(
        default=None, alias="successor"
    )  # Successor order URN for discontinued orders

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """Check if order is currently active"""
        status = self.status
        return bool(status and status.upper() in ["ACTIVE", "PENDING", "SCHEDULED"])

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("start", "stop", "entered", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def order_type(self) -> OrderType:
        """Get order type"""
        match self.display_group:
            case "CH":
                return self.OrderType.LAB
            case "CSLT":
                return self.OrderType.CONSULT
            case "O RX" | "NV RX":
                return self.OrderType.MEDICATION
            case _:
                return self.OrderType.UNKNOWN

    @computed_field  # type: ignore[prop-decorator]
    @property
    def non_va_medication(self) -> bool | None:
        """Check if medication is a non-VA medication"""
        return bool(self.display_group and self.display_group.upper() == "NV RX")
