"""Get items by UID/URN tool for MCP server"""

from datetime import UTC, datetime
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field, SerializeAsAny

from ...models.patient import BasePatientModel, PatientDataCollection
from ...models.responses.metadata import (
    DemographicsMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import ResponseData, ToolResponse
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


class ItemsByUidResponseData(ResponseData):
    """Payload for get_items_by_uid"""

    items: dict[str, SerializeAsAny[BasePatientModel]]
    requested_count: int
    found_count: int


class GetItemsByUidResponse(ToolResponse[ItemsByUidResponseData]):
    """Generic response returning a mapping of uid -> item"""

    pass


def register_get_items_by_uid_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_items_by_uid tool with the MCP server"""

    @mcp.tool()
    async def get_items_by_uid(
        patient_icn: str,
        uids: Annotated[
            list[str],
            Field(description="List of UIDs/URNs to fetch", max_length=100),
        ],
        station: str | None = None,
    ) -> GetItemsByUidResponse:
        """Return one or more patient items by UID/URN for the requested patient ICN. Maximum of 100 items at a time"""
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
                demographics=DemographicsMetadata(patient_icn=patient_icn),
            )
            return GetItemsByUidResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data: PatientDataCollection = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Build lookup from the aggregated dictionary
            all_items = patient_data.all_items

            result: dict[str, BasePatientModel] = {}
            for uid in uids:
                item = all_items.get(uid)
                if item is not None:
                    result[uid] = item

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
                    patient_gender=patient_data.demographics.gender_name,
                ),
            )

            data = ItemsByUidResponseData(
                items=result,
                requested_count=len(uids),
                found_count=len(result),
            )

            return GetItemsByUidResponse(
                success=True,
                data=data,
                metadata=md,
                total_item_count=len(result),
            )

        except Exception as e:
            logger.exception("Unexpected error in get_items_by_uid")
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
            return GetItemsByUidResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
