"""Vista clinical models"""

from datetime import datetime

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ..base import BaseVistaModel


class Clinician(BaseVistaModel):
    """Clinician information for orders and consults"""

    name: str
    role: str  # e.g., "S" for Signer
    signature: str | None = Field(default=None)  # Electronic signature text
    signed_date_time: datetime | None = Field(default=None, alias="signedDateTime")
    uid: str

    @field_validator("signed_date_time", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        return parse_datetime(v)
