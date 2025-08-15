"""Patient demographics models"""

from datetime import UTC, date, datetime

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_date
from .base import BasePatientModel, Gender


class PatientAddress(BasePatientModel):
    """Patient address information"""

    street_line1: str = Field(alias="streetLine1")
    street_line2: str | None = Field(None, alias="streetLine2")
    city: str
    state_province: str = Field(alias="stateProvince")
    postal_code: str = Field(alias="postalCode")
    country: str | None = Field(default="USA")

    @field_validator("postal_code", mode="before")
    @classmethod
    def validate_postal_code(cls, v):
        """Handle numeric postal codes"""
        if v is None:
            return "00000"
        # Convert to string and pad with zeros
        postal = str(v).strip()
        if postal.isdigit() and len(postal) < 5:
            return postal.zfill(5)
        return postal


class PatientTelecom(BasePatientModel):
    """Patient contact information"""

    telecom: str  # Phone number or email
    usage_code: str = Field(alias="usageCode")  # HP, WP, MC, etc.
    usage_name: str = Field(alias="usageName")  # "home phone", "work place", etc.

    @property
    def is_phone(self) -> bool:
        """Check if this is a phone number"""
        return self.usage_code in ["HP", "WP", "MC", "CP"]

    @property
    def is_email(self) -> bool:
        """Check if this is an email"""
        return "@" in self.telecom

    @property
    def display_type(self) -> str:
        """Get display-friendly type"""
        type_map = {
            "HP": "Home",
            "WP": "Work",
            "MC": "Mobile",
            "CP": "Cell",
            "EM": "Email",
        }
        return type_map.get(self.usage_code, self.usage_name)


class PatientSupport(BasePatientModel):
    """Emergency contact / next of kin"""

    contact_type_code: str = Field(alias="contactTypeCode")  # urn:va:pat-contact:NOK
    contact_type_name: str = Field(alias="contactTypeName")  # "Next of Kin"
    name: str
    relationship: str | None = None
    phone: str | None = None

    @field_validator("contact_type_code", mode="before")
    @classmethod
    def clean_contact_code(cls, v):
        """Extract contact type from URN"""
        if v and ":" in v:
            # e.g., "urn:va:pat-contact:NOK" -> "NOK"
            return v.split(":")[-1]
        return v


class VeteranInfo(BasePatientModel):
    """Veteran-specific information"""

    is_veteran: bool = Field(alias="isVet")
    lrdfn: int | None = None
    service_connected: bool = Field(default=False, alias="serviceConnected")
    service_connection_percent: int = Field(default=0, alias="serviceConnectionPercent")
    service_period: str | None = None

    @field_validator("service_connection_percent", mode="before")
    @classmethod
    def validate_percent(cls, v):
        """Ensure percent is valid"""
        if v is None:
            return 0
        percent = int(v)
        return max(0, min(100, percent))  # Clamp to 0-100


