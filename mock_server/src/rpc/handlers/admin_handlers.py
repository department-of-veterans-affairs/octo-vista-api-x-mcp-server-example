"""
Administrative RPC handlers for appointments and user management
"""

from typing import Any

from src.data.appointments import get_appointments_for_clinic
from src.rpc.models import Parameter


class AdminHandlers:
    """Handlers for administrative RPCs"""

    @staticmethod
    def handle_sdes_get_appts_by_clin_ien_2(
        parameters: list[Parameter],
    ) -> dict[str, Any]:
        """
        Handle SDES GET APPTS BY CLIN IEN 2 - Get appointments by clinic
        Returns JSON object with appointment data
        """
        # Get parameters
        clinic_ien = ""
        start_date = ""
        end_date = ""

        if parameters:
            if len(parameters) > 0:
                param_value = parameters[0].get_value()
                if isinstance(param_value, str):
                    clinic_ien = param_value

            if len(parameters) > 1:
                param_value = parameters[1].get_value()
                if isinstance(param_value, str):
                    start_date = param_value

            if len(parameters) > 2:
                param_value = parameters[2].get_value()
                if isinstance(param_value, str):
                    end_date = param_value

        # Get appointments from test data
        appointments = get_appointments_for_clinic(clinic_ien, start_date, end_date)

        # The parser expects lowercase "appointments" key
        return {"appointments": appointments}

    @staticmethod
    def handle_sdes_get_user_profile_by_duz(
        parameters: list[Parameter],
    ) -> dict[str, Any]:
        """
        Handle SDES GET USER PROFILE BY DUZ - Get user profile details
        Returns JSON object with user profile
        """
        # Get DUZ from first parameter
        duz = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                duz = param_value

        # Mock user profiles
        profiles = {
            "10000000219": {
                "duz": "10000000219",
                "name": "PROVIDER,TEST",
                "title": "PHYSICIAN",
                "service": "MEDICINE",
                "phone": "202-555-1234",
                "pager": "202-555-5678",
                "email": "test.provider@va.gov",
                "digitalSignature": True,
                "securityKeys": ["ORES", "PROVIDER", "XUPROG"],
                "menuOptions": ["OR CPRS GUI CHART", "SDESRPC"],
                "defaultLocation": {"ien": "195", "name": "PRIMARY CARE"},
            },
            "10000000220": {
                "duz": "10000000220",
                "name": "WILLIAMS,PATRICIA L",
                "title": "PSYCHIATRIST",
                "service": "MENTAL HEALTH",
                "phone": "202-555-2345",
                "pager": "202-555-6789",
                "email": "patricia.williams@va.gov",
                "digitalSignature": True,
                "securityKeys": ["ORES", "PROVIDER", "XUPROG", "GMR MANAGER"],
                "menuOptions": ["OR CPRS GUI CHART", "SDESRPC"],
                "defaultLocation": {"ien": "196", "name": "MENTAL HEALTH"},
            },
        }

        # Return profile or error
        profile = profiles.get(duz)
        if profile:
            return profile
        else:
            return {"error": "User not found", "errorCode": "USER_NOT_FOUND"}

    @staticmethod
    def handle_orwtpd1_listall(parameters: list[Parameter]) -> str:
        """
        Handle ORWTPD1 LISTALL - List all team members
        Returns delimited string format
        """
        # Mock team members data
        # Format: IEN^NAME^ROLE^PHONE^PAGER
        team_members = [
            "10000000219^PROVIDER,TEST^ATTENDING PHYSICIAN^202-555-1234^202-555-5678",
            "10000000220^WILLIAMS,PATRICIA L^PSYCHIATRIST^202-555-2345^202-555-6789",
            "10000000221^SMITH,JENNIFER A^PRIMARY CARE PHYSICIAN^202-555-3456^202-555-7890",
            "10000000222^NURSE,JANE M^RN CARE COORDINATOR^202-555-4567^202-555-8901",
            "10000000223^THERAPIST,JOHN D^PHYSICAL THERAPIST^202-555-5678^202-555-9012",
        ]

        return "\n".join(team_members)
