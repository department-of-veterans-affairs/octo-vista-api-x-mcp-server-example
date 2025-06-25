"""Utility functions for Vista API MCP Server"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# Default configurations
DEFAULT_STATIONS = {
    "500": {
        "name": "Washington DC VAMC",
        "duz": "10000000219",
        "timezone": "America/New_York",
    },
    "508": {
        "name": "Atlanta VAMC", 
        "duz": "10000000220",
        "timezone": "America/New_York",
    },
    "640": {
        "name": "Palo Alto VAMC",
        "duz": "10000000221", 
        "timezone": "America/Los_Angeles",
    },
}


def get_default_station() -> str:
    """Get default station from environment or use 500"""
    return os.getenv("DEFAULT_STATION", "500")


def get_default_duz() -> str:
    """Get default DUZ from environment or use station default"""
    station = get_default_station()
    station_info = DEFAULT_STATIONS.get(station, DEFAULT_STATIONS["500"])
    return os.getenv("DEFAULT_DUZ", station_info["duz"])


def get_station_info(station: str) -> Dict[str, str]:
    """Get station information"""
    return DEFAULT_STATIONS.get(station, {
        "name": f"Station {station}",
        "duz": get_default_duz(),
        "timezone": "America/New_York",
    })


def translate_vista_error(error: Union[Exception, Dict[str, Any]]) -> str:
    """
    Translate Vista API errors to user-friendly messages
    
    Args:
        error: Exception or error dictionary
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, dict):
        error_type = error.get("errorType", "Unknown")
        error_code = error.get("errorCode", "")
        message = error.get("message", "An error occurred")
        
        # Common error translations
        if error_type == "SecurityFault":
            if "permission" in message.lower():
                return "You don't have permission to perform this operation. Please check your access rights."
            elif "station" in message.lower():
                return f"Access denied to the requested station. Please verify station access."
            else:
                return "Security error: Access denied."
                
        elif error_type == "VistaLinkFault":
            if "connect" in message.lower():
                return "Cannot connect to VistA system. The station may be offline or unreachable."
            elif "timeout" in message.lower():
                return "Connection to VistA timed out. Please try again."
            else:
                return f"VistA connection error: {message}"
                
        elif error_type == "RpcFault":
            if "not found" in message.lower():
                return "The requested operation is not available."
            elif "parameter" in message.lower():
                return "Invalid parameters provided for the operation."
            else:
                return f"Operation failed: {message}"
                
        elif error_type == "JwtException":
            return "Authentication error. Please check your credentials."
            
        else:
            return f"{error_type}: {message}"
            
    else:
        # Handle exception objects
        return str(error)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp for responses"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def mask_ssn(ssn: str) -> str:
    """Mask SSN for privacy"""
    if not ssn or len(ssn) < 4:
        return "***-**-****"
    return f"***-**-{ssn[-4:]}"


def validate_station(station: str) -> bool:
    """Validate station number format"""
    if not station:
        return False
    # Station should be 3 digits, optionally followed by division suffix
    return len(station) >= 3 and station[:3].isdigit()


def validate_duz(duz: str) -> bool:
    """Validate DUZ format"""
    if not duz:
        return False
    # DUZ should be numeric
    return duz.isdigit()


def validate_dfn(dfn: str) -> bool:
    """Validate DFN format"""
    if not dfn:
        return False
    # DFN should be numeric
    return dfn.isdigit()


def format_phone(phone: str) -> str:
    """Format phone number for display"""
    if not phone:
        return ""
    
    # Remove non-digits
    digits = "".join(c for c in phone if c.isdigit())
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    else:
        return phone


def parse_boolean(value: Any) -> bool:
    """Parse various boolean representations"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.upper() in ["TRUE", "YES", "Y", "1", "ON"]
    return bool(value)


def build_metadata(
    station: Optional[str] = None,
    rpc_name: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Build standard metadata for responses"""
    metadata = {
        "timestamp": format_timestamp(),
        "source": "VistA RPC",
    }
    
    if station:
        metadata["station"] = station
        station_info = get_station_info(station)
        if station_info:
            metadata["station_name"] = station_info.get("name", f"Station {station}")
            
    if rpc_name:
        metadata["rpc"] = rpc_name
        
    if duration_ms is not None:
        metadata["duration_ms"] = duration_ms
        
    return metadata


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "patient.address.city")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
            
    return value


def create_rpc_parameter(value: Union[str, List[str], Dict[str, str]]) -> Dict[str, Any]:
    """
    Create RPC parameter in correct format
    
    Args:
        value: Parameter value (string, list, or dict)
        
    Returns:
        Formatted parameter dictionary
    """
    if isinstance(value, str):
        return {"string": value}
    elif isinstance(value, list):
        return {"array": value}
    elif isinstance(value, dict):
        return {"namedArray": value}
    else:
        return {"string": str(value)}


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return os.getenv("VISTA_MCP_DEBUG", "").lower() in ["true", "1", "yes"]


def log_rpc_call(
    rpc_name: str,
    station: str,
    duz: str,
    parameters: Optional[List[Dict[str, Any]]] = None,
    duration_ms: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
):
    """Log RPC call for audit trail"""
    log_data = {
        "rpc": rpc_name,
        "station": station,
        "duz": duz,
        "timestamp": format_timestamp(),
        "success": success,
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
        
    if error:
        log_data["error"] = error
        
    if is_debug_mode() and parameters:
        log_data["parameters"] = parameters
        
    if success:
        logger.info(f"RPC call completed: {rpc_name}", extra=log_data)
    else:
        logger.error(f"RPC call failed: {rpc_name}", extra=log_data)