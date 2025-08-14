"""Unit tests for PatientDemographics model and parsing."""

from datetime import date

from src.models.patient.demographics import PatientDemographics
from src.services.parsers.patient.patient_parser import PatientDataParser


class TestPatientDemographicsModel:
    """Test PatientDemographics Pydantic model functionality."""

    def test_demographics_with_basic_fields(self):
        """Test creating PatientDemographics with basic required fields."""
        data = {
            "dfn": "100022",
            "icn": "1008714701V416111",
            "ssn": "666-11-4701",
            "fullName": "ANDERSON,JAMES ROBERT",
            "familyName": "ANDERSON",
            "givenNames": "JAMES ROBERT",
            "dateOfBirth": "1950-04-07",
            "genderCode": "M",
            "genderName": "Male",
        }

        demographics = PatientDemographics(**data)

        assert demographics.dfn == "100022"
        assert demographics.icn == "1008714701V416111"
        assert demographics.ssn == "666-11-4701"
        assert demographics.full_name == "ANDERSON,JAMES ROBERT"
        assert demographics.family_name == "ANDERSON"
        assert demographics.given_names == "JAMES ROBERT"
        assert demographics.date_of_birth == date(1950, 4, 7)
        assert demographics.gender_code == "M"
        assert demographics.gender_name == "Male"

    def test_demographics_with_new_fields(self):
        """Test creating PatientDemographics with new fields added for completeness."""
        data = {
            "dfn": "100022",
            "icn": "1008714701V416111",
            "ssn": "666-11-4701",
            "fullName": "VETERAN,JOHN DOE",
            "familyName": "VETERAN",
            "givenNames": "JOHN DOE",
            "dateOfBirth": "1950-04-07",
            "genderCode": "M",
            "genderName": "Male",
            # New fields
            "disability": [
                {"percent": 15, "condition": "INFLAMMATION OF IRIS"},
                {"percent": 30, "condition": "HEARING LOSS"},
                {"percent": 10, "condition": "TINNITUS"},
            ],
            "exposures": [
                {"type": "Agent Orange", "status": "Yes"},
                {"type": "MST", "status": "Unknown"},
                {"type": "Gulf War", "status": "No"},
            ],
            "facilities": [
                {
                    "name": "SALT LAKE CITY VA MEDICAL CENTER",
                    "id": "500",
                    "type": "VAMC",
                },
                {"name": "PROVO VA CLINIC", "id": "501", "type": "CBOC"},
            ],
            "pcTeamMembers": [
                {"team": "RED TEAM", "role": "PROVIDER", "name": "PROVIDER,ONE"},
                {"team": "RED TEAM", "role": "NURSE", "name": "NURSE,TWO"},
                {
                    "team": "RED TEAM",
                    "role": "COORDINATOR",
                    "name": "COORDINATOR,THREE",
                },
            ],
            "eligibility": [
                {"type": "SERVICE CONNECTED", "percent": "50% to 100%"},
                {"type": "VA HEALTHCARE", "status": "ELIGIBLE"},
                {"type": "DENTAL", "status": "ELIGIBLE"},
            ],
        }

        demographics = PatientDemographics(**data)

        # Verify new fields
        assert len(demographics.disability) == 3
        assert demographics.disability[0]["percent"] == 15
        assert demographics.disability[0]["condition"] == "INFLAMMATION OF IRIS"
        assert demographics.disability[1]["percent"] == 30
        assert demographics.disability[2]["condition"] == "TINNITUS"

        assert len(demographics.exposures) == 3
        assert demographics.exposures[0]["type"] == "Agent Orange"
        assert demographics.exposures[0]["status"] == "Yes"
        assert demographics.exposures[1]["type"] == "MST"
        assert demographics.exposures[2]["status"] == "No"

        assert len(demographics.facilities) == 2
        assert demographics.facilities[0]["name"] == "SALT LAKE CITY VA MEDICAL CENTER"
        assert demographics.facilities[0]["id"] == "500"
        assert demographics.facilities[1]["type"] == "CBOC"

        assert len(demographics.pc_team_members) == 3
        assert demographics.pc_team_members[0]["team"] == "RED TEAM"
        assert demographics.pc_team_members[0]["role"] == "PROVIDER"
        assert demographics.pc_team_members[1]["name"] == "NURSE,TWO"
        assert demographics.pc_team_members[2]["role"] == "COORDINATOR"

        assert len(demographics.eligibility) == 3
        assert demographics.eligibility[0]["type"] == "SERVICE CONNECTED"
        assert demographics.eligibility[0]["percent"] == "50% to 100%"
        assert demographics.eligibility[1]["status"] == "ELIGIBLE"

    def test_demographics_field_aliases(self):
        """Test that field aliases work correctly."""
        data = {
            "dfn": "100022",
            "icn": "1008714701V416111",
            "ssn": "666-11-4701",
            "fullName": "TEST,USER",
            "familyName": "TEST",
            "givenNames": "USER",
            "dateOfBirth": "1970-01-01",
            "genderCode": "F",
            "genderName": "Female",
            "pcTeamMembers": [
                {"team": "BLUE TEAM", "role": "PROVIDER", "name": "DOC,ONE"},
            ],
        }

        demographics = PatientDemographics(**data)

        # Verify alias works for input
        assert len(demographics.pc_team_members) == 1
        assert demographics.pc_team_members[0]["team"] == "BLUE TEAM"

        # Verify alias works for output
        output = demographics.model_dump(by_alias=True)
        assert "pcTeamMembers" in output
        assert output["pcTeamMembers"][0]["team"] == "BLUE TEAM"

    def test_demographics_empty_new_fields(self):
        """Test that new fields default to empty lists when not provided."""
        data = {
            "dfn": "100022",
            "icn": "1008714701V416111",
            "ssn": "666-11-4701",
            "fullName": "TEST,USER",
            "familyName": "TEST",
            "givenNames": "USER",
            "dateOfBirth": "1970-01-01",
            "genderCode": "M",
            "genderName": "Male",
        }

        demographics = PatientDemographics(**data)

        # Verify new fields default to empty lists
        assert demographics.disability == []
        assert demographics.exposures == []
        assert demographics.facilities == []
        assert demographics.pc_team_members == []
        assert demographics.eligibility == []

    def test_demographics_partial_new_fields(self):
        """Test demographics with only some new fields populated."""
        data = {
            "dfn": "100022",
            "icn": "1008714701V416111",
            "ssn": "666-11-4701",
            "fullName": "PARTIAL,TEST",
            "familyName": "PARTIAL",
            "givenNames": "TEST",
            "dateOfBirth": "1960-06-15",
            "genderCode": "M",
            "genderName": "Male",
            # Only some new fields
            "disability": [{"percent": 70, "condition": "PTSD"}],
            "eligibility": [{"type": "SERVICE CONNECTED", "percent": "70%"}],
            # Other new fields not provided
        }

        demographics = PatientDemographics(**data)

        # Verify populated fields
        assert len(demographics.disability) == 1
        assert demographics.disability[0]["percent"] == 70
        assert len(demographics.eligibility) == 1
        assert demographics.eligibility[0]["percent"] == "70%"

        # Verify unpopulated fields are empty
        assert demographics.exposures == []
        assert demographics.facilities == []
        assert demographics.pc_team_members == []


