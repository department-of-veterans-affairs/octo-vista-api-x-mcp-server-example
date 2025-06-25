"""Base abstract class for Vista API clients"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVistaClient(ABC):
    """Abstract base class for Vista API clients"""
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize the base Vista client
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    @abstractmethod
    async def invoke_rpc(
        self,
        station: str,
        caller_duz: str,
        rpc_name: str,
        context: str = "OR CPRS GUI CHART",
        parameters: Optional[List[Dict[str, Any]]] = None,
        json_result: bool = False,
        use_cache: bool = True,
    ) -> Any:
        """
        Invoke a Vista RPC
        
        Args:
            station: Vista station number
            caller_duz: DUZ of the calling user
            rpc_name: Name of the RPC to invoke
            context: RPC context (default: OR CPRS GUI CHART)
            parameters: RPC parameters
            json_result: Whether to request JSON response
            use_cache: Whether to use response cache
            
        Returns:
            RPC response (string or dict depending on RPC and json_result)
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Close any open connections"""
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class VistaAPIError(Exception):
    """Vista API error with structured information"""
    
    def __init__(
        self,
        error_type: str,
        error_code: str,
        message: str,
        status_code: int,
    ):
        self.error_type = error_type
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{error_type}: {message}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_type": self.error_type,
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
        }