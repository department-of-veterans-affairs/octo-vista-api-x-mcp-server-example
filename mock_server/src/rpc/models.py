"""
RPC models matching Vista API X structure
"""

from typing import Any

from pydantic import BaseModel, Field, validator


class Parameter(BaseModel):
    """RPC parameter with multiple type support"""

    ref: str | None = Field(None, description="Reference parameter")
    string: str | None = Field(None, description="String parameter")
    array: list[str] | None = Field(None, description="Array parameter")
    namedArray: dict[str, str] | None = Field(None, description="Named array parameter")

    @validator("*", pre=True)
    def check_single_type(cls, v, values):
        """Ensure only one parameter type is set"""
        if v is not None:
            # Count how many fields are already set
            set_fields = sum(1 for val in values.values() if val is not None)
            if set_fields > 0:
                raise ValueError("Only one parameter type can be specified")
        return v

    def get_value(self) -> Any:
        """Get the parameter value regardless of type"""
        if self.string is not None:
            return self.string
        elif self.ref is not None:
            return self.ref
        elif self.array is not None:
            return self.array
        elif self.namedArray is not None:
            return self.namedArray
        return None

    def get_type(self) -> str:
        """Get the parameter type"""
        if self.string is not None:
            return "string"
        elif self.ref is not None:
            return "ref"
        elif self.array is not None:
            return "array"
        elif self.namedArray is not None:
            return "namedArray"
        return "unknown"


class RpcRequestX(BaseModel):
    """RPC request matching Vista API X structure"""

    rpc: str = Field(..., description="RPC name")
    context: str = Field(..., description="RPC context")
    version: float | None = Field(None, description="RPC version")
    timeout: int | None = Field(15000, ge=10000, le=60000, description="Timeout in milliseconds (10000-60000)")
    jsonResult: bool | None = Field(False, description="Return result as JSON")
    parameters: list[Parameter] | None = Field(default_factory=list, description="RPC parameters")


class RpcResponseX(BaseModel):
    """RPC response matching Vista API X structure"""

    path: str = Field(..., description="Request path")
    payload: dict[str, Any] | Any = Field(..., description="Response payload")


class RpcContext:
    """RPC context constants matching Vista API X"""

    OR_CPRS_GUI_CHART = "OR CPRS GUI CHART"
    VPR_APPLICATION_PROXY = "VPR APPLICATION PROXY"
    SDESRPC = "SDESRPC"
    SDECRPC = "SDECRPC"
    DDR_APPLICATION_PROXY = "DDR APPLICATION PROXY"
    XUS_SIGNON_SETUP = "XUS SIGNON SETUP"
    XOBV_VISTALINK_TESTER = "XOBV VISTALINK TESTER"
    GMV_RPC_CONTEXT = "GMV RPC CONTEXT"
    CDS_RPC_CONTEXT = "CDS RPC CONTEXT"
    LHS_RPC_CONTEXT = "LHS RPC CONTEXT"
    ORWLRR = "ORWLRR"


class CommonRpcs:
    """Common RPC names"""

    # Patient operations
    ORWPT_LIST = "ORWPT LIST"
    ORWPT_ID_INFO = "ORWPT ID INFO"
    ORWPT_SELECT = "ORWPT SELECT"
    VPR_GET_PATIENT_DATA_JSON = "VPR GET PATIENT DATA JSON"

    # Clinical operations
    ORWPS_ACTIVE = "ORWPS ACTIVE"
    ORWLRR_INTERIM = "ORWLRR INTERIM"
    ORQQVI_VITALS = "ORQQVI VITALS"
    ORQQPL_PROBLEM_LIST = "ORQQPL PROBLEM LIST"
    ORWDXA_DRUG = "ORWDXA DRUG"

    # Administrative
    SDES_GET_APPTS_BY_CLIN_IEN_2 = "SDES GET APPTS BY CLIN IEN 2"
    SDES_GET_USER_PROFILE_BY_DUZ = "SDES GET USER PROFILE BY DUZ"
    ORWU_USERINFO = "ORWU USERINFO"

    # System
    XWB_IM_HERE = "XWB IM HERE"
    XUS_INTRO_MSG = "XUS INTRO MSG"
    DDR_LISTER = "DDR LISTER"
    ORWU_DT = "ORWU DT"

    # Documents
    TIU_GET_DOCUMENTS_BY_PATIENT = "TIU GET DOCUMENTS BY PATIENT"

    # Teams
    ORWTPD1_LISTALL = "ORWTPD1 LISTALL"
