"""
System RPC handlers for heartbeat, date/time, and system info
"""

from datetime import datetime

from src.config import settings
from src.rpc.models import Parameter


class SystemHandlers:
    """Handlers for system-related RPCs"""

    @staticmethod
    def handle_xwb_im_here(parameters: list[Parameter]) -> str:
        """
        Handle XWB IM HERE - Heartbeat check
        Returns "1" for success
        """
        return "1"

    @staticmethod
    def handle_orwu_dt(parameters: list[Parameter]) -> str:
        """
        Handle ORWU DT - Get server date/time
        Returns FileMan date/time format
        """
        # Get format parameter (NOW, TODAY, etc.)
        format_param = "NOW"
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                format_param = param_value.upper()

        # Get current time
        now = datetime.now()

        # Convert to FileMan format (YYYMMDD.HHMMSS)
        # Year offset: FileMan year = actual year - 1700
        fm_year = now.year - 1700
        fm_date = f"{fm_year:03d}{now.month:02d}{now.day:02d}"

        if format_param == "TODAY":
            # Return just date part
            return fm_date
        else:
            # Return date.time
            fm_time = f"{now.hour:02d}{now.minute:02d}{now.second:02d}"
            return f"{fm_date}.{fm_time}"

    @staticmethod
    def handle_xus_intro_msg(parameters: list[Parameter]) -> str:
        """
        Handle XUS INTRO MSG - Get system intro message
        Returns system information text
        """
        return (
            "VISTA MOCK SYSTEM\n"
            f"Software Version: {settings.app_version}\n"
            "Site: WASHINGTON DC VAMC (500)\n"
            "\n"
            "This is a mock implementation for development and testing.\n"
            "DO NOT use for actual patient care."
        )

    @staticmethod
    def handle_orwu_userinfo(parameters: list[Parameter]) -> str:
        """
        Handle ORWU USERINFO - Get basic user info
        Returns delimited user information
        """
        # In a real system, this would get info from the context
        # For mock, return test provider info
        return "10000000219^PROVIDER,TEST^TEST PROVIDER^PHYSICIAN^MEDICINE^202-555-1234"

    @staticmethod
    def handle_orwu_versrv(parameters: list[Parameter]) -> str:
        """
        Handle ORWU VERSRV - Get server version
        Returns server version info
        """
        return f"OR*3.0*999^{settings.app_version}^VISTA MOCK SERVER"

    @staticmethod
    def handle_xus_get_user_info(parameters: list[Parameter]) -> str:
        """
        Handle XUS GET USER INFO - Get detailed user info
        Returns more detailed user information
        """
        # Format: DUZ^NAME^TITLE^SERVICE^PHONE^ROOM^VERIFYCODE_CHANGE_DATE
        return "10000000219^PROVIDER,TEST^PHYSICIAN^MEDICINE^202-555-1234^ROOM 123^3250101"
