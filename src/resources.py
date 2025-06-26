"""MCP Resources for Vista API"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from .models import VprDomain
from .utils import DEFAULT_STATIONS

logger = logging.getLogger(__name__)


def register_resources(mcp: FastMCP):
    """Register MCP resources with the server"""

    @mcp.resource("vista://stations")
    async def get_stations() -> str:
        """
        Get list of available Vista stations

        Returns:
            JSON list of stations with their information
        """
        stations = []
        for number, info in DEFAULT_STATIONS.items():
            stations.append(
                {
                    "number": number,
                    "name": info["name"],
                    "default_duz": info["duz"],
                    "timezone": info["timezone"],
                }
            )

        return json.dumps(
            {
                "stations": stations,
                "description": "Available Vista stations for connection",
            },
            indent=2,
        )

    @mcp.resource("vista://vpr-domains")
    async def get_vpr_domains() -> str:
        """
        Get list of available VPR data domains

        Returns:
            JSON list of VPR domains with descriptions
        """
        domains = []
        domain_descriptions = {
            VprDomain.PATIENT: "Patient demographics and identification",
            VprDomain.ALLERGY: "Allergies and adverse reactions",
            VprDomain.MED: "Medications (active and inactive)",
            VprDomain.LAB: "Laboratory results",
            VprDomain.VITAL: "Vital sign measurements",
            VprDomain.PROBLEM: "Problem list (diagnoses)",
            VprDomain.APPOINTMENT: "Scheduled appointments",
            VprDomain.DOCUMENT: "Clinical documents and notes",
            VprDomain.PROCEDURE: "Procedures performed",
            VprDomain.CONSULT: "Consultation requests and results",
            VprDomain.ORDER: "Clinical orders",
            VprDomain.VISIT: "Patient visits and encounters",
            VprDomain.SURGERY: "Surgical procedures",
            VprDomain.IMAGE: "Imaging studies",
            VprDomain.IMMUNIZATION: "Immunization records",
            VprDomain.EDUCATION: "Patient education records",
            VprDomain.EXAM: "Physical examination findings",
            VprDomain.FACTOR: "Health factors",
        }

        for domain in VprDomain:
            domains.append(
                {
                    "id": domain.value,
                    "name": domain.value.title(),
                    "description": domain_descriptions.get(domain, ""),
                }
            )

        return json.dumps(
            {
                "domains": domains,
                "description": "VPR (Virtual Patient Record) data domains for get_patient_data tool",
                "usage": "Use these domain IDs when calling get_patient_data to retrieve specific types of clinical data",
            },
            indent=2,
        )

    @mcp.resource("vista://test-patients")
    async def get_test_patients() -> str:
        """
        Get catalog of test patients available in the mock server

        Returns:
            JSON list of test patients with their characteristics
        """
        test_patients = [
            {
                "dfn": "100022",
                "name": "ANDERSON, JAMES ROBERT",
                "ssn_last_four": "6789",
                "age": 73,
                "description": "Vietnam veteran with PTSD, diabetes, hypertension",
                "key_conditions": ["PTSD", "Diabetes Type 2", "Hypertension"],
                "medications": 5,
                "allergies": ["Penicillin", "Sulfa"],
            },
            {
                "dfn": "100023",
                "name": "MARTINEZ, MARIA",
                "ssn_last_four": "5432",
                "age": 58,
                "description": "Gulf War veteran with fibromyalgia, depression",
                "key_conditions": ["Fibromyalgia", "Depression", "Chronic pain"],
                "medications": 7,
                "allergies": ["Codeine"],
            },
            {
                "dfn": "100024",
                "name": "THOMPSON, MICHAEL DAVID",
                "ssn_last_four": "4567",
                "age": 40,
                "description": "OEF/OIF veteran with TBI, amputee, chronic pain",
                "key_conditions": [
                    "TBI",
                    "Right leg amputation",
                    "PTSD",
                    "Chronic pain",
                ],
                "medications": 8,
                "allergies": ["Penicillin"],
            },
            {
                "dfn": "100025",
                "name": "WILLIAMS, ROBERT EARL",
                "ssn_last_four": "3456",
                "age": 95,
                "description": "Korean War veteran with dementia, heart failure",
                "key_conditions": ["Dementia", "CHF", "Atrial fibrillation"],
                "medications": 12,
                "allergies": ["Aspirin", "Statins"],
            },
            {
                "dfn": "100026",
                "name": "JOHNSON, DAVID",
                "ssn_last_four": "2345",
                "age": 52,
                "description": "Homeless veteran with substance abuse, mental health issues",
                "key_conditions": [
                    "Alcohol use disorder",
                    "Bipolar disorder",
                    "Hepatitis C",
                ],
                "medications": 4,
                "allergies": [],
            },
            {
                "dfn": "100027",
                "name": "DAVIS, JENNIFER",
                "ssn_last_four": "8901",
                "age": 35,
                "description": "Recent veteran with MST, anxiety, adjustment disorder",
                "key_conditions": ["MST", "Anxiety disorder", "Adjustment disorder"],
                "medications": 3,
                "allergies": ["NSAIDs"],
            },
            {
                "dfn": "100028",
                "name": "WILSON, GEORGE HENRY",
                "ssn_last_four": "0123",
                "age": 70,
                "description": "Rural veteran with COPD, limited healthcare access",
                "key_conditions": ["COPD", "Tobacco use disorder", "Hypertension"],
                "medications": 6,
                "allergies": ["Penicillin", "Bee stings"],
            },
            {
                "dfn": "100029",
                "name": "GARCIA, ANTONIO",
                "ssn_last_four": "9012",
                "age": 65,
                "description": "Veteran with end-stage renal disease on dialysis",
                "key_conditions": ["ESRD", "Diabetes", "Hypertension", "Anemia"],
                "medications": 10,
                "allergies": ["Contrast dye"],
            },
        ]

        return json.dumps(
            {
                "test_patients": test_patients,
                "description": "Test patients available in the Vista API mock server",
                "usage": "Use these DFNs and patient information for testing",
                "station": "500",
            },
            indent=2,
        )

    @mcp.resource("vista://rpc-catalog")
    async def get_rpc_catalog() -> str:
        """
        Get catalog of available RPCs and their purposes

        Returns:
            JSON catalog of RPCs organized by category
        """
        rpc_catalog = {
            "patient_operations": {
                "description": "Patient search and demographics",
                "rpcs": [
                    {
                        "name": "ORWPT LIST",
                        "tool": "search_patients",
                        "description": "Search for patients by name or SSN",
                        "parameters": ["search_prefix"],
                    },
                    {
                        "name": "ORWPT ID INFO",
                        "tool": "get_patient_demographics",
                        "description": "Get detailed patient demographics",
                        "parameters": ["patient_dfn"],
                    },
                    {
                        "name": "ORWPT SELECT",
                        "tool": "select_patient",
                        "description": "Set current patient context",
                        "parameters": ["patient_dfn"],
                    },
                    {
                        "name": "VPR GET PATIENT DATA JSON",
                        "tool": "get_patient_data",
                        "description": "Get comprehensive patient data",
                        "parameters": ["patient_dfn", "domains"],
                    },
                ],
            },
            "clinical_operations": {
                "description": "Clinical data retrieval",
                "rpcs": [
                    {
                        "name": "ORWPS ACTIVE",
                        "tool": "get_medications",
                        "description": "Get patient medications",
                        "parameters": ["patient_dfn"],
                    },
                    {
                        "name": "ORWLRR INTERIM",
                        "tool": "get_lab_results",
                        "description": "Get laboratory results",
                        "parameters": ["patient_dfn", "days_back"],
                    },
                    {
                        "name": "ORQQVI VITALS",
                        "tool": "get_vital_signs",
                        "description": "Get vital sign measurements",
                        "parameters": ["patient_dfn"],
                    },
                    {
                        "name": "ORQQPL PROBLEM LIST",
                        "tool": "get_problems",
                        "description": "Get problem list",
                        "parameters": ["patient_dfn"],
                    },
                    {
                        "name": "ORQQAL LIST",
                        "tool": "get_allergies",
                        "description": "Get allergies and reactions",
                        "parameters": ["patient_dfn"],
                    },
                ],
            },
            "administrative_operations": {
                "description": "Administrative functions",
                "rpcs": [
                    {
                        "name": "SDES GET APPTS BY CLIN IEN 2",
                        "tool": "get_appointments",
                        "description": "Get clinic appointments",
                        "parameters": ["clinic_ien"],
                    },
                    {
                        "name": "SDES GET USER PROFILE BY DUZ",
                        "tool": "get_user_profile",
                        "description": "Get user profile information",
                        "parameters": ["user_duz"],
                    },
                    {
                        "name": "ORWTPD1 LISTALL",
                        "tool": "list_team_members",
                        "description": "List care team members",
                        "parameters": [],
                    },
                ],
            },
            "system_operations": {
                "description": "System functions",
                "rpcs": [
                    {
                        "name": "XWB IM HERE",
                        "tool": "heartbeat",
                        "description": "Connection keep-alive",
                        "parameters": [],
                    },
                    {
                        "name": "ORWU DT",
                        "tool": "get_server_time",
                        "description": "Get server date/time",
                        "parameters": ["format"],
                    },
                    {
                        "name": "XUS INTRO MSG",
                        "tool": "get_intro_message",
                        "description": "Get system message",
                        "parameters": [],
                    },
                    {
                        "name": "ORWU USERINFO",
                        "tool": "get_user_info",
                        "description": "Get current user info",
                        "parameters": [],
                    },
                    {
                        "name": "ORWU VERSRV",
                        "tool": "get_server_version",
                        "description": "Get server version",
                        "parameters": [],
                    },
                ],
            },
        }

        return json.dumps(
            {
                "rpc_catalog": rpc_catalog,
                "description": "Complete catalog of available Vista RPCs and their corresponding MCP tools",
                "total_rpcs": sum(len(cat["rpcs"]) for cat in rpc_catalog.values()),
            },
            indent=2,
        )
