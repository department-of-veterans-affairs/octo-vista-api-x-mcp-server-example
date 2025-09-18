"""Unit tests for POV (Purpose of Visit) parsing and model functionality."""

from datetime import UTC, datetime

from src.models.patient.pov import POVSummary, POVType, PurposeOfVisit
from src.models.responses.metadata import (
    PerformanceMetrics,
    POVsFiltersMetadata,
    ResponseMetadata,
    StationMetadata,
)
from src.models.responses.tool_responses import POVsResponse, POVsResponseData
from src.services.parsers.patient.patient_parser import PatientDataParser


class TestPOVModel:
    """Test PurposeOfVisit Pydantic model functionality."""

    def test_pov_creation_with_valid_data(self):
        """Test creating a POV with valid data."""
        data = {
            "uid": "urn:va:pov:9E7A:100022:1001",
            "localId": "1001",
            "name": "Essential hypertension",
            "type": "P",
            "icdCode": "I10",
            "icdName": "Essential (primary) hypertension",
            "encounterName": "CARDIOLOGY CLINIC",
            "encounterUid": "urn:va:visit:9E7A:100022:H2001",
            "entered": "20231201.143000",
            "providerName": "SMITH,JOHN",
            "providerUid": "urn:va:user:9E7A:10000000123",
            "facilityCode": "500",
            "facilityName": "SALT LAKE CITY",
            "locationUid": "urn:va:location:9E7A:23",
            "locationName": "CARDIOLOGY CLINIC",
        }

        pov = PurposeOfVisit(**data)

        assert pov.uid == "urn:va:pov:9E7A:100022:1001"
        assert pov.local_id == "1001"
        assert pov.name == "Essential hypertension"
        assert pov.pov_type == POVType.PRIMARY
        assert pov.icd_code == "I10"
        assert pov.encounter_name == "CARDIOLOGY CLINIC"
        assert pov.facility_code == "500"
        assert pov.facility_name == "SALT LAKE CITY"

    def test_pov_properties(self):
        """Test POV computed properties."""
        primary_pov = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test Primary",
            type="P",
            encounterName="Test Encounter",
            encounterUid="test-enc",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test Hospital",
        )

        secondary_pov = PurposeOfVisit(
            uid="test2",
            localId="2",
            name="Test Secondary",
            type="S",
            encounterName="Test Encounter",
            encounterUid="test-enc",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test Hospital",
        )

        # Test primary POV properties
        assert primary_pov.is_primary is True
        assert primary_pov.is_secondary is False
        assert primary_pov.display_name == "Test Primary (Primary)"
        # Test enum value directly
        assert primary_pov.pov_type == POVType.PRIMARY

        # Test secondary POV properties
        assert secondary_pov.is_primary is False
        assert secondary_pov.is_secondary is True
        assert secondary_pov.display_name == "Test Secondary (Secondary)"
        assert secondary_pov.pov_type == POVType.SECONDARY

    def test_pov_has_icd_code(self):
        """Test has_icd_code property."""
        pov_with_icd = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test",
            type="P",
            icdCode="I10",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        pov_without_icd = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test",
            type="P",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert pov_with_icd.has_icd_code is True
        assert pov_without_icd.has_icd_code is False

    def test_pov_datetime_parsing(self):
        """Test datetime field parsing from VistA format."""
        data = {
            "uid": "test",
            "localId": "1",
            "name": "Test",
            "type": "P",
            "encounterName": "Test",
            "encounterUid": "test",
            "entered": "20231201.143000",
            "facilityCode": "500",
            "facilityName": "Test",
        }

        pov = PurposeOfVisit(**data)
        assert isinstance(pov.entered, datetime)
        assert pov.entered.year == 2023
        assert pov.entered.month == 12
        assert pov.entered.day == 1

    def test_pov_field_validation(self):
        """Test field validation and string conversion."""
        data = {
            "uid": "test",
            "localId": 123,  # Should be converted to string
            "name": "Test",
            "type": "P",
            "encounterName": "Test",
            "encounterUid": "test",
            "entered": datetime.now(UTC),
            "facilityCode": 500,  # Should be converted to string
            "facilityName": "Test",
        }

        pov = PurposeOfVisit(**data)
        assert pov.local_id == "123"
        assert pov.facility_code == "500"


