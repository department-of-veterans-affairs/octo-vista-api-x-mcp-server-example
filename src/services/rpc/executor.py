"""RPC execution service with standardized error handling and logging."""

import json
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ...utils import build_metadata, log_rpc_call, translate_vista_error
from ...vista.base import BaseVistaClient, VistaAPIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def execute_rpc(
    vista_client: BaseVistaClient,
    rpc_name: str,
    parameters: list[dict[str, Any]],
    parser: Callable[[Any], T],
    station: str,
    caller_duz: str,
    error_response_builder: Callable[[str, dict[str, Any]], dict[str, Any]],
    context: str | None = None,
    json_result: bool = False,
) -> dict[str, Any]:
    """Execute an RPC call with standardized error handling and logging.

    Args:
        vista_client: The Vista API client instance
        rpc_name: Name of the RPC to invoke
        parameters: RPC parameters
        parser: Function to parse the RPC result
        station: Station ID
        caller_duz: Caller DUZ
        error_response_builder: Function to build error response
        context: Optional RPC context
        json_result: Whether to expect JSON result

    Returns:
        Parsed and formatted response
    """
    start_time = time.time()

    try:
        # Build RPC kwargs
        rpc_kwargs: dict[str, Any] = {
            "station": station,
            "caller_duz": caller_duz,
            "rpc_name": rpc_name,
            "parameters": parameters,
        }

        if context:
            rpc_kwargs["context"] = context
        if json_result:
            rpc_kwargs["json_result"] = json_result

        logger.debug(
            f"RPC Request - Name: {rpc_name}, Station: {station}, DUZ: {caller_duz}"
        )
        logger.debug(f"RPC kwargs: {json.dumps(rpc_kwargs, default=str, indent=2)}")

        result = await vista_client.invoke_rpc(**rpc_kwargs)

        try:
            result_json = json.dumps(result, default=str, indent=2)
            logger.debug(f"Raw RPC response (JSON): {result_json}")
        except (TypeError, ValueError) as e:
            logger.debug(f"Raw RPC response (string): {str(result)}")
            logger.debug(f"JSON serialization failed: {e}")

        # Parse result
        parsed_data = parser(result)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log successful call
        log_rpc_call(
            rpc_name=rpc_name,
            station=station,
            duz=caller_duz,
            duration_ms=duration_ms,
            success=True,
        )

        # Build RPC details for metadata
        rpc_details: dict[str, Any] = {
            "rpc": rpc_name,
            "context": context or "OR CPRS GUI CHART",
            "parameters": parameters,
        }
        if json_result:
            rpc_details["jsonResult"] = True

        # Build metadata with RPC details
        metadata = build_metadata(
            station=station,
            rpc_name=rpc_name,
            duration_ms=duration_ms,
        )
        metadata["rpc"] = rpc_details
        metadata["duz"] = caller_duz

        return {
            "parsed_data": parsed_data,
            "metadata": metadata,
            "duration_ms": duration_ms,
        }

    except VistaAPIError as e:
        logger.error(
            f"VISTA_API_ERROR: {json.dumps({
            'error_type': e.error_type,
            'error_code': e.error_code,
            'message': e.message,
            'status_code': e.status_code,
            'rpc_name': rpc_name,
            'station': station,
            'duz': caller_duz
        })}"
        )

        # Log failed call
        log_rpc_call(
            rpc_name=rpc_name,
            station=station,
            duz=caller_duz,
            success=False,
            error=str(e),
        )

        # Build RPC details for error metadata
        rpc_details = {
            "rpc": rpc_name,
            "context": context or "OR CPRS GUI CHART",
            "parameters": parameters,
        }
        if json_result:
            rpc_details["jsonResult"] = True

        error_metadata = build_metadata(station=station, rpc_name=rpc_name)
        error_metadata["rpc"] = rpc_details
        error_metadata["duz"] = caller_duz

        # Build error response
        return error_response_builder(
            translate_vista_error(e.to_dict()),
            error_metadata,
        )

    except Exception as e:
        logger.error(
            f"UNEXPECTED_ERROR: {json.dumps({
            'error': str(e),
            'error_type': type(e).__name__,
            'rpc_name': rpc_name,
            'station': station,
            'duz': caller_duz
        })}"
        )
        logger.exception(f"Unexpected error in {rpc_name}")

        # Build RPC details for error metadata
        rpc_details = {
            "rpc": rpc_name,
            "context": context or "OR CPRS GUI CHART",
            "parameters": parameters,
        }
        if json_result:
            rpc_details["jsonResult"] = True

        error_metadata = build_metadata(station=station, rpc_name=rpc_name)
        error_metadata["rpc"] = rpc_details
        error_metadata["duz"] = caller_duz

        # Build error response
        return error_response_builder(
            f"Unexpected error: {str(e)}",
            error_metadata,
        )
