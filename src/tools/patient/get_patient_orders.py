"""Get patient orders tool"""

from datetime import UTC, datetime
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    OrdersFiltersMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import OrdersResponse, OrdersResponseData
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_orders_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_orders tool with the MCP server"""

    @mcp.tool()
    async def get_patient_orders(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> OrdersResponse:
        """Get patient orders including medications, labs, and procedures."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        logger.info(
            f" [DEBUG] get_patient_orders: patient_dfn={patient_dfn}, station={station}, active_only={active_only}"
        )
        # Validate DFN
        if not validate_dfn(patient_dfn):
            # Inline-construct typed metadata
            md = ResponseMetadata(
                request_id=f"req_{int(start_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=0,
                    start_time=start_time,
                    end_time=start_time,
                ),
                station=StationMetadata(station_number=station),
            )
            return OrdersResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter orders
            orders = patient_data.orders
            if active_only:
                orders = [o for o in orders if o.is_active]

            # Apply pagination
            orders_page, total_orders_after_filtering = paginate_list(
                orders, offset, limit
            )

            # Build typed metadata inline
            end_time = datetime.now(UTC)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            rpc_details = RpcCallMetadata(
                rpc="VPR GET PATIENT DATA JSON",
                context="LHS RPC CONTEXT",
                parameters=[{"namedArray": {"patientId": patient_dfn}}],
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
                    patient_dfn=patient_dfn,
                    patient_name=patient_data.patient_name,
                    patient_age=patient_data.demographics.calculate_age(),
                ),
                filters=OrdersFiltersMetadata(
                    active_only=active_only,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_orders_after_filtering,
                    returned=len(orders_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_orders",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = OrdersResponseData(
                active_count=sum(1 for o in orders_page if o.is_active),
                orders=orders_page,
            )

            return OrdersResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_orders")
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
            return OrdersResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