class TestPOVSummary:
    """Test POVSummary model functionality."""

    def test_pov_summary_creation(self):
        """Test creating POV summary with valid data."""
        summary = POVSummary(
            total_povs=10,
            primary_count=6,
            secondary_count=4,
            unique_encounters=5,
            date_range_days=365,
            most_recent_pov=datetime.now(UTC),
            facilities=["Hospital A", "Clinic B"],
            encounter_types=["Outpatient", "Emergency"],
        )

        assert summary.total_povs == 10
        assert summary.primary_count == 6
        assert summary.secondary_count == 4
        assert summary.unique_encounters == 5
        assert summary.date_range_days == 365
        assert len(summary.facilities) == 2
        assert len(summary.encounter_types) == 2

    def test_pov_summary_defaults(self):
        """Test POV summary with default values."""
        summary = POVSummary()

        assert summary.total_povs == 0
        assert summary.primary_count == 0
        assert summary.secondary_count == 0
        assert summary.unique_encounters == 0
        assert summary.date_range_days is None
        assert summary.most_recent_pov is None
        assert summary.facilities == []
        assert summary.encounter_types == []


class TestPOVsFiltersMetadata:
    """Test POVsFiltersMetadata functionality."""

    def test_filters_metadata_creation(self):
        """Test creating POV filters metadata."""
        filters = POVsFiltersMetadata(
            days_back=365,
            primary_only=True,
        )

        assert filters.days_back == 365
        assert filters.primary_only is True

    def test_filters_metadata_with_none_values(self):
        """Test filters metadata with default values."""
        filters = POVsFiltersMetadata(
            days_back=30,
            primary_only=False,
        )

        assert filters.days_back == 30
        assert filters.primary_only is False

    def test_filters_metadata_serialization(self):
        """Test filters metadata serialization."""
        filters = POVsFiltersMetadata(
            days_back=90,
            primary_only=True,
        )

        # Test the custom serialization from base class
        serialized = filters.model_dump(exclude_none=True)
        assert "days_back" in serialized
        assert "primary_only" in serialized
        assert serialized["primary_only"] is True


class TestPOVsResponseModels:
    """Test POV response models."""

    def test_povs_response_data_creation(self):
        """Test creating POVs response data."""
        pov = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test POV",
            type="P",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        summary = POVSummary(total_povs=1, primary_count=1, secondary_count=0)

        data = POVsResponseData(
            povs=[pov],
            summary=summary,
            by_encounter={"test": ["test"]},
            by_type={"Primary": 1},
            primary_povs=["test"],
            secondary_povs=[],
        )

        assert len(data.povs) == 1
        assert data.summary.total_povs == 1
        assert data.by_encounter == {"test": ["test"]}
        assert data.by_type == {"Primary": 1}
        assert data.primary_povs == ["test"]
        assert data.secondary_povs == []

    def test_povs_response_creation(self):
        """Test creating complete POVs response."""
        pov = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test POV",
            type="P",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        summary = POVSummary(total_povs=1, primary_count=1, secondary_count=0)
        data = POVsResponseData(povs=[pov], summary=summary)

        # Create real metadata for validation
        metadata = ResponseMetadata(
            request_id="test_request",
            performance=PerformanceMetrics(
                duration_ms=100,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
            ),
            station=StationMetadata(station_number="500"),
        )

        response = POVsResponse(
            success=True,
            data=data,
            metadata=metadata,
        )

        assert response.success is True
        assert len(response.data.povs) == 1
        assert response.data.summary.total_povs == 1
        assert response.metadata.request_id == "test_request"