class TestPatientDemographicsParsing:
    """Test parsing of patient demographics from VPR data."""

    def test_parse_demographics_with_new_fields(self):
        """Test that parser correctly handles demographics with new fields."""
        vpr_data = {
            "data": {
                "items": [
                    {
                        "uid": "urn:va:patient:500:100022",
                        "dfn": "100022",
                        "icn": "1008714701V416111",
                        "ssn": "666114701",
                        "fullName": "VETERAN,COMPLETE",
                        "familyName": "VETERAN",
                        "givenNames": "COMPLETE",
                        "dateOfBirth": "19500407",
                        "genderCode": "urn:va:pat-gender:M",
                        "genderName": "Male",
                        # New fields from VistA
                        "disability": [
                            {"percent": 30, "condition": "KNEE INJURY"},
                            {"percent": 20, "condition": "BACK PAIN"},
                        ],
                        "exposures": [
                            {"type": "Agent Orange", "status": "Yes"},
                            {"type": "Burn Pits", "status": "Possible"},
                        ],
                        "facilities": [
                            {"name": "TAMPA VA", "id": "673", "lastVisit": "20240115"},
                        ],
                        "pcTeamMembers": [
                            {"team": "GREEN", "role": "PCP", "name": "SMITH,JOHN MD"},
                        ],
                        "eligibility": [
                            {"type": "SERVICE CONNECTED", "percent": "50%"},
                        ],
                    }
                ]
            }
        }

        parser = PatientDataParser(station="500", dfn="100022")
        result = parser.parse(vpr_data)

        # Verify demographics were parsed
        assert result.demographics is not None
        demographics = result.demographics

        # Verify basic fields
        assert demographics.dfn == "100022"
        assert demographics.full_name == "VETERAN,COMPLETE"

        # Verify new fields were parsed
        assert len(demographics.disability) == 2
        assert demographics.disability[0]["percent"] == 30
        assert demographics.disability[0]["condition"] == "KNEE INJURY"

        assert len(demographics.exposures) == 2
        assert demographics.exposures[0]["type"] == "Agent Orange"
        assert demographics.exposures[0]["status"] == "Yes"

        assert len(demographics.facilities) == 1
        assert demographics.facilities[0]["name"] == "TAMPA VA"
        assert demographics.facilities[0]["id"] == "673"

        assert len(demographics.pc_team_members) == 1
        assert demographics.pc_team_members[0]["team"] == "GREEN"
        assert demographics.pc_team_members[0]["role"] == "PCP"

        assert len(demographics.eligibility) == 1
        assert demographics.eligibility[0]["type"] == "SERVICE CONNECTED"
        assert demographics.eligibility[0]["percent"] == "50%"

    def test_parse_demographics_without_new_fields(self):
        """Test that parser handles demographics without new fields gracefully."""
        vpr_data = {
            "data": {
                "items": [
                    {
                        "uid": "urn:va:patient:500:100022",
                        "icn": "1008714701V416111",
                        "ssn": "666114701",
                        "fullName": "MINIMAL,USER",
                        "familyName": "MINIMAL",
                        "givenNames": "USER",
                        "dateOfBirth": "19700101",
                        "genderCode": "F",
                        "genderName": "Female",
                        # No new fields provided
                    }
                ]
            }
        }

        parser = PatientDataParser(station="500", dfn="100022")
        result = parser.parse(vpr_data)

        demographics = result.demographics
        assert demographics is not None

        # Verify basic fields work
        assert demographics.full_name == "MINIMAL,USER"
        assert demographics.gender_code == "F"

        # Verify new fields default to empty lists
        assert demographics.disability == []
        assert demographics.exposures == []
        assert demographics.facilities == []
        assert demographics.pc_team_members == []
        assert demographics.eligibility == []

    def test_parse_demographics_with_complex_data(self):
        """Test parsing demographics with complex nested data structures."""
        vpr_data = {
            "data": {
                "items": [
                    {
                        "uid": "urn:va:patient:500:100022",
                        "icn": "1008714701V416111",
                        "ssn": "666114701",
                        "fullName": "COMPLEX,DATA",
                        "familyName": "COMPLEX",
                        "givenNames": "DATA",
                        "dateOfBirth": "19550815",
                        "genderCode": "M",
                        "genderName": "Male",
                        # Complex disability data
                        "disability": [
                            {
                                "percent": 100,
                                "condition": "MULTIPLE CONDITIONS",
                                "effective_date": "20100101",
                                "review_date": "20250101",
                            }
                        ],
                        # Complex team structure
                        "pcTeamMembers": [
                            {
                                "team": "PACT RED",
                                "role": "PRIMARY CARE PROVIDER",
                                "name": "JOHNSON,SARAH MD",
                                "phone": "555-1234",
                                "email": "sjohnson@va.gov",
                            },
                            {
                                "team": "PACT RED",
                                "role": "RN CARE MANAGER",
                                "name": "DAVIS,MICHAEL RN",
                                "phone": "555-1235",
                            },
                            {
                                "team": "PACT RED",
                                "role": "CLINICAL ASSOCIATE",
                                "name": "WILSON,JENNIFER",
                            },
                            {
                                "team": "MENTAL HEALTH",
                                "role": "PSYCHIATRIST",
                                "name": "BROWN,ROBERT MD",
                            },
                        ],
                        # Multiple facilities with details
                        "facilities": [
                            {
                                "name": "MAIN VA MEDICAL CENTER",
                                "id": "500",
                                "type": "VAMC",
                                "primary": True,
                                "enrollment_date": "20050101",
                            },
                            {
                                "name": "NORTH CLINIC",
                                "id": "500GA",
                                "type": "CBOC",
                                "primary": False,
                            },
                            {
                                "name": "SPECIALTY CARE CENTER",
                                "id": "500SP",
                                "type": "SPECIALTY",
                            },
                        ],
                        # Complex eligibility
                        "eligibility": [
                            {
                                "type": "SERVICE CONNECTED",
                                "percent": "100%",
                                "permanent": True,
                            },
                            {"type": "CATASTROPHICALLY DISABLED", "status": "VERIFIED"},
                            {"type": "PRIORITY GROUP", "group": "1"},
                        ],
                    }
                ]
            }
        }

        parser = PatientDataParser(station="500", dfn="100022")
        result = parser.parse(vpr_data)

        demographics = result.demographics
        assert demographics is not None

        # Verify complex data is preserved
        assert demographics.disability[0]["percent"] == 100
        assert "effective_date" in demographics.disability[0]

        assert len(demographics.pc_team_members) == 4
        mental_health = [
            m for m in demographics.pc_team_members if m["team"] == "MENTAL HEALTH"
        ]
        assert len(mental_health) == 1
        assert mental_health[0]["role"] == "PSYCHIATRIST"

        assert len(demographics.facilities) == 3
        primary_facility = [f for f in demographics.facilities if f.get("primary")]
        assert len(primary_facility) == 1
        assert primary_facility[0]["name"] == "MAIN VA MEDICAL CENTER"

        assert len(demographics.eligibility) == 3
        priority = [
            e for e in demographics.eligibility if e["type"] == "PRIORITY GROUP"
        ]
        assert priority[0]["group"] == "1"
