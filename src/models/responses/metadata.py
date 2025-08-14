"""Response metadata models for MCP tools"""

import uuid
from datetime import UTC, datetime

from pydantic import (
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)

from ..base.common import BaseModelExcludeNone
from ..utils import format_datetime_for_mcp_response


class PaginationMetadata(BaseModelExcludeNone):
    """Enhanced pagination metadata with LLM guidance"""

    total_available_items: int
    returned: int
    offset: int
    limit: int
    has_more: bool = False
    next_offset: int | None = None
    suggested_next_call: str | None = None
    # Extra fields for computation
    tool_name: str | None = Field(None, exclude=True)
    patient_dfn: str | None = Field(None, exclude=True)

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


class RpcCallMetadata(BaseModelExcludeNone):
    """Metadata about an RPC call"""

    rpc: str
    context: str
    json_result: bool = Field(default=True, serialization_alias="jsonResult")
    parameters: list[dict[str, dict[str, str]]]
    duz: str | None


class StationMetadata(BaseModelExcludeNone):
    """Station information"""

    station_number: str
    station_name: str | None = None
    division: str | None = None


class DemographicsMetadata(BaseModelExcludeNone):
    """Patient demographics information"""

    patient_dfn: str | None = None
    patient_name: str | None = None
    patient_age: int | None = None


class PerformanceMetrics(BaseModelExcludeNone):
    """Performance metrics for the request"""

    duration_ms: int
    start_time: datetime
    end_time: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_serializer("start_time", "end_time")
    def serialize_datetime_fields(self, value: datetime) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds with millisecond precision"""
        return self.duration_ms / 1000


class ResponseMetadata(BaseModelExcludeNone):
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
    pagination: PaginationMetadata | None = None

    # Performance
    performance: PerformanceMetrics

    # Source system
    source_system: str = "VistA"
    station: StationMetadata

    # RPC call details (if applicable)
    rpc: RpcCallMetadata | None = None

    # Patient demographics (if applicable)
    demographics: DemographicsMetadata | None = None

    # Additional context
    additional_info: dict[str, object] = Field(default_factory=dict)

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Request ID must be a non-empty string")
        return v


# Helper function to create metadata


def create_response_metadata(
    *,
    request_id: str | None = None,
    station: str,
    start_time: datetime,
    rpc_details: RpcCallMetadata | None = None,
    **additional_info: object,
) -> ResponseMetadata:
    """Helper to create standardized response metadata"""
    request_id = request_id or f"req_{uuid.uuid4().hex}"
    end_time = datetime.now(UTC)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    return ResponseMetadata(
        request_id=request_id,
        performance=PerformanceMetrics(
            duration_ms=duration_ms, start_time=start_time, end_time=end_time
        ),
        station=StationMetadata(station_number=station),
        rpc=rpc_details,
        additional_info=additional_info,
    )
