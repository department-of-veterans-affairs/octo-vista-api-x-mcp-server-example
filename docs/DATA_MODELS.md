# Data Models Reference

This document provides a comprehensive reference for all data models used in the Vista API MCP Server.

## Table of Contents

1. [Overview](#overview)
2. [Base Models](#base-models)
3. [Patient Demographics](#patient-demographics)
4. [Clinical Data Models](#clinical-data-models)
5. [Visit and Appointment Models](#visit-and-appointment-models)
6. [Administrative Models](#administrative-models)
7. [Response Models](#response-models)
8. [Enums and Constants](#enums-and-constants)
9. [Data Collection](#data-collection)
10. [Example JSON Structures](#example-json-structures)

## Overview

The Vista API MCP Server uses a comprehensive set of Pydantic models to represent patient data from VistA systems. All models inherit from `BasePatientModel` and follow consistent patterns for validation, serialization, and data handling.

### Key Design Principles

- **Type Safety**: All models use Pydantic for runtime type validation
- **HIPAA Compliance**: Sensitive data is automatically masked in logs
- **VistA Compatibility**: Models map directly to VistA data structures
- **MCP Integration**: Models are optimized for MCP tool responses
- **Extensibility**: Easy to add new fields and models

## Base Models

### BaseVistaModel

The root base class for all models in the system.

```python
class BaseVistaModel(BaseModel):
    """Base model that excludes None values from serialization by default"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        strict=True,
        str_strip_whitespace=True,
    )
```

**Key Features:**
- Excludes `None` values from JSON serialization
- Supports field aliases for VistA compatibility
- Automatic string trimming
- Enum value serialization

### BasePatientModel

Base class for all patient-related data models.

```python
class BasePatientModel(BaseVistaModel):
    """Base model for all patient data models"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        ser_json_timedelta="iso8601",
        json_schema_serialization_defaults_required=True,
    )
```

**Key Features:**
- ISO 8601 datetime serialization
- Field name and alias population
- JSON schema compliance

## Patient Demographics

### PatientDemographics

Complete patient demographic information.

```python
class PatientDemographics(BasePatientModel):
    # Identifiers
    dfn: str | None = None
    icn: str | None = None
    ssn: str
    brief_id: str | None = None
    
    # Name
    full_name: str
    family_name: str
    given_names: str
    
    # Basic demographics
    date_of_birth: date
    gender_code: str
    gender_name: str
    
    # Contact information
    addresses: list[PatientAddress] = []
    telecoms: list[PatientTelecom] = []
    
    # Additional demographics
    marital_status_code: str | None = None
    marital_status_name: str | None = None
    religion_code: str | None = None
    religion_name: str | None = None
    races: list[dict[str, str]] | list[str] = []
    ethnicities: list[dict[str, str]] | list[str] = []
    language_code: str | None = "EN"
    language_name: str | None = "ENGLISH"
    
    # Support network
    supports: list[PatientSupport] = []
    
    # Veteran information
    veteran: VeteranInfo | None = None
    
    # Clinical metadata
    sensitive: bool = False
    flags: list[PatientFlag] = []
    
    # Administrative
    eligibility_status: str | None = None
    primary_team: str | None = None
    primary_provider: str | None = None
    disability: list[dict] = []
    exposures: list[dict] = []
    facilities: list[dict] = []
    pc_team_members: list[dict] = []
```

### PatientAddress

Patient address information.

```python
class PatientAddress(BasePatientModel):
    street_line1: str
    street_line2: str | None = None
    city: str
    state_province: str
    postal_code: str
    country: str | None = "USA"
```

### PatientTelecom

Patient contact information (phone, email).

```python
class PatientTelecom(BasePatientModel):
    telecom: str  # Phone number or email
    usage_code: str  # HP, WP, MC, etc.
    usage_name: str  # "home phone", "work place", etc.
    
    @property
    def is_phone(self) -> bool:
        """Check if this is a phone number"""
        
    @property
    def is_email(self) -> bool:
        """Check if this is an email"""
```

### VeteranInfo

Veteran-specific information.

```python
class VeteranInfo(BasePatientModel):
    service_connected: bool = False
    service_connection_percent: int | None = None
    discharge_status: str | None = None
    discharge_date: date | None = None
    branch_of_service: str | None = None
    rank: str | None = None
    combat_zone: bool = False
    pow_status: bool = False
    exposure_indicators: list[str] = []
```

## Clinical Data Models

### VitalSign

Vital sign measurements.

```python
class VitalSign(BasePatientModel):
    uid: str
    local_id: str
    
    # Measurement info
    type_code: str
    type_name: str
    display_name: str
    
    # Results
    result: str  # Original string value (e.g., "135/100")
    systolic: int | None = None  # For BP
    diastolic: int | None = None  # For BP
    units: str | None = None
    
    # Reference ranges
    high: float | str | None = None
    low: float | str | None = None
    
    # Metadata
    observed: datetime
    resulted: datetime
    entered_by: str | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    location_uid: str | None = None
    location_name: str | None = None
    
    # Interpretation
    interpretation_code: str | None = None
    interpretation_name: str | None = None
    
    @property
    def is_abnormal(self) -> bool:
        """Check if vital sign is abnormal"""
        
    @property
    def is_critical(self) -> bool:
        """Check if vital sign is critical"""
        
    @property
    def display_value(self) -> str:
        """Get display-friendly value with units"""
```

### LabResult

Laboratory test results.

```python
class LabResult(BasePatientModel):
    uid: str
    local_id: str
    
    # Test information
    type_code: str  # LOINC code
    type_name: str  # "GLUCOSE"
    display_name: str | None = None
    
    # Results
    result: str | None = None
    units: str | None = None
    
    # Reference ranges
    high: float | str | None = None
    low: float | str | None = None
    
    # Interpretation
    interpretation_code: str | None = None
    interpretation_name: str | None = None
    
    # Grouping
    group_name: str | None = None
    group_uid: str | None = None
    
    # Metadata
    observed: datetime
    resulted: datetime
    verified: datetime | None = None
    
    # Order info
    order_uid: str | None = None
    lab_order_id: str | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    
    # Sample info
    specimen: str | None = None
    sample: str | None = None
    
    # Status
    status_code: str
    status_name: str
    
    # Additional info
    comment: str | None = None
    
    @property
    def is_abnormal(self) -> bool:
        """Check if lab result is abnormal"""
        
    @property
    def is_critical(self) -> bool:
        """Check if result is critically high or low"""
```

### Medication

Patient medication records.

```python
class Medication(BasePatientModel):
    uid: str
    local_id: str
    
    # Medication identification
    name: str
    qualified_name: str
    med_type: str
    product_form_name: str
    
    # Status and type
    med_status: str
    med_status_name: str
    va_status: str
    va_type: str
    type: str | None = None
    indication: str | None = None
    
    # Dosage and administration
    sig: str = ""
    patient_instruction: str | None = None
    dosages: list[MedicationDosage] = []
    
    # Orders and fills
    orders: list[MedicationOrder] = []
    fills: list[MedicationFill] = []
    
    # Products and ingredients
    products: list[MedicationProduct] = []
    
    # Facility information
    facility_code: str
    facility_name: str
    
    # Dates
    start_date: datetime | None = None
    end_date: datetime | None = None
    last_filled: datetime | None = None
    stopped: datetime | None = None
    
    @property
    def is_active(self) -> bool:
        """Check if the medication is active"""
        
    @property
    def is_pending(self) -> bool:
        """Check if the medication is pending"""
        
    @property
    def dose(self) -> str:
        """Get the dose of the medication"""
        
    @property
    def route(self) -> str:
        """Get the route of the medication"""
```

### Problem

Patient medical problems.

```python
class Problem(BasePatientModel):
    uid: str
    local_id: str
    
    # Problem details
    problem_text: str
    
    # ICD Code information
    icd_code: str | None = None
    icd_name: str | None = None
    
    # Status and acuity
    status_code: str
    status_name: ProblemStatus
    acuity_code: str | None = None
    acuity_name: ProblemAcuity | None = None
    
    # Dates
    entered: datetime
    onset: datetime | None = None
    updated: datetime
    
    # Provider information
    provider_name: str | None = None
    provider_uid: str | None = None
    
    # Location information
    facility_code: str | int
    facility_name: str
    location_uid: str | None = None
    location_name: str | None = None
    
    # Service information
    service: str | None = None
    
    # Service connection
    service_connected: bool | None = None
    service_connection_percent: int | None = None
    
    # Flags
    removed: bool = False
    unverified: bool = False
    
    # Comments
    comments: list[ProblemComment] = []
    
    @property
    def is_active(self) -> bool:
        """Check if problem is active"""
        
    @property
    def is_chronic(self) -> bool:
        """Check if problem is chronic"""
```

### Consult

Consultation records.

```python
class Consult(BasePatientModel):
    uid: str
    local_id: str
    
    # Consult details
    service: str  # "CARDIOLOGY"
    type_name: str  # "CARDIOLOGY Cons"
    order_name: str  # "CARDIOLOGY"
    order_uid: str
    
    # Status
    status_name: str  # "PENDING", "SCHEDULED", etc.
    urgency: str = "Routine"  # "Routine", "Urgent", "STAT"
    
    # Dates
    date_time: datetime  # Order date
    scheduled_date: datetime | None = None
    completed_date: datetime | None = None
    
    # Provider info
    provider_uid: str | None = None
    provider_name: str | None = None
    requesting_provider: str | None = None
    
    # Clinical info
    reason: str | None = None
    provisional_dx: ProvisionalDx | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    
    # Type
    consult_procedure: str = "Consult"
    category: str = "C"
    
    @property
    def is_active(self) -> bool:
        """Check if consult is active"""
        
    @property
    def is_overdue(self) -> bool:
        """Check if consult is overdue"""
```

### Allergy

Patient allergy information.

```python
class Allergy(BasePatientModel):
    uid: str
    local_id: str
    
    # Allergy details
    allergen_name: str
    allergen_type: str
    reaction: str | None = None
    severity: str | None = None
    
    # Status
    status: str  # "ACTIVE", "INACTIVE"
    verified: bool = False
    
    # Dates
    entered: datetime
    verified_date: datetime | None = None
    
    # Provider info
    entered_by: str | None = None
    verified_by: str | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    
    # Products and reactions
    products: list[AllergyProduct] = []
    reactions: list[AllergyReaction] = []
    
    @property
    def is_active(self) -> bool:
        """Check if allergy is active"""
```

## Visit and Appointment Models

### Visit

Patient visit records.

```python
class Visit(BasePatientModel):
    uid: str
    local_id: str
    
    # Visit details
    visit_type: VisitType
    visit_date: datetime
    discharge_date: datetime | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    location_uid: str | None = None
    location_name: str | None = None
    
    # Provider info
    attending_provider: str | None = None
    attending_provider_uid: str | None = None
    
    # Clinical info
    chief_complaint: str | None = None
    diagnosis: str | None = None
    
    # Administrative
    patient_class: str | None = None
    admission_source: str | None = None
    discharge_disposition: str | None = None
    
    @property
    def is_inpatient(self) -> bool:
        """Check if this is an inpatient visit"""
        
    @property
    def duration_days(self) -> int | None:
        """Calculate visit duration in days"""
```

### Appointment

Patient appointment records.

```python
class Appointment(BasePatientModel):
    uid: str
    local_id: str
    
    # Basic appointment info
    appointment_date: datetime
    category: AppointmentCategory | None = None
    status: AppointmentStatus
    
    # Facility information
    facility: FacilityInfo
    
    # Location information
    location_name: str | None = None
    location_uid: str | None = None
    
    # Patient classification
    patient_class: AppointmentPatientClass | None = None
    
    # Provider information
    providers: list[AppointmentProvider] = []
    
    # Appointment details
    stop_code: AppointmentStopCode | None = None
    named_type: AppointmentNamedType | None = None
    
    # Clinical info
    chief_complaint: str | None = None
    reason: str | None = None
    
    # Administrative
    appointment_length: int | None = None  # minutes
    comment: str | None = None
    
    @property
    def is_future(self) -> bool:
        """Check if appointment is in the future"""
        
    @property
    def is_past(self) -> bool:
        """Check if appointment is in the past"""
```

## Administrative Models

### Order

Medical orders.

```python
class Order(BasePatientModel):
    uid: str
    local_id: str
    
    # Order details
    order_name: str
    order_text: str
    order_type: str
    
    # Status
    status: str
    status_name: str
    
    # Dates
    ordered: datetime
    start_date: datetime | None = None
    stop_date: datetime | None = None
    
    # Provider info
    ordering_provider: str | None = None
    ordering_provider_uid: str | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    
    # Clinical info
    indication: str | None = None
    comment: str | None = None
    
    @property
    def is_active(self) -> bool:
        """Check if order is active"""
```

### Document

Clinical documents.

```python
class Document(BasePatientModel):
    uid: str
    local_id: str
    
    # Document details
    title: str
    document_type: str
    status: str
    
    # Content
    text: DocumentText | None = None
    
    # Dates
    authored: datetime
    signed: datetime | None = None
    
    # Provider info
    author: str | None = None
    author_uid: str | None = None
    signer: str | None = None
    signer_uid: str | None = None
    
    # Location
    facility_code: str | int
    facility_name: str
    
    # Administrative
    encounter_uid: str | None = None
    visit_uid: str | None = None
```

## Response Models

### ToolResponse

Standard response format for all MCP tools.

```python
class ToolResponse(BaseVistaModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    error_code: str | None = None
    total_item_count: int | None = None
    metadata: ResponseMetadata | None = None
    
    @property
    def is_error(self) -> bool:
        return not self.success
```

### ResponseMetadata

Metadata included in all responses.

```python
class ResponseMetadata(BaseVistaModel):
    # Request info
    request_id: str | None = None
    timestamp: datetime
    duration_ms: int
    
    # Vista context
    station: str
    duz: str | None = None
    
    # Performance metrics
    performance: PerformanceMetrics | None = None
    
    # RPC details
    rpc: dict[str, Any] | None = None
    
    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / 1000
```

## Enums and Constants

### Gender

```python
class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"
```

### InterpretationCode

Lab/vital interpretation codes (HL7 standard).

```python
class InterpretationCode(str, Enum):
    HIGH = "H"
    LOW = "L"
    CRITICAL_HIGH = "HH"
    CRITICAL_LOW = "LL"
    ABNORMAL = "A"
    NORMAL = "N"
```

### ConsultStatus

```python
class ConsultStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISCONTINUED = "DISCONTINUED"
```

### VitalType

```python
class VitalType(str, Enum):
    BP = "BLOOD PRESSURE"
    TEMP = "TEMPERATURE"
    PULSE = "PULSE"
    RESP = "RESPIRATION"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    PAIN = "PAIN"
    O2_SAT = "PULSE OXIMETRY"
```

## Data Collection

### PatientDataCollection

Main model that organizes all patient data.

```python
class PatientDataCollection(BasePatientModel):
    # Core demographics - always present
    demographics: PatientDemographics
    
    # Clinical data - stored as dictionaries for O(1) lookups by ID
    vital_signs_dict: dict[str, VitalSign] = {}
    lab_results_dict: dict[str, LabResult] = {}
    consults_dict: dict[str, Consult] = {}
    medications_dict: dict[str, Medication] = {}
    visits_dict: dict[str, Visit] = {}
    health_factors_dict: dict[str, HealthFactor] = {}
    treatments_dict: dict[str, Treatment] = {}
    diagnoses_dict: dict[str, Diagnosis] = {}
    orders_dict: dict[str, Order] = {}
    documents_dict: dict[str, Document] = {}
    cpt_codes_dict: dict[str, CPTCode] = {}
    allergies_dict: dict[str, Allergy] = {}
    povs_dict: dict[str, PurposeOfVisit] = {}
    problems_dict: dict[str, Problem] = {}
    appointments_dict: dict[str, Appointment] = {}
    
    # Metadata
    source_station: str
    source_icn: str
    retrieved_at: datetime
    cache_version: str = "1.0"
    total_items: int = 0
    
    @property
    def all_items(self) -> dict[str, BasePatientModel]:
        """Get all items in the collection"""
        
    @property
    def patient_name(self) -> str:
        """Convenience property for patient name"""
        
    @property
    def patient_icn(self) -> str:
        """Convenience property for patient ICN"""
```

## Example JSON Structures

### Patient Demographics Example

```json
{
  "dfn": "100022",
  "icn": "1000220000V123456",
  "ssn": "***-**-1234",
  "full_name": "ANDERSON,JAMES ROBERT",
  "family_name": "ANDERSON",
  "given_names": "JAMES ROBERT",
  "date_of_birth": "1955-03-15",
  "gender_code": "M",
  "gender_name": "MALE",
  "addresses": [
    {
      "street_line1": "123 Main St",
      "city": "Washington",
      "state_province": "DC",
      "postal_code": "20001",
      "country": "USA"
    }
  ],
  "telecoms": [
    {
      "telecom": "(555) 123-4567",
      "usage_code": "HP",
      "usage_name": "home phone"
    }
  ],
  "veteran": {
    "service_connected": true,
    "service_connection_percent": 50,
    "branch_of_service": "ARMY"
  }
}
```

### Vital Sign Example

```json
{
  "uid": "vital-123",
  "local_id": "12345",
  "type_code": "8480-6",
  "type_name": "BLOOD PRESSURE",
  "display_name": "Blood Pressure",
  "result": "135/100",
  "systolic": 135,
  "diastolic": 100,
  "units": "mmHg",
  "high": "140",
  "low": "90",
  "observed": "2025-01-07T14:30:00Z",
  "resulted": "2025-01-07T14:30:00Z",
  "facility_code": "500",
  "facility_name": "Washington DC VAMC",
  "interpretation_code": "H",
  "interpretation_name": "HIGH"
}
```

### Medication Example

```json
{
  "uid": "med-456",
  "local_id": "67890",
  "name": "METFORMIN",
  "qualified_name": "METFORMIN 1000MG TAB",
  "med_type": "DRUG",
  "product_form_name": "TABLET",
  "med_status": "ACTIVE",
  "med_status_name": "ACTIVE",
  "va_status": "ACTIVE",
  "va_type": "OUTPATIENT",
  "sig": "Take 1 tablet by mouth twice daily",
  "patient_instruction": "Take with food",
  "facility_code": "500",
  "facility_name": "Washington DC VAMC",
  "start_date": "2023-01-15T00:00:00Z",
  "dosages": [
    {
      "dose": "1000MG",
      "schedule_name": "TWICE DAILY",
      "route_name": "ORAL",
      "units": "MG"
    }
  ]
}
```

### Lab Result Example

```json
{
  "uid": "lab-789",
  "local_id": "11111",
  "type_code": "33747-0",
  "type_name": "HEMOGLOBIN A1C",
  "display_name": "Hemoglobin A1c",
  "result": "7.2",
  "units": "%",
  "high": "6.0",
  "low": "4.0",
  "interpretation_code": "H",
  "interpretation_name": "HIGH",
  "observed": "2025-01-07T08:00:00Z",
  "resulted": "2025-01-07T10:30:00Z",
  "facility_code": "500",
  "facility_name": "Washington DC VAMC",
  "status_code": "F",
  "status_name": "FINAL"
}
```

## Field Validation and Processing

### Common Validation Patterns

1. **String Fields**: Automatically trimmed and converted to strings
2. **Date Fields**: Parsed from VistA format and serialized as ISO 8601
3. **Enum Fields**: Validated against predefined values
4. **Optional Fields**: Use `None` as default, excluded from serialization
5. **Alias Fields**: Support both field names and VistA aliases

### Data Masking

Sensitive fields are automatically masked in logs:

- SSNs: `123-45-6789` → `[REDACTED-SSN]`
- DFNs: `AB123456` → `[REDACTED-DFN]`
- Patient names in error messages
- IP addresses and other identifiers

### Error Handling

All models include comprehensive error handling:

- Validation errors with detailed messages
- Type conversion with fallbacks
- Required field validation
- Custom validators for complex fields

## Best Practices

### Using Models in Code

```python
# Create a new patient demographics
demographics = PatientDemographics(
    ssn="123-45-6789",
    full_name="DOE,JOHN",
    family_name="DOE",
    given_names="JOHN",
    date_of_birth=date(1980, 1, 1),
    gender_code="M",
    gender_name="MALE"
)

# Access computed properties
if demographics.veteran and demographics.veteran.service_connected:
    print(f"Service connected: {demographics.veteran.service_connection_percent}%")

# Serialize to JSON
json_data = demographics.model_dump()
```

### Working with Collections

```python
# Create a patient data collection
collection = PatientDataCollection(
    demographics=demographics,
    source_station="500",
    source_icn="1000220000V123456"
)

# Add vital signs
vital = VitalSign(
    uid="vital-1",
    local_id="123",
    type_name="BLOOD PRESSURE",
    result="120/80",
    observed=datetime.now(),
    resulted=datetime.now(),
    facility_code="500",
    facility_name="Test VAMC"
)

collection.vital_signs_dict[vital.uid] = vital

# Access as list
vitals_list = collection.vital_signs
```

This comprehensive data model reference provides all the information needed to understand and work with the Vista API MCP Server's data structures.
