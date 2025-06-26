"""
RPC invocation resource matching Vista API X
"""

import asyncio
import random
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from src.config import settings
from src.exceptions.handlers import (
    RpcFaultException,
    SecurityFaultException,
    VistaLinkFaultException,
    create_error_response,
)
from src.middleware.auth_filter import SecurityContext
from src.rpc.authorization import RpcAuthorization
from src.rpc.handlers.admin_handlers import AdminHandlers
from src.rpc.handlers.clinical_handlers import ClinicalHandlers
from src.rpc.handlers.ddr_handlers import DDRHandlers
from src.rpc.handlers.patient_handlers import PatientHandlers
from src.rpc.handlers.system_handlers import SystemHandlers
from src.rpc.models import RpcRequestX, RpcResponseX

# Create RPC router
rpc_router = APIRouter()

# RPC handler registry
RPC_HANDLERS = {
    # Patient operations
    "ORWPT LIST": PatientHandlers.handle_orwpt_list,
    "ORWPT ID INFO": PatientHandlers.handle_orwpt_id_info,
    "ORWPT SELECT": PatientHandlers.handle_orwpt_select,
    "VPR SELECT PATIENT": PatientHandlers.handle_orwpt_list,  # Use same handler as ORWPT LIST
    "VPR GET PATIENT DATA JSON": PatientHandlers.handle_vpr_get_patient_data_json,
    "VPR GET PATIENT DATA": PatientHandlers.handle_vpr_get_patient_data_json,  # Add non-JSON variant
    "ORWPT16 ID INFO": PatientHandlers.handle_orwpt_id_info,  # Alias for ID INFO
    # Clinical operations
    "ORWPS ACTIVE": ClinicalHandlers.handle_orwps_active,
    "ORWLRR INTERIM": ClinicalHandlers.handle_orwlrr_interim,
    "ORQQVI VITALS": ClinicalHandlers.handle_orqqvi_vitals,
    "GMV V/M VITALS": ClinicalHandlers.handle_orqqvi_vitals,  # Alias for vitals
    "ORQQPL PROBLEM LIST": ClinicalHandlers.handle_orqqpl_problem_list,
    "ORQQPL LIST": ClinicalHandlers.handle_orqqpl_problem_list,  # Alias without PROBLEM
    "ORQQAL LIST": ClinicalHandlers.handle_orqqal_list,
    # System operations
    "XWB IM HERE": SystemHandlers.handle_xwb_im_here,
    "ORWU DT": SystemHandlers.handle_orwu_dt,
    "XUS INTRO MSG": SystemHandlers.handle_xus_intro_msg,
    "ORWU USERINFO": SystemHandlers.handle_orwu_userinfo,
    "ORWU VERSRV": SystemHandlers.handle_orwu_versrv,
    "XUS GET USER INFO": SystemHandlers.handle_xus_get_user_info,
    # Administrative operations
    "SDES GET APPTS BY CLIN IEN 2": AdminHandlers.handle_sdes_get_appts_by_clin_ien_2,
    "SDES GET USER PROFILE BY DUZ": AdminHandlers.handle_sdes_get_user_profile_by_duz,
    "ORWTPD1 LISTALL": AdminHandlers.handle_orwtpd1_listall,
    # DDR operations (requires ALLOW_DDR flag)
    "DDR LISTER": DDRHandlers.handle_ddr_lister,
    "DDR FIND": DDRHandlers.handle_ddr_find,
    "DDR GETS": DDRHandlers.handle_ddr_gets,
}


