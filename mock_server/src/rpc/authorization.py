"""
RPC authorization matching Vista API X implementation
"""


from src.exceptions.handlers import SecurityFaultException
from src.middleware.auth_filter import SecurityContext


class RpcAuthorization:
    """Handle RPC authorization checks"""

    def __init__(self, security_context: SecurityContext):
        self.context = security_context

    def assert_allow_connection(self, station: str, duz: str):
        """
        Assert that connection is allowed to station/DUZ.
        Matches Vista API X assertAllowConnection.
        """
        if not self.context.is_authenticated:
            raise SecurityFaultException(message="Not authenticated", error_code="JWT-ACCESS-DENIED-0001")

        # Normalize station to 3-digit
        station_3digit = station[:3] if len(station) >= 3 else station

        if not self.context.has_vista_access(station_3digit, duz):
            raise SecurityFaultException(
                message=f"Connection not allowed to station={station}, duz={duz}",
                error_code="ACCESS-DENIED-79902",
                fault_code="STATION_DUZ_NOT_AUTHORIZED",
            )

    def assert_allow_execution(self, context: str, rpc: str):
        """
        Assert that RPC execution is allowed.
        Matches Vista API X assertAllowExecution.
        """
        if not self.context.is_authenticated:
            raise SecurityFaultException(message="Not authenticated", error_code="JWT-ACCESS-DENIED-0001")

        # Check if DDR RPC requires special flag
        if context == "DDR APPLICATION PROXY" or rpc.startswith("DDR"):
            if not self.context.has_flag("ALLOW_DDR"):
                raise SecurityFaultException(
                    message="DDR access not allowed. Missing ALLOW_DDR flag.",
                    error_code="ACCESS-DENIED-78292",
                    fault_code="DDR_NOT_ALLOWED",
                )

        # Check RPC permission
        if not self.context.has_authority(context, rpc):
            raise SecurityFaultException(
                message=f"RPC execution not allowed: {context}/{rpc}",
                error_code="ACCESS-DENIED-78292",
                fault_code="RPC_NOT_AUTHORIZED",
            )

    def check_permission(self, station: str, duz: str, context: str, rpc: str) -> bool:
        """
        Check if user has permission for station/DUZ/context/RPC.
        Returns True if allowed, False otherwise.
        """
        try:
            self.assert_allow_connection(station, duz)
            self.assert_allow_execution(context, rpc)
            return True
        except SecurityFaultException:
            return False

    def get_allowed_stations(self) -> list:
        """Get list of stations user has access to"""
        stations = []
        for vista_id in self.context.vista_ids:
            site_id = vista_id.get("siteId", "")
            if site_id and site_id != "*":
                # Normalize to 3-digit
                station_3digit = site_id[:3] if len(site_id) >= 3 else site_id
                if station_3digit not in stations:
                    stations.append(station_3digit)
        return stations

    def get_allowed_rpcs(self) -> list:
        """Get list of allowed RPCs"""
        rpcs = []
        for auth in self.context.authorities:
            context = auth.get("context", "")
            rpc = auth.get("rpc", "")

            if context and rpc:
                if rpc == "*":
                    rpcs.append(f"{context}/*")
                else:
                    rpcs.append(f"{context}/{rpc}")

        return rpcs

    def has_wildcard_access(self) -> bool:
        """Check if user has wildcard (*/*) access"""
        for auth in self.context.authorities:
            if auth.get("context") == "*" and auth.get("rpc") == "*":
                return True
        return False
