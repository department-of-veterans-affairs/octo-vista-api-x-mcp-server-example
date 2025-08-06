"""Unit tests for location mapper utility"""

from src.services.formatters.location_mapper import LocationMapper


class TestLocationMapper:
    """Test location mapper functionality"""

    def test_get_location_type_inpatient(self):
        """Test inpatient location type classification"""
        assert LocationMapper.get_location_type("WARD", "MEDICAL WARD") == "inpatient"
        assert (
            LocationMapper.get_location_type("ICU", "INTENSIVE CARE UNIT")
            == "inpatient"
        )
        assert (
            LocationMapper.get_location_type("CCU", "CORONARY CARE UNIT") == "inpatient"
        )
        assert (
            LocationMapper.get_location_type("STEPDOWN", "STEP-DOWN UNIT")
            == "inpatient"
        )

    def test_get_location_type_emergency(self):
        """Test emergency location type classification"""
        assert LocationMapper.get_location_type("ER", "EMERGENCY ROOM") == "emergency"
        assert (
            LocationMapper.get_location_type("TRAUMA", "TRAUMA CENTER") == "emergency"
        )
        assert LocationMapper.get_location_type("URGENT", "URGENT CARE") == "emergency"

    def test_get_location_type_surgery(self):
        """Test surgery location type classification"""
        assert LocationMapper.get_location_type("OR", "OPERATING ROOM") == "surgery"
        assert (
            LocationMapper.get_location_type("PREOP", "PRE-OPERATIVE UNIT") == "surgery"
        )
        assert (
            LocationMapper.get_location_type("POSTOP", "POST-OPERATIVE UNIT")
            == "surgery"
        )
        assert (
            LocationMapper.get_location_type("PACU", "POST-ANESTHESIA CARE UNIT")
            == "surgery"
        )

    def test_get_location_type_observation(self):
        """Test observation location type classification"""
        assert (
            LocationMapper.get_location_type("OBS", "OBSERVATION UNIT") == "observation"
        )
        assert (
            LocationMapper.get_location_type("SHORT", "SHORT STAY UNIT")
            == "observation"
        )

    def test_get_location_type_outpatient(self):
        """Test outpatient location type classification"""
        assert (
            LocationMapper.get_location_type("CLINIC", "PRIMARY CARE CLINIC")
            == "outpatient"
        )
        assert LocationMapper.get_location_type("LAB", "LABORATORY") == "outpatient"
        assert (
            LocationMapper.get_location_type("RADIOLOGY", "RADIOLOGY DEPARTMENT")
            == "outpatient"
        )
        assert LocationMapper.get_location_type("PHARMACY", "PHARMACY") == "outpatient"

    def test_get_location_type_unknown(self):
        """Test unknown location type classification"""
        assert LocationMapper.get_location_type("", "") == "unknown"
        assert (
            LocationMapper.get_location_type("UNKNOWN", "UNKNOWN LOCATION") == "unknown"
        )

    def test_standardize_location_name(self):
        """Test location name standardization"""
        assert LocationMapper.standardize_location_name("ER") == "Emergency Room"
        assert LocationMapper.standardize_location_name("ICU") == "Intensive Care Unit"
        assert LocationMapper.standardize_location_name("OR") == "Operating Room"
        assert LocationMapper.standardize_location_name("OBS") == "Observation Unit"
        assert LocationMapper.standardize_location_name("UNKNOWN") == "UNKNOWN"

    def test_get_facility_name(self):
        """Test facility name mapping"""
        assert LocationMapper.get_facility_name("500") == "Washington DC VAMC"
        assert LocationMapper.get_facility_name("501") == "Baltimore VAMC"
        assert LocationMapper.get_facility_name("999") == "Station 999"  # Unknown code

    def test_location_type_checkers(self):
        """Test location type checker methods"""
        # Test inpatient checkers
        assert LocationMapper.is_inpatient_location("WARD", "MEDICAL WARD") is True
        assert LocationMapper.is_inpatient_location("ER", "EMERGENCY ROOM") is False

        # Test emergency checkers
        assert LocationMapper.is_emergency_location("ER", "EMERGENCY ROOM") is True
        assert LocationMapper.is_emergency_location("WARD", "MEDICAL WARD") is False

        # Test surgery checkers
        assert LocationMapper.is_surgery_location("OR", "OPERATING ROOM") is True
        assert LocationMapper.is_surgery_location("WARD", "MEDICAL WARD") is False

        # Test observation checkers
        assert LocationMapper.is_observation_location("OBS", "OBSERVATION UNIT") is True
        assert LocationMapper.is_observation_location("WARD", "MEDICAL WARD") is False

        # Test outpatient checkers
        assert (
            LocationMapper.is_outpatient_location("CLINIC", "PRIMARY CARE CLINIC")
            is True
        )
        assert LocationMapper.is_outpatient_location("WARD", "MEDICAL WARD") is False

    def test_get_location_summary(self):
        """Test comprehensive location summary"""
        summary = LocationMapper.get_location_summary("WARD", "MEDICAL WARD")

        assert summary["code"] == "WARD"
        assert summary["name"] == "MEDICAL WARD"
        assert summary["type"] == "inpatient"
        assert summary["is_inpatient"] is True
        assert summary["is_emergency"] is False
        assert summary["is_surgery"] is False
        assert summary["is_observation"] is False
        assert summary["is_outpatient"] is False

    def test_get_location_summary_emergency(self):
        """Test emergency location summary"""
        summary = LocationMapper.get_location_summary("ER", "EMERGENCY ROOM")

        assert summary["code"] == "ER"
        assert summary["name"] == "EMERGENCY ROOM"
        assert summary["type"] == "emergency"
        assert summary["is_inpatient"] is False
        assert summary["is_emergency"] is True
        assert summary["is_surgery"] is False
        assert summary["is_observation"] is False
        assert summary["is_outpatient"] is False

    def test_get_location_summary_outpatient(self):
        """Test outpatient location summary"""
        summary = LocationMapper.get_location_summary("CLINIC", "PRIMARY CARE CLINIC")

        assert summary["code"] == "CLINIC"
        assert summary["name"] == "PRIMARY CARE CLINIC"
        assert summary["type"] == "outpatient"
        assert summary["is_inpatient"] is False
        assert summary["is_emergency"] is False
        assert summary["is_surgery"] is False
        assert summary["is_observation"] is False
        assert summary["is_outpatient"] is True

    def test_case_insensitive_matching(self):
        """Test that location matching is case insensitive"""
        assert LocationMapper.get_location_type("ward", "medical ward") == "inpatient"
        assert LocationMapper.get_location_type("Ward", "Medical Ward") == "inpatient"
        assert LocationMapper.get_location_type("ER", "emergency room") == "emergency"
        assert LocationMapper.get_location_type("er", "Emergency Room") == "emergency"

    def test_partial_matching(self):
        """Test partial matching in location names"""
        assert (
            LocationMapper.get_location_type("WARD", "MEDICAL WARD UNIT") == "inpatient"
        )
        assert (
            LocationMapper.get_location_type("ICU", "INTENSIVE CARE UNIT FLOOR")
            == "inpatient"
        )
        assert (
            LocationMapper.get_location_type("CLINIC", "PRIMARY CARE CLINIC DEPARTMENT")
            == "outpatient"
        )
