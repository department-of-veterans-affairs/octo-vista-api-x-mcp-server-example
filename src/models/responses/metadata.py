"""Response metadata models for MCP tools"""

from datetime import UTC, date, datetime

from pydantic import (
    Field,
    SerializeAsAny,
    computed_field,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)

from ...utils import get_logger
from ..base import BaseVistaModel
from ..utils import format_datetime_for_mcp_response

logger = get_logger()


# Filter Metadata Models
class FiltersMetadata(BaseVistaModel):
    """Base class for tool-specific filter metadata"""

    days_back: int | None = Field(
        default=None, description="Number of days to look back for data"
    )

    @model_serializer(mode="wrap")
    def _serialize(self, serializer):
        """Don't return unset filters to keep json smaller"""
        data = serializer(self)
        return {k: v for k, v in data.items() if v is not False and v is not None}


class AllergiesFiltersMetadata(FiltersMetadata):
    """Filter metadata for allergies tool"""

    verified_only: bool = Field(
        default=False, description="Show only verified allergies"
    )
    omit_historical: bool = Field(default=True, description="Omit historical allergies")


class VitalsFiltersMetadata(FiltersMetadata):
    """Filter metadata for vitals tool"""

    vital_type: str | None = Field(
        default=None, description="Filter by specific vital sign type"
    )


class LabsFiltersMetadata(FiltersMetadata):
    """Filter metadata for labs tool"""

    abnormal_only: bool = Field(
        default=False, description="Show only abnormal lab results"
    )
    lab_type: str | None = Field(
        default=None, description="Filter by specific lab test type"
    )


class ConsultsFiltersMetadata(FiltersMetadata):
    """Filter metadata for consults tool"""

    active_only: bool = Field(default=True, description="Show only active consults")


class MedicationsFiltersMetadata(FiltersMetadata):
    """Filter metadata for medications tool"""

    active_only: bool = Field(default=True, description="Show only active medications")
    therapeutic_class: str | None = Field(
        default=None, description="Filter by therapeutic class"
    )


class OrdersFiltersMetadata(FiltersMetadata):
    """Filter metadata for orders tool"""

    active_only: bool = Field(default=True, description="Show only active orders")


class DocumentsFiltersMetadata(FiltersMetadata):
    """Filter metadata for documents tool"""

    completed_only: bool = Field(
        default=True, description="Show only completed documents"
    )
    document_type: str | None = Field(
        default=None, description="Filter by document type"
    )


class DiagnosesFiltersMetadata(FiltersMetadata):
    """Filter metadata for diagnoses tool"""

    body_system: str | None = Field(default=None, description="Filter by body system")
    diagnosis_type: str | None = Field(
        default=None, description="Filter by diagnosis type"
    )
    status_filter: str | None = Field(
        default=None, description="Filter by diagnosis status"
    )
    icd_version: str | None = Field(default=None, description="Filter by ICD version")


class HealthFactorsFiltersMetadata(FiltersMetadata):
    """Filter metadata for health factors tool"""

    category_filter: str | None = Field(
        default=None, description="Filter by health factor category"
    )
    risk_category: str | None = Field(
        default=None, description="Filter by risk category"
    )
    severity_filter: str | None = Field(
        default=None, description="Filter by severity level"
    )


class VisitsFiltersMetadata(FiltersMetadata):
    """Filter metadata for visits tool"""

    visit_type: str | None = Field(default=None, description="Filter by visit type")
    active_only: bool = Field(default=False, description="Show only active visits")


class ProceduresFiltersMetadata(FiltersMetadata):
    """Filter metadata for procedures tool"""

    date_from: date | None = Field(
        default=None, description="Start date for procedure filtering"
    )
    date_to: date | None = Field(
        default=None, description="End date for procedure filtering"
    )


class POVsFiltersMetadata(FiltersMetadata):
    """Filter metadata for POVs (Purpose of Visit) tool"""

    primary_only: bool = Field(
        default=False, description="Filter to show only primary POVs"
    )


class ProblemsFiltersMetadata(FiltersMetadata):
    """Filter metadata for Problems tool"""

    active_only: bool = Field(
        default=False, description="Filter to show only active problems"
    )
    service_connected_only: bool = Field(
        default=False, description="Filter to show only service connected problems"
    )