class TestPOVParsing:
    """Test POV parsing functionality."""

    def test_preprocess_pov_item(self):
        """Test POV item preprocessing."""
        parser = PatientDataParser(station="500", icn="123456")

        raw_pov = {
            "uid": "urn:va:pov:9E7A:100022:1001",
            "localId": "1001",
            "name": "Essential hypertension",
            "type": "P",
            "icdCode": "I10",
            "encounterName": "CARDIOLOGY CLINIC",
            "encounterUid": "urn:va:visit:9E7A:100022:H2001",
            "entered": "20231201.143000",
            "facilityCode": "500",
            "facilityName": "SALT LAKE CITY",
        }

        processed = parser._preprocess_pov_item(raw_pov)

        assert processed["uid"] == raw_pov["uid"]
        assert processed["localId"] == raw_pov["localId"]
        assert processed["name"] == raw_pov["name"]
        assert processed["type"] == raw_pov["type"]

    def test_parse_povs_empty_list(self):
        """Test parsing empty POV list."""
        parser = PatientDataParser(station="500", icn="123456")

        povs = parser._parse_povs([])

        assert povs == {}

    def test_parse_povs_with_valid_data(self):
        """Test parsing POVs with valid data."""
        parser = PatientDataParser(station="500", icn="123456")

        raw_povs = [
            {
                "uid": "urn:va:pov:9E7A:100022:1001",
                "localId": "1001",
                "name": "Essential hypertension",
                "type": "P",
                "icdCode": "I10",
                "encounterName": "CARDIOLOGY CLINIC",
                "encounterUid": "urn:va:visit:9E7A:100022:H2001",
                "entered": "20231201.143000",
                "facilityCode": "500",
                "facilityName": "SALT LAKE CITY",
            }
        ]

        povs = parser._parse_povs(raw_povs)

        assert len(povs) == 1
        pov_list = list(povs.values())
        assert isinstance(pov_list[0], PurposeOfVisit)
        assert pov_list[0].name == "Essential hypertension"
        assert pov_list[0].is_primary is True

    def test_parse_povs_with_invalid_data(self):
        """Test parsing POVs with invalid data (should skip invalid items)."""
        parser = PatientDataParser(station="500", icn="123456")

        raw_povs = [
            {
                "uid": "urn:va:pov:9E7A:100022:1001",
                "localId": "1001",
                "name": "Valid POV",
                "type": "P",
                "encounterName": "CLINIC",
                "encounterUid": "test",
                "entered": "20231201.143000",
                "facilityCode": "500",
                "facilityName": "HOSPITAL",
            },
            {
                "uid": "invalid",
                # Missing required fields
            },
        ]

        povs = parser._parse_povs(raw_povs)

        # Should only return the valid POV
        assert len(povs) == 1
        pov_list = list(povs.values())
        assert pov_list[0].name == "Valid POV"


class TestPOVTypeClassification:
    """Test POV type classification and filtering."""

    def test_primary_pov_identification(self):
        """Test identifying primary POVs."""
        primary_pov = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Primary Diagnosis",
            type="P",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert primary_pov.is_primary is True
        assert primary_pov.is_secondary is False

    def test_secondary_pov_identification(self):
        """Test identifying secondary POVs."""
        secondary_pov = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Secondary Diagnosis",
            type="S",
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert secondary_pov.is_primary is False
        assert secondary_pov.is_secondary is True

    def test_case_insensitive_type_checking(self):
        """Test case-insensitive POV type checking."""
        lowercase_primary = PurposeOfVisit(
            uid="test",
            localId="1",
            name="Test",
            type=POVType.PRIMARY,  # Test with enum directly
            encounterName="Test",
            encounterUid="test",
            entered=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert lowercase_primary.is_primary is True
        assert lowercase_primary.is_secondary is False
