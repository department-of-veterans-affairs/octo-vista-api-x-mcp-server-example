from datetime import datetime

from pydantic import BaseModel, Field, computed_field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from .base import BasePatientModel


class MedicationDosage(BaseModel):
    """Represents dosage information for a medication"""

    dose: str | None = Field(default=None)
    relative_start: int | None = Field(default=None, alias="relativeStart")
    relative_stop: int | None = Field(default=None, alias="relativeStop")
    route_name: str | None = Field(default=None, alias="routeName")
    schedule_freq: int | None = Field(default=None, alias="scheduleFreq")
    schedule_name: str | None = Field(default=None, alias="scheduleName")
    schedule_type: str | None = Field(default=None, alias="scheduleType")
    start: datetime | None = Field(default=None)
    stop: datetime | None = Field(default=None)
    units: str | None = Field(default=None)

    @field_validator(
        "units",
        "schedule_type",
        "schedule_name",
        "route_name",
        "dose",
        mode="before",
    )
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("start", "stop", mode="before")
    @classmethod
    def validate_int_dates(cls, v):
        """Validate date fields from VistA format"""
        return parse_datetime(v)


class MedicationFill(BaseModel):
    """Represents a medication fill/dispense event"""

    days_supply_dispensed: int | None = Field(default=None, alias="daysSupplyDispensed")
    dispense_date: datetime | None = Field(default=None, alias="dispenseDate")
    quantity_dispensed: int | None = Field(default=None, alias="quantityDispensed")
    release_date: datetime | None = Field(default=None, alias="releaseDate")
    routing: str | None = Field(default=None)

    @field_validator("routing", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("dispense_date", "release_date", mode="before")
    @classmethod
    def validate_int_dates(cls, v):
        """Validate date fields from VistA format"""
        return parse_datetime(v)


class MedicationOrder(BaseModel):
    """Represents a medication order/prescription"""

    days_supply: int | None = Field(default=None, alias="daysSupply")
    fill_cost: float | None = Field(default=None, alias="fillCost")
    fills_allowed: int | None = Field(default=None, alias="fillsAllowed")
    fills_remaining: int | None = Field(default=None, alias="fillsRemaining")
    location_name: str | None = Field(default=None, alias="locationName")
    location_uid: str | None = Field(default=None, alias="locationUid")
    order_uid: str = Field(default="", alias="orderUid")
    ordered: datetime | None = Field(default=None)
    pharmacist_name: str | None = Field(default=None, alias="pharmacistName")
    pharmacist_uid: str | None = Field(default=None, alias="pharmacistUid")
    prescription_id: str | None = Field(default=None, alias="prescriptionId")
    provider_name: str | None = Field(default=None, alias="providerName")
    provider_uid: str | None = Field(default=None, alias="providerUid")
    quantity_ordered: int | None = Field(default=None, alias="quantityOrdered")
    va_routing: str | None = Field(default=None, alias="vaRouting")

    @field_validator(
        "prescription_id",
        "location_name",
        "location_uid",
        "order_uid",
        "pharmacist_name",
        "pharmacist_uid",
        "provider_name",
        "provider_uid",
        "va_routing",
        mode="before",
    )
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("ordered", mode="before")
    @classmethod
    def validate_int_dates(cls, v):
        """Validate date fields from VistA format"""
        return parse_datetime(v)


class MedicationProduct(BaseModel):
    """Represents a medication product with its details"""

    drug_class_code: str | None = Field(default=None, alias="drugClassCode")
    drug_class_name: str | None = Field(default=None, alias="drugClassName")
    ingredient_code: str | None = Field(default=None, alias="ingredientCode")
    ingredient_code_name: str | None = Field(default=None, alias="ingredientCodeName")
    ingredient_name: str | None = Field(default=None, alias="ingredientName")
    ingredient_role: str | None = Field(default=None, alias="ingredientRole")
    strength: str | None = Field(default=None)
    supplied_code: str | None = Field(default=None, alias="suppliedCode")
    supplied_name: str | None = Field(default=None, alias="suppliedName")

    @field_validator(
        "drug_class_code",
        "drug_class_name",
        "ingredient_code",
        "ingredient_code_name",
        "ingredient_name",
        "ingredient_role",
        "supplied_code",
        "supplied_name",
        mode="before",
    )
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""


class Medication(BasePatientModel):
    """Patient medication record from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # Medication identification
    name: str
    qualified_name: str = Field(alias="qualifiedName")
    med_type: str = Field(alias="medType")
    product_form_name: str = Field(alias="productFormName")

    # Status and type
    med_status: str = Field(alias="medStatus")
    med_status_name: str = Field(alias="medStatusName")
    va_status: str = Field(alias="vaStatus")
    va_type: str = Field(alias="vaType")
    type: str | None = None
    indication: str | None = Field(default=None)

    # Dosage and administration
    sig: str = ""
    patient_instruction: str | None = Field(default=None, alias="patientInstruction")
    dosages: list[MedicationDosage] = Field(default_factory=list)

    # Orders and fills
    orders: list[MedicationOrder] = Field(default_factory=list)
    fills: list[MedicationFill] = Field(default_factory=list)

    # Products and ingredients
    products: list[MedicationProduct] = Field(default_factory=list)

    # Facility information
    facility_code: str = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Dates
    start_date: datetime | None = Field(default=None, alias="overallStart")
    end_date: datetime | None = Field(default=None, alias="overallStop")
    last_filled: datetime | None = Field(default=None, alias="lastFilled")
    stopped: datetime | None = Field(default=None)

    @field_validator(
        "local_id",
        "facility_code",
        "sig",
        "type",
        "va_type",
        "patient_instruction",
        mode="before",
    )
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("start_date", "end_date", "last_filled", "stopped", mode="before")
    @classmethod
    def validate_int_dates(cls, v):
        """Validate date fields from VistA format"""
        return parse_datetime(v)

    @property
    def is_active(self) -> bool:
        """Check if the medication is active"""
        va_status = self.va_status.upper()
        return va_status.upper().startswith("ACTIVE")

    @property
    def is_pending(self) -> bool:
        """Check if the medication is pending"""
        va_status = self.va_status.upper()
        return va_status.upper().startswith("PENDING")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dose(self) -> str:
        """Get the dose of the medication"""
        try:
            return self.dosages[0].dose or ""
        except (AttributeError, IndexError):
            return ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def route(self) -> str:
        """Get the route of the medication"""
        try:
            return self.dosages[0].route_name or ""
        except (AttributeError, IndexError):
            return ""