class PatientFlag(BasePatientModel):
    """Patient flag/alert"""

    name: str
    text: str | None = None
    category: str | None = None

    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk flag"""
        if not self.name:
            return False
        high_risk_keywords = [
            "SUICIDE",
            "VIOLENCE",
            "BEHAVIORAL",
            "WANDERING",
            "FALL",
            "HIGH RISK",
        ]
        return any(keyword in self.name.upper() for keyword in high_risk_keywords)


class PatientDemographics(BasePatientModel):
    """Complete patient demographic information"""

    # Identifiers
    dfn: str | None = None  # May be set from parser context
    icn: str | None = None
    ssn: str
    brief_id: str | None = Field(None, alias="briefId")

    # Name
    full_name: str = Field(alias="fullName")
    family_name: str = Field(alias="familyName")
    given_names: str = Field(alias="givenNames")

    # Basic demographics
    date_of_birth: date = Field(alias="dateOfBirth")
    age: int | None = None
    gender_code: str = Field(alias="genderCode")
    gender_name: str = Field(alias="genderName")

    # Contact information
    addresses: list[PatientAddress] = Field(default_factory=list)
    telecoms: list[PatientTelecom] = Field(default_factory=list)

    # Additional demographics
    marital_status_code: str | None = None
    marital_status_name: str | None = None
    religion_code: str | None = Field(None, alias="religionCode")
    religion_name: str | None = Field(None, alias="religionName")
    races: list[dict[str, str]] | list[str] = Field(default_factory=list)
    ethnicities: list[dict[str, str]] | list[str] = Field(default_factory=list)
    language_code: str | None = Field(default="EN", alias="languageCode")
    language_name: str | None = Field(default="ENGLISH", alias="languageName")

    # Support network
    supports: list[PatientSupport] = Field(default_factory=list)

    # Veteran information
    veteran: VeteranInfo | None = None

    # Clinical metadata
    sensitive: bool = Field(default=False)
    flags: list[PatientFlag] = Field(default_factory=list)

    # Administrative
    eligibility_status: str | None = Field(None, alias="eligibilityStatus")
    primary_team: str | None = Field(None, alias="pcTeamName")
    primary_provider: str | None = None
    disability: list[dict] = Field(default_factory=list)
    exposures: list[dict] = Field(default_factory=list)
    facilities: list[dict] = Field(default_factory=list)
    pc_team_members: list[dict] = Field(default_factory=list, alias="pcTeamMembers")
    eligibility: list[dict] = Field(default_factory=list)

    @field_validator("gender_code", mode="before")
    @classmethod
    def clean_gender_code(cls, v):
        """Extract gender code from URN"""
        if v and ":" in v:
            # e.g., "urn:va:pat-gender:M" -> "M"
            return v.split(":")[-1]
        return v

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_date_of_birth(cls, v):
        """Parse date format"""
        # datetime is a subclass of date; check it first so we convert to date
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        return parse_date(v)

    @field_validator("ssn", mode="before")
    @classmethod
    def format_ssn(cls, v):
        """Ensure SSN is properly formatted"""
        if not v:
            return "***-**-****"
        ssn = str(v)
        # If it's already masked, return as is
        if "***" in ssn:
            return ssn
        # If it's numeric, format it
        if ssn.isdigit() and len(ssn) == 9:
            return f"{ssn[:3]}-{ssn[3:5]}-{ssn[5:]}"
        return ssn

    @field_validator("icn", mode="before")
    @classmethod
    def ensure_string_icn(cls, v):
        """Ensure ICN is string"""
        return str(v) if v is not None else None

    @field_validator("races", mode="before")
    @classmethod
    def parse_races(cls, v):
        """Parse race data which can be list of dicts or strings"""
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    race = item.get("race", "")
                    if race:
                        result.append(race)
                else:
                    result.append(str(item))
            return result
        return v

    @field_validator("ethnicities", mode="before")
    @classmethod
    def parse_ethnicities(cls, v):
        """Parse ethnicity data which can be list of dicts or strings"""
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    ethnicity = item.get("ethnicity", "")
                    if ethnicity:
                        result.append(ethnicity)
                else:
                    result.append(str(item))
            return result
        return v

    @field_validator("marital_status_code", "marital_status_name", mode="before")
    @classmethod
    def parse_marital_status(cls, v, info):
        """Parse marital status from maritalStatuses array"""
        if v is not None:
            return v

        # Check if we have maritalStatuses in the values
        values = info.data
        marital_statuses = values.get("maritalStatuses", [])
        if marital_statuses and isinstance(marital_statuses, list) and marital_statuses:
            status = marital_statuses[0]
            if isinstance(status, dict):
                if info.field_name == "marital_status_code":
                    code = status.get("code", "")
                    # Extract code from URN if present
                    if ":" in code:
                        return code.split(":")[-1]
                    return code
                else:  # marital_status_name
                    return status.get("name", "")
        return None

    @property
    def gender(self) -> Gender:
        """Get gender enum"""
        return Gender.from_code(self.gender_code)

    @property
    def primary_phone(self) -> str | None:
        """Get primary phone number"""
        for telecom in self.telecoms:
            if telecom.usage_code == "HP":
                return telecom.telecom
        # Fall back to any phone
        for telecom in self.telecoms:
            if telecom.is_phone:
                return telecom.telecom
        return None

    @property
    def mobile_phone(self) -> str | None:
        """Get mobile phone number"""
        for telecom in self.telecoms:
            if telecom.usage_code in ["MC", "CP"]:
                return telecom.telecom
        return None

    @property
    def email(self) -> str | None:
        """Get email address"""
        for telecom in self.telecoms:
            if telecom.is_email:
                return telecom.telecom
        return None

    @property
    def primary_address(self) -> PatientAddress | None:
        """Get primary address"""
        return self.addresses[0] if self.addresses else None

    @property
    def emergency_contact(self) -> PatientSupport | None:
        """Get primary emergency contact"""
        for support in self.supports:
            if support.contact_type_code in ["ECON", "EC"]:
                return support
        # Fall back to NOK
        for support in self.supports:
            if support.contact_type_code == "NOK":
                return support
        return None

    @property
    def has_high_risk_flags(self) -> bool:
        """Check if patient has any high-risk flags"""
        return any(flag.is_high_risk for flag in self.flags)

    def calculate_age(self, as_of: datetime | None = None) -> int:
        """Calculate patient age"""
        if as_of is None:
            as_of = datetime.now(UTC)

        age = as_of.year - self.date_of_birth.year

        # Adjust if birthday hasn't occurred this year
        if (as_of.month, as_of.day) < (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            age -= 1

        return age
