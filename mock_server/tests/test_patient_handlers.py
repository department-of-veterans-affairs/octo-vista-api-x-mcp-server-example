"""
Unit tests for patient handlers
"""

from src.rpc.handlers.patient_handlers import PatientHandlers
from src.rpc.models import Parameter


class TestVPRGetPatientDataJSON:
    """Test VPR GET PATIENT DATA JSON handler"""

    def test_legacy_parameter_format(self):
        """Test with legacy string parameters"""
        # Create parameters in legacy format
        parameters = [
            Parameter(string="100841"),  # Patient DFN
            Parameter(string=""),  # Start date
            Parameter(string=""),  # End date
            Parameter(string="patient;vital;med"),  # Domains
        ]

        # Call handler
        result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

        # Verify result
        assert isinstance(result, dict)
        assert "data" in result
        assert "items" in result["data"]

        # Check patient data was loaded
        items = result["data"]["items"]
        assert len(items) > 0
        patient_item = items[0]
        assert patient_item["localId"] == 100841

    def test_named_array_parameter_format(self):
        """Test with named array parameter format"""
        # Create parameters in named array format
        parameters = [Parameter(namedArray={"patientId": "100841"})]

        # Call handler
        result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

        # Verify result
        assert isinstance(result, dict)
        assert "data" in result
        assert "items" in result["data"]

        # Check patient data was loaded
        items = result["data"]["items"]
        assert len(items) > 0
        patient_item = items[0]
        assert patient_item["localId"] == 100841

    def test_patient_not_found(self):
        """Test with non-existent patient"""
        # Try with a patient that doesn't exist
        parameters = [Parameter(namedArray={"patientId": "999999"})]

        # Call handler
        result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

        # Should return error
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Patient not found"

    def test_empty_parameters(self):
        """Test with empty parameters"""
        # Call handler with empty parameters
        result = PatientHandlers.handle_vpr_get_patient_data_json([])

        # Should return error (no patient ID)
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Patient not found"

    def test_numeric_patient_id_in_named_array(self):
        """Test with numeric patient ID in named array"""
        # Create parameters with numeric patient ID
        parameters = [
            Parameter(namedArray={"patientId": 100841})  # Numeric instead of string
        ]

        # Call handler
        result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

        # Should still work (we convert to string)
        assert isinstance(result, dict)
        assert "data" in result
        assert "items" in result["data"]

        items = result["data"]["items"]
        assert len(items) > 0
        patient_item = items[0]
        assert patient_item["localId"] == 100841