@rpc_router.post("/{stationNo}/users/{duz}/rpc/invoke", response_model=RpcResponseX)
async def invoke_rpc(stationNo: str, duz: str, request: Request, rpc_request: RpcRequestX) -> RpcResponseX:
    """
    Execute VistA RPC.
    Matches Vista API X /vista-sites/{stationNo}/users/{duz}/rpc/invoke endpoint.
    """
    # Create security context
    security_context = SecurityContext(request)

    # Create authorization checker
    auth = RpcAuthorization(security_context)

    try:
        # Step 1: Check station/DUZ authorization
        auth.assert_allow_connection(stationNo, duz)

        # Step 2: Check RPC execution permission
        auth.assert_allow_execution(rpc_request.context, rpc_request.rpc)

        # Step 3: Simulate VistaLink connection with retries
        retry_count = 0
        max_retries = settings.vistalink_retry_attempts

        while retry_count < max_retries:
            try:
                # Add configurable delay
                if settings.enable_response_delay:
                    delay_ms = random.randint(settings.min_response_delay_ms, settings.max_response_delay_ms)
                    await asyncio.sleep(delay_ms / 1000)

                # Simulate error injection
                if settings.error_injection_rate > 0:
                    if random.random() < settings.error_injection_rate:
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            await asyncio.sleep(settings.vistalink_retry_delay_ms / 1000)
                            continue
                        else:
                            raise VistaLinkFaultException(
                                message="Simulated VistaLink connection failure",
                                fault_code="CONNECTION_TIMEOUT",
                                fault_string="Connection timeout after 3 retry attempts",
                            )

                # Execute RPC
                result = await execute_rpc(rpc_request)

                # Format response
                response = RpcResponseX(path=str(request.url.path), payload=result)

                return response

            except (VistaLinkFaultException, RpcFaultException):
                raise
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise VistaLinkFaultException(
                        message=f"RPC execution failed after {max_retries} attempts",
                        fault_code="RPC_EXECUTION_FAILED",
                        fault_string=str(e),
                    )
                await asyncio.sleep(settings.vistalink_retry_delay_ms / 1000)

    except SecurityFaultException:
        raise
    except VistaLinkFaultException:
        raise
    except RpcFaultException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code="INTERNAL-ERROR",
                title="Internal Server Error",
                message=str(e),
                path=str(request.url.path),
                status_code=500,
            ),
        )


async def execute_rpc(rpc_request: RpcRequestX) -> Any:
    """Execute the actual RPC"""

    # Check if handler exists
    handler = RPC_HANDLERS.get(rpc_request.rpc)

    if not handler:
        # Return generic response for unimplemented RPCs
        return f"Mock response for {rpc_request.rpc} in context {rpc_request.context}"

    try:
        # Execute handler
        result = handler(rpc_request.parameters or [])

        # Format response based on jsonResult flag
        if rpc_request.jsonResult:
            # For JSON results, return the object directly
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                # Try to parse as JSON
                try:
                    import json

                    return json.loads(result)
                except (ValueError, TypeError):
                    # If parsing fails, return as string
                    return result
            else:
                return result
        else:
            # For non-JSON results, return string directly
            if isinstance(result, str):
                return result
            else:
                import json

                return json.dumps(result)

    except Exception as e:
        raise RpcFaultException(
            message=f"RPC execution error: {e!s}",
            rpc_name=rpc_request.rpc,
            fault_code="RPC_ERROR",
        )


# Add more RPC implementations as needed
def add_system_rpc_handlers():
    """Add system RPC handlers"""

    def handle_xwb_im_here(parameters):
        """Heartbeat/keepalive"""
        return "1"

    def handle_xus_intro_msg(parameters):
        """System intro message"""
        return "Vista API X Mock Server\nVersion 2.1\nTest Environment"

    def handle_orwu_dt(parameters):
        """Get server date/time in FileMan format"""
        # FileMan date: YYYMMDD.HHMMSS where YYY = year - 1700
        import datetime

        now = datetime.datetime.now()
        year_offset = now.year - 1700
        fm_date = f"{year_offset:03d}{now.month:02d}{now.day:02d}.{now.hour:02d}{now.minute:02d}{now.second:02d}"
        return fm_date

    def handle_orwu_userinfo(parameters):
        """Get user information"""
        # Return mock user info
        duz = "10000000219"
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                duz = param_value

        return f"{duz}^PROVIDER,TEST^TEST PROVIDER^MD^1^500^PRIMARY CARE"

    # Register handlers
    RPC_HANDLERS["XWB IM HERE"] = handle_xwb_im_here
    RPC_HANDLERS["XUS INTRO MSG"] = handle_xus_intro_msg
    RPC_HANDLERS["ORWU DT"] = handle_orwu_dt
    RPC_HANDLERS["ORWU USERINFO"] = handle_orwu_userinfo


# Initialize system RPC handlers
add_system_rpc_handlers()
