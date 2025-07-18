"""Vista patient models"""

from typing import Any

from pydantic import Field

from ..base import BaseVistaModel


class PatientSearchResult(BaseVistaModel):
    """Patient search result"""

    dfn: str = Field(..., description="Patient DFN (internal ID)")
    name: str = Field(..., description="Patient name (LAST,FIRST)")
    ssn_last_four: str = Field(..., description="Last 4 digits of SSN")
    date_of_birth: str | None = Field(None, description="Date of birth")
    gender: str | None = Field(None, description="Gender (M/F)")
    sensitive: bool = Field(False, description="Sensitive patient flag")
    station: str = Field(..., description="Station number")


class PatientDemographics(BaseVistaModel):
    """Detailed patient demographics"""

    dfn: str = Field(..., description="Patient DFN")
    name: str = Field(..., description="Full name")
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    ssn: str = Field(..., description="Masked SSN")
    date_of_birth: str
    age: int | None = None
    gender: str | None = None
    marital_status: str | None = None
    phone: str | None = None
    cell_phone: str | None = None
    email: str | None = None
    address: dict[str, str] | None = None
    emergency_contact: dict[str, str] | None = None
    insurance: list[dict[str, str]] | None = None
    veteran_status: dict[str, Any] | None = None
    station: str