class PaginationMetadata(BaseVistaModel):
    """Enhanced pagination metadata with LLM guidance"""

    total_available_items: int = Field(description="Total number of items available")
    returned: int = Field(description="Number of items returned in this response")
    offset: int = Field(description="Starting offset for this page")
    limit: int = Field(description="Maximum number of items per page")
    has_more: bool = Field(
        default=False, description="Whether more items are available"
    )
    next_offset: int | None = Field(
        default=None, description="Offset for the next page"
    )
    suggested_next_call: str | None = Field(
        default=None, description="Suggested next API call"
    )
    # Extra fields for computation
    tool_name: str | None = Field(
        default=None, exclude=True, description="Tool name for suggestions"
    )
    patient_dfn: str | None = Field(
        default=None, exclude=True, description="Patient DFN for suggestions"
    )

    @model_validator(mode="after")
    def compute_fields(self):
        """Compute derived fields after initialization"""
        # Compute has_more
        self.has_more = (
            self.returned == self.limit
            and (self.offset + self.limit) < self.total_available_items
        )

        # Compute next_offset
        self.next_offset = self.offset + self.limit if self.has_more else None

        # Build suggested next call if we have the required info
        if self.has_more and self.tool_name and self.patient_dfn:
            params = [f'patient_dfn="{self.patient_dfn}"']
            params.append(f"limit={self.limit}")
            if self.next_offset is not None:
                params.append(f"offset={self.next_offset}")
            self.suggested_next_call = f"{self.tool_name}({', '.join(params)})"

        return self


class RpcCallMetadata(BaseVistaModel):
    """Metadata about an RPC call"""

    rpc: str = Field(description="RPC procedure name")
    context: str = Field(description="RPC context")
    json_result: bool = Field(
        default=True,
        serialization_alias="jsonResult",
        description="Whether result is JSON",
    )
    parameters: list[dict[str, dict[str, str]]] = Field(description="RPC parameters")
    duz: str | None = Field(default=None, description="User DUZ identifier")


class StationMetadata(BaseVistaModel):
    """Station information"""

    station_number: str = Field(description="Station number identifier")
    station_name: str | None = Field(default=None, description="Station name")
    division: str | None = Field(default=None, description="Division identifier")


class DemographicsMetadata(BaseVistaModel):
    """Patient demographics information"""

    patient_dfn: str | None = Field(default=None, description="Patient DFN identifier")
    patient_name: str | None = Field(default=None, description="Patient full name")
    patient_age: int | None = Field(default=None, description="Patient age in years")


class PerformanceMetrics(BaseVistaModel):
    """Performance metrics for the request"""

    duration_ms: int = Field(description="Request duration in milliseconds")
    start_time: datetime = Field(description="Request start time")
    end_time: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Request end time"
    )

    @field_serializer("start_time", "end_time")
    def serialize_datetime_fields(self, value: datetime) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds with millisecond precision"""
        return self.duration_ms / 1000


class ResponseMetadata(BaseVistaModel):
    """Standard metadata for API responses"""

    # Core metadata
    request_id: str = Field(
        default_factory=lambda: f"req_{datetime.now(UTC).timestamp()}",
        description="Unique request identifier",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str = "1.0"

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str | None:
        """Serialize timestamp field to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    # Pagination
    pagination: PaginationMetadata | None = Field(
        default=None, description="Pagination information"
    )

    # Performance
    performance: PerformanceMetrics = Field(description="Performance metrics")

    # Source system
    source_system: str = Field(default="VistA", description="Source system identifier")
    station: StationMetadata = Field(description="Station information")

    # RPC call details (if applicable)
    rpc: RpcCallMetadata | None = Field(default=None, description="RPC call metadata")

    # Patient demographics (if applicable)
    demographics: DemographicsMetadata | None = Field(
        default=None, description="Patient demographics"
    )

    # Filters applied (strongly typed)
    # Important: use a Union of all concrete FiltersMetadata subclasses so Pydantic
    # preserves the specific subtype and does not coerce it to the base class,
    # which would drop subtype fields during validation/serialization.
    filters: SerializeAsAny[FiltersMetadata] | None = Field(
        default=None, description="Applied filters"
    )

    # Additional context
    additional_info: dict[str, object] | None = Field(
        default=None, description="Additional context information"
    )

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Request ID must be a non-empty string")
        return v
