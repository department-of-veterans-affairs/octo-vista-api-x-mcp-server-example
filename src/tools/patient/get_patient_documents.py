"""Get patient documents tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    DocumentsFiltersMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import DocumentsResponse, DocumentsResponseData
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger()


def register_get_patient_documents_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_documents tool with the MCP server"""

    @mcp.tool()
    async def get_patient_documents(
        patient_icn: str,
        station: str = "",
        completed_only: bool = True,
        days_back: Annotated[int, Field(default=365, ge=1)] = 365,
        document_type: str = "",
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> DocumentsResponse:
        """Get patient clinical documents and notes."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate ICN
        if not validate_icn(patient_icn):
            md = ResponseMetadata(
                request_id=f"req_{int(start_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=0,
                    start_time=start_time,
                    end_time=start_time,
                ),
                station=StationMetadata(station_number=station),
            )
            return DocumentsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter documents with combined conditions
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
            documents = [
                d
                for d in patient_data.documents
                if d.reference_date_time
                and d.reference_date_time >= cutoff_date
                and (not completed_only or d.is_completed)
                and (not document_type or d.document_type == document_type)
            ]

            # Apply pagination
            documents_page, total_documents_after_filtering = paginate_list(
                documents, offset, limit
            )

            # Build typed metadata inline
            end_time = datetime.now(UTC)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            rpc_details = RpcCallMetadata(
                rpc="VPR GET PATIENT DATA JSON",
                context="LHS RPC CONTEXT",
                parameters=build_icn_only_named_array_param(patient_icn),
                duz=caller_duz,
            )
            md = ResponseMetadata(
                request_id=f"req_{int(end_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=duration_ms,
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
                rpc=rpc_details,
                demographics=DemographicsMetadata(
                    patient_icn=patient_icn,
                    patient_name=patient_data.patient_name,
                    patient_age=patient_data.demographics.calculate_age(),
                ),
                filters=DocumentsFiltersMetadata(
                    document_type=document_type,
                    completed_only=completed_only,
                    days_back=days_back,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_documents_after_filtering,
                    returned=len(documents_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_documents",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = DocumentsResponseData(
                completed=[d.uid for d in documents_page if d.is_completed],
                documents=documents_page,
            )

            return DocumentsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(f"Error getting patient documents: {e}")
            end_time = datetime.now(UTC)
            md = ResponseMetadata(
                request_id=f"req_{int(end_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=int((end_time - start_time).total_seconds() * 1000),
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
            )
            return DocumentsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
