"""
Patient-related RPC handlers
"""

import copy
import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from src.data.test_patients import get_patient_by_dfn_or_icn, search_patients_by_name
from src.rpc.models import Parameter


def patient_id_from_dfn_or_icn_param_value(param_dict: dict[str, Any]) -> str | None:
    """
    Extract patient ID from parameters, handling both DFN and ICN formats.
    """
    patient_id = None
    with suppress(Exception):
        patient_id = param_dict["patientId"].lstrip(";").strip()

    return patient_id


class PatientHandlers:
    """Handlers for patient-related RPCs"""

    # Load VPR template once at class level
    _vpr_template = None

    @classmethod
    def _load_vpr_template(cls) -> dict:
        """Load the VPR template JSON file"""
        if cls._vpr_template is None:
            template_path = (
                Path(__file__).parent / ".." / ".." / "data" / "_VistARawSheba.json"
            )
            with template_path.open() as f:
                cls._vpr_template = json.load(f)
        return cls._vpr_template

    @staticmethod
    def _inject_patient_data(vpr_data: dict, patient: dict) -> dict:
        """
        Inject patient-specific data into VPR template.
        This modifies UIDs and patient demographics while preserving the rest of the structure.
        """
        # Deep copy to avoid modifying the template
        result = copy.deepcopy(vpr_data)

        # Handle both wrapped (payload.data) and unwrapped (data) formats
        # Check if this is wrapped format
        data_obj = (
            result["payload"]
            if "payload" in result and isinstance(result["payload"], dict)
            else result
        )

        # Dynamically detect the original patient ID from the VPR data
        original_patient_id = None

        # Update the patient demographics (first item in items array)
        if data_obj.get("data", {}).get("items") and len(data_obj["data"]["items"]) > 0:
            patient_item = data_obj["data"]["items"][0]

            # Extract the original patient ID from the VPR data
            if patient_item.get("localId"):
                original_patient_id = str(patient_item["localId"])
            elif patient_item.get("uid"):
                # Extract from UID like "urn:va:patient:84F0:237:237"
                uid_parts = patient_item["uid"].split(":")
                if len(uid_parts) >= 5:
                    original_patient_id = uid_parts[4]

            # If we couldn't detect the original patient ID, we can't proceed safely
            if not original_patient_id:
                raise ValueError(
                    "Could not determine original patient ID from VPR data"
                )

            # Update basic demographics
            patient_item["fullName"] = patient["name"]
            patient_item["familyName"] = patient["name"].split(",")[0]
            patient_item["givenNames"] = (
                patient["name"].split(",")[1].strip() if "," in patient["name"] else ""
            )
            patient_item["ssn"] = int(patient["ssn"].replace("***-**-", "666000"))
            patient_item["dateOfBirth"] = int(patient["dob"])
            patient_item["genderCode"] = f"urn:va:pat-gender:{patient['gender']}"
            patient_item["genderName"] = (
                "Male" if patient["gender"] == "M" else "Female"
            )

            patient_item["dfn"] = patient["dfn"]
            patient_item["icn"] = patient["icn"]
            patient_item["localId"] = int(patient["dfn"])

            # Update address
            # Parse address from single string format "street, city, state zip"
            address_parts = patient["address"].split(",")
            street = address_parts[0].strip() if len(address_parts) > 0 else "UNKNOWN"
            city = address_parts[1].strip() if len(address_parts) > 1 else "UNKNOWN"
            state_zip = (
                address_parts[2].strip() if len(address_parts) > 2 else "UNKNOWN 00000"
            )

            # Split state and zip
            state_zip_parts = state_zip.split()
            state = state_zip_parts[0] if len(state_zip_parts) > 0 else "UNKNOWN"
            zip_code = state_zip_parts[1] if len(state_zip_parts) > 1 else "00000"

            patient_item["addresses"] = [
                {
                    "city": city,
                    "postalCode": zip_code,
                    "stateProvince": state,
                    "streetLine1": street,
                }
            ]

            # Update telecoms
            telecoms = []
            if patient.get("phone"):
                telecoms.append(
                    {
                        "telecom": patient["phone"],
                        "usageCode": "HP",
                        "usageName": "home phone",
                    }
                )
            if patient.get("cellPhone"):
                telecoms.append(
                    {
                        "telecom": patient["cellPhone"],
                        "usageCode": "MC",
                        "usageName": "mobile contact",
                    }
                )
            if patient.get("workPhone"):
                telecoms.append(
                    {
                        "telecom": patient["workPhone"],
                        "usageCode": "WP",
                        "usageName": "work place",
                    }
                )
            patient_item["telecoms"] = telecoms

            # Update emergency contact
            if patient.get("emergencyContact"):
                ec = patient["emergencyContact"]
                patient_item["supports"] = [
                    {
                        "contactTypeCode": "urn:va:pat-contact:NOK",
                        "contactTypeName": "Next of Kin",
                        "name": ec["name"],
                    },
                    {
                        "contactTypeCode": "urn:va:pat-contact:ECON",
                        "contactTypeName": "Emergency Contact",
                        "name": ec["name"],
                    },
                ]

            # Update veteran info
            if patient.get("veteranStatus"):
                vs = patient["veteranStatus"]
                patient_item["veteran"] = {
                    "isVet": 1,
                    "lrdfn": int(patient["dfn"]),  # Using DFN as lrdfn for simplicity
                    "serviceConnected": vs.get("serviceConnected", False),
                    "serviceConnectionPercent": vs.get("serviceConnectedPercent", 0),
                }

            # Update patient UID
            patient_item["uid"] = (
                f"urn:va:patient:84F0:{patient['dfn']}:{patient['dfn']}"
            )

            # Update briefId (construct from name)
            name_parts = patient["name"].split(",")
            if len(name_parts) >= 2:
                last_initial = name_parts[0][0] if name_parts[0] else ""
                # Get last 4 of SSN substitute
                ssn_last4 = patient["ssn"].split("-")[-1]
                patient_item["briefId"] = f"{last_initial}{ssn_last4}"

            # Update marital status
            if patient.get("maritalStatus"):
                marital_code_map = {
                    "SINGLE": "S",
                    "MARRIED": "M",
                    "DIVORCED": "D",
                    "WIDOWED": "W",
                }
                code = marital_code_map.get(patient["maritalStatus"], "U")
                patient_item["maritalStatuses"] = [
                    {
                        "code": f"urn:va:pat-maritalStatus:{code}",
                        "name": patient["maritalStatus"].title(),
                    }
                ]

            # Update religion
            if patient.get("religion"):
                patient_item["religionName"] = patient["religion"]

            # Update race and ethnicity
            if patient.get("race"):
                patient_item["races"] = [{"race": patient["race"]}]

            if patient.get("ethnicity"):
                patient_item["ethnicities"] = [{"ethnicity": patient["ethnicity"]}]

            # Update flags
            if patient.get("flags"):
                patient_item["flags"] = [
                    {"name": flag, "text": flag} for flag in patient["flags"]
                ]

            # Update service period from military info
            if patient.get("military", {}).get("serviceEra"):
                patient_item["servicePeriod"] = patient["military"]["serviceEra"]

            # Update eligibility info
            if patient.get("eligibility"):
                eligibility = patient["eligibility"]
                patient_item["eligibility"] = [
                    {
                        "name": eligibility.get("priorityGroup", "GROUP 5"),
                        "primary": 1,
                    }
                ]
                patient_item["eligibilityStatus"] = "VERIFIED"

            # Update all UIDs in the rest of the items to use the correct DFN
            # Replace the original patient ID with the requested patient's DFN
            for item in data_obj["data"]["items"][1:]:
                # Replace original patient ID with actual DFN in UIDs
                if "uid" in item and isinstance(item["uid"], str):
                    item["uid"] = item["uid"].replace(
                        f":{original_patient_id}:", f":{patient['dfn']}:"
                    )

                # Update any orderUid references
                if "orderUid" in item and isinstance(item["orderUid"], str):
                    item["orderUid"] = item["orderUid"].replace(
                        f":{original_patient_id}:", f":{patient['dfn']}:"
                    )

                # Update groupUid for lab results
                if "groupUid" in item and isinstance(item["groupUid"], str):
                    item["groupUid"] = item["groupUid"].replace(
                        f":{original_patient_id}:", f":{patient['dfn']}:"
                    )

        return result

    @staticmethod
    def handle_orwpt_list(parameters: list[Parameter]) -> str:
        """
        Handle ORWPT LIST - Patient search by name
        Returns delimited string format
        """
        # Get search prefix from first parameter
        search_prefix = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                # Remove ^ prefix if present
                search_prefix = param_value.lstrip("^")

        # Search patients
        results = search_patients_by_name(search_prefix)

        # Format as delimited string
        lines = []
        for patient in results:
            # Format: DFN^NAME^GENDER^DOB^SSN^SENSITIVE_FLAG
            line = f"{patient['dfn']}^{patient['name']}^{patient['gender']}^{patient['dob']}^{patient['ssn']}^NO"
            lines.append(line)

        return "\r\n".join(lines)

    @staticmethod
    def handle_orwpt_id_info(parameters: list[Parameter]) -> str:
        """
        Handle ORWPT ID INFO - Get patient demographics
        Returns Vista-formatted delimited string
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Get patient data
        patient = get_patient_by_dfn_or_icn(dfn)

        if not patient or patient.get("name") == "TEST,PATIENT":
            return ""

        # Format as Vista delimited string
        # First line: DFN^NAME^SSN^DOB^AGE^SEX^DIED^SERVICE_CONNECTED^SENSITIVE^TYPE
        first_line = f"{dfn}^{patient['name']}^{patient['ssn'].replace('***-**-', '')}^{patient['dob']}^{patient['age']}^{patient['gender']}^^^NO^"

        # Additional lines for address, phone, etc.
        lines = [first_line]

        # Add address lines
        if patient.get("address"):
            lines.append(f"ADDRESS: {patient['address']}")

        # Add phone
        if patient.get("phone"):
            lines.append(f"PHONE: {patient['phone']}")

        # Add cell phone
        if patient.get("cellPhone"):
            lines.append(f"CELL: {patient['cellPhone']}")

        # Add email
        if patient.get("email"):
            lines.append(f"EMAIL: {patient['email']}")

        # Add emergency contact
        if patient.get("emergencyContact"):
            ec = patient["emergencyContact"]
            lines.append(
                f"EMERGENCY CONTACT: {ec['name']} ({ec['relationship']}) {ec['phone']}"
            )

        return "\n".join(lines)

    @classmethod
    def handle_vpr_get_patient_data_json(
        cls, parameters: list[Parameter]
    ) -> dict[str, Any]:
        """
        Handle VPR GET PATIENT DATA JSON - Get comprehensive patient data
        Returns JSON object using the VPR template with injected patient data

        Supports parameter formats:
        1. Legacy format: [";DFN", "START_DATE", "STOP_DATE", "DOMAINS"]
        2. Named array format: [{"namedArray": {"patientId": "DFN"}}]
        """
        # Parse parameters
        patient_id: str | None = None
        # domains = []  # Currently unused

        # Check if this is the new named array format
        if parameters and len(parameters) > 0:
            first_param = parameters[0]
            param_value = first_param.get_value()

            # Check for named array format
            patient_id = patient_id_from_dfn_or_icn_param_value(param_value)
            if not patient_id:
                # Legacy parameter format
                for i, param in enumerate(parameters):
                    param_value = param.get_value()
                    if i == 0:  # Patient ID
                        if isinstance(param_value, str):
                            # Remove semicolon prefix if present
                            patient_id = param_value.lstrip(";")
                    elif i == 1 or i == 2:  # Start date
                        if isinstance(param_value, str):
                            pass
                    elif (
                        i == 3 and isinstance(param_value, str) and param_value
                    ):  # Domain list
                        # Domains are semicolon-separated
                        _ = param_value.split(";")  # domains variable not used

        if not patient_id:
            return {"error": "Patient ID not found"}

        # Get patient data
        patient = get_patient_by_dfn_or_icn(patient_id)

        if not patient or patient.get("name") == "TEST,PATIENT":
            return {"error": "Patient not found"}

        try:
            # Load the VPR template
            template = cls._load_vpr_template()

            # Inject patient-specific data
            result = cls._inject_patient_data(template, patient)

            # If the template was wrapped format, extract just the payload
            if "payload" in result and isinstance(result["payload"], dict):
                return result["payload"]

            # If domains were specified, we could filter items here
            # For now, return all data as the template includes comprehensive patient data
            return result

        except Exception as e:
            # Fall back to error response if template loading fails
            return {
                "apiVersion": "1.0",
                "error": f"Error loading VPR data: {e}",
            }

    @staticmethod
    def handle_orwpt_select(parameters: list[Parameter]) -> str:
        """
        Handle ORWPT SELECT - Set patient context
        Returns success indicator
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Check if patient exists
        patient = get_patient_by_dfn_or_icn(dfn)

        if not patient or patient.get("name") == "TEST,PATIENT":
            return "0^Patient not found"

        # Return success
        return f"1^{patient['name']}"
