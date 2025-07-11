"""
Clinical RPC handlers for medications, labs, vitals, problems, and allergies
"""

from src.data.clinical_data import (
    PATIENT_ALLERGIES,
    PATIENT_LABS,
    PATIENT_MEDICATIONS,
    PATIENT_PROBLEMS,
    PATIENT_VITALS,
)
from src.rpc.models import Parameter


class ClinicalHandlers:
    """Handlers for clinical RPCs"""

    @staticmethod
    def handle_orwps_active(parameters: list[Parameter]) -> str:
        """
        Handle ORWPS ACTIVE - Get active medications
        Returns delimited string format
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Get patient medications
        medications = PATIENT_MEDICATIONS.get(dfn, [])

        # Format response
        lines = ["~Active Medications"]

        for i, med in enumerate(medications, 1):
            if med["status"] == "ACTIVE":
                # Format: SEQ^NAME^SIG^STARTDATE^STOPDATE^QTY^REFILLS^MEDROUTE
                line = f"{i}^{med['name']}^{med['sig']}^{med['orderDate']}^^{med.get('quantity', '90')}^{med.get('refills', '5')}^Y"
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def handle_orwlrr_interim(parameters: list[Parameter]) -> str:
        """
        Handle ORWLRR INTERIM - Get lab results
        Returns delimited string format
        Parameters: DFN, startDate, endDate, tests, dateRange, others, maxOccurrences
        """
        # Get DFN from first parameter
        dfn = ""
        max_results = 50

        if parameters:
            if len(parameters) > 0:
                param_value = parameters[0].get_value()
                if isinstance(param_value, str):
                    dfn = param_value

            # Get max results from 7th parameter if provided
            if len(parameters) > 6:
                param_value = parameters[6].get_value()
                if isinstance(param_value, str) and param_value.isdigit():
                    max_results = int(param_value)

        # Get patient labs
        labs = PATIENT_LABS.get(dfn, [])[:max_results]

        # Format response
        lines = ["~Lab Results"]

        for i, lab in enumerate(labs, 1):
            # Format: SEQ^TEST^VALUE^UNITS^REFRANGE^DATETIME^FLAG^STATUS
            flag = lab.get("flag", "")
            status = "F"  # Final
            line = f"{i}^{lab['test']}^{lab['value']}^{lab.get('units', '')}^{lab.get('refRange', '')}^{lab['date']}^{flag}^{status}"
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def handle_orqqvi_vitals(parameters: list[Parameter]) -> str:
        """
        Handle ORQQVI VITALS - Get vital signs
        Returns delimited string format
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Get patient vitals
        vitals = PATIENT_VITALS.get(dfn, [])

        # Format response
        lines = ["~Vital Signs"]

        # Get most recent vitals set
        if vitals:
            latest = vitals[0]
            date = latest["date"]

            # Add each vital type as separate line
            # Format: DATETIME^TYPE^VALUE^UNITS^QUALIFIERS
            if "bp" in latest:
                lines.append(f"{date}^BP^{latest['bp']}^^SITTING")
            if "pulse" in latest:
                lines.append(f"{date}^P^{latest['pulse']}^^REGULAR")
            if "resp" in latest:
                lines.append(f"{date}^R^{latest['resp']}")
            if "temp" in latest:
                lines.append(f"{date}^T^{latest['temp']}^F")
            if "weight" in latest:
                lines.append(f"{date}^WT^{latest['weight']}^LB")
            if "height" in latest:
                lines.append(f"{date}^HT^{latest['height']}^IN")
            if "pain" in latest:
                lines.append(f"{date}^PAIN^{latest['pain']}^0-10")

        return "\n".join(lines)

    @staticmethod
    def handle_orqqpl_problem_list(parameters: list[Parameter]) -> str:
        """
        Handle ORQQPL PROBLEM LIST - Get problem list
        Returns delimited string format
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Get patient problems
        problems = PATIENT_PROBLEMS.get(dfn, [])

        # Format response
        lines = []

        for i, prob in enumerate(problems, 1):
            # Format: SEQ^IEN^DESCRIPTION^ICD^STATUS^ONSETDATE^TYPE
            prob_type = "CHRONIC" if "CHRONIC" in prob.get("description", "").upper() else "ACUTE"
            line = f"{i}^S:{78900 + i}^{prob['description']}^ICD-10: {prob['icd10']}^{prob['status'][0]}^{prob.get('onsetDate', '')}^{prob_type}"
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def handle_orqqal_list(parameters: list[Parameter]) -> str:
        """
        Handle ORQQAL LIST - Get allergy list
        Returns delimited string format
        """
        # Get DFN from first parameter
        dfn = ""
        if parameters and len(parameters) > 0:
            param_value = parameters[0].get_value()
            if isinstance(param_value, str):
                dfn = param_value

        # Get patient allergies
        allergies = PATIENT_ALLERGIES.get(dfn, [])

        # Format response
        lines = []

        for i, allergy in enumerate(allergies, 1):
            # Format: SEQ^ALLERGEN^TYPE^DATEENTERED^REACTION^VERIFIED
            allergy_type = allergy.get("type", "DRUG")
            date_entered = allergy.get("dateEntered", "3200601")
            verified = allergy.get("verified", "VERIFIED")

            line = f"{i}^{allergy['allergen']}^{allergy_type}^{date_entered}^{allergy['reaction']}^{verified}"
            lines.append(line)

        return "\n".join(lines)
