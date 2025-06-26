"""
Patient-related RPC handlers
"""

from typing import Any

from src.data.clinical_data import get_clinical_data_for_patient
from src.data.test_patients import get_patient_by_dfn, search_patients_by_name
from src.rpc.models import Parameter


class PatientHandlers:
    """Handlers for patient-related RPCs"""

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
        patient = get_patient_by_dfn(dfn)

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
            lines.append(f"EMERGENCY CONTACT: {ec['name']} ({ec['relationship']}) {ec['phone']}")

        return "\n".join(lines)

    @staticmethod
    def handle_vpr_get_patient_data_json(parameters: list[Parameter]) -> dict[str, Any]:
        """
        Handle VPR GET PATIENT DATA JSON - Get comprehensive patient data
        Returns JSON object
        """
        # Parse parameters
        patient_id = ""
        domains = []

        # VPR uses different parameter format
        if parameters:
            for i, param in enumerate(parameters):
                param_value = param.get_value()
                if i == 0:  # Patient ID
                    if isinstance(param_value, str):
                        # Remove semicolon prefix if present
                        patient_id = param_value.lstrip(";")
                elif i == 1 or i == 2:  # Start date
                    if isinstance(param_value, str):
                        pass
                elif i == 3:  # Domain list
                    if isinstance(param_value, str) and param_value:
                        # Domains are semicolon-separated
                        domains = param_value.split(";")

        # If no domains specified, return all
        if not domains:
            domains = [
                "patient",
                "allergy",
                "appointment",
                "consult",
                "document",
                "education",
                "exam",
                "factor",
                "image",
                "immunization",
                "lab",
                "med",
                "order",
                "problem",
                "procedure",
                "surgery",
                "visit",
                "vital",
            ]

        # Get patient data
        patient = get_patient_by_dfn(patient_id)

        if not patient or patient.get("name") == "TEST,PATIENT":
            return {"error": "Patient not found"}

        # Build response
        response = {
            "apiVersion": "1.0",
            "data": {
                "updated": 20240116143000,  # YYYYMMDDHHMMSS format
                "totalItems": 0,
                "items": [],
            },
        }

        # Add patient demographics if requested
        if "patient" in domains:
            patient_item = {
                "uid": f"urn:va:patient:{patient_id}",
                "pid": patient_id,
                "fullName": patient["name"],
                "displayName": patient["name"],
                "ssn": patient["ssn"],
                "birthDate": patient["dob"],
                "gender": patient["gender"],
                "address": [
                    {
                        "use": "home",
                        "line": [patient["address"]],
                        "city": patient.get("city", ""),
                        "state": patient.get("state", ""),
                        "postalCode": patient.get("zip", ""),
                    }
                ],
                "telecom": [
                    {"use": "home", "value": patient["phone"]},
                    {"use": "mobile", "value": patient.get("cellPhone", "")},
                ],
            }
            response["data"]["items"].append(patient_item)
            response["data"]["totalItems"] += 1

        # Add other domains
        for domain in domains:
            if domain == "patient":
                continue  # Already handled

            # Get clinical data for domain
            domain_data = get_clinical_data_for_patient(patient_id, domain)

            # Convert to VPR format
            for item in domain_data:
                vpr_item = {
                    "uid": f"urn:va:{domain}:{patient_id}:{response['data']['totalItems']}",
                    "kind": domain.upper(),
                    "summary": item.get("description", item.get("name", "")),
                    "pid": patient_id,
                }

                # Add domain-specific fields
                if domain == "problem":
                    vpr_item.update(
                        {
                            "problemText": item["description"],
                            "icdCode": item.get("icd10", ""),
                            "status": item["status"],
                            "onset": item.get("onsetDate", ""),
                        }
                    )
                elif domain == "med":
                    vpr_item.update(
                        {
                            "name": item["name"],
                            "sig": item["sig"],
                            "status": item["status"],
                            "orderDate": item.get("orderDate", ""),
                        }
                    )
                elif domain == "allergy":
                    vpr_item.update(
                        {
                            "agent": item["allergen"],
                            "reaction": item["reaction"],
                            "severity": item["severity"],
                        }
                    )
                elif domain == "vital":
                    vpr_item.update(
                        {
                            "dateTime": item["date"],
                            "bp": item.get("bp", ""),
                            "pulse": item.get("pulse", ""),
                            "temp": item.get("temp", ""),
                            "weight": item.get("weight", ""),
                        }
                    )
                elif domain == "lab":
                    vpr_item.update(
                        {
                            "test": item["test"],
                            "result": item["value"],
                            "units": item.get("units", ""),
                            "referenceRange": item.get("refRange", ""),
                            "flag": item.get("flag", ""),
                            "dateTime": item["date"],
                        }
                    )

                response["data"]["items"].append(vpr_item)
                response["data"]["totalItems"] += 1

        return response

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
        patient = get_patient_by_dfn(dfn)

        if not patient or patient.get("name") == "TEST,PATIENT":
            return "0^Patient not found"

        # Return success
        return f"1^{patient['name']}"
