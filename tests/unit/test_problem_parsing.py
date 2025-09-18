"""Unit tests for Problem parsing and models."""

from datetime import UTC, datetime

from src.models.patient.problem import (
    Problem,
    ProblemAcuity,
    ProblemComment,
    ProblemStatus,
    ProblemSummary,
)
from src.models.responses.tool_responses import ProblemsResponse, ProblemsResponseData
from src.services.parsers.patient.patient_parser import PatientDataParser


class TestProblemModel:
    """Test Problem model validation and properties."""

    def test_problem_creation(self):
        """Test creating a Problem from VistA data."""
        problem = Problem(
            uid="urn:va:problem:84F0:237:2001",
            localId="2001",
            problemText="Former heavy tobacco smoker (SCT 428081000124100)",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            icdCode="urn:10d:Z87.891",
            icdName="Personal history of nicotine dependence",
            entered=datetime(2025, 7, 14, tzinfo=UTC),
            updated=datetime(2025, 7, 14, tzinfo=UTC),
            facilityCode="500",
            facilityName="CAMP MASTER",
        )

        assert problem.uid == "urn:va:problem:84F0:237:2001"
        assert problem.local_id == "2001"
        assert (
            problem.problem_text == "Former heavy tobacco smoker (SCT 428081000124100)"
        )
        assert problem.status_name == ProblemStatus.ACTIVE
        assert problem.icd_code == "urn:10d:Z87.891"
        assert problem.facility_code == "500"
        assert problem.facility_name == "CAMP MASTER"

    def test_problem_properties(self):
        """Test Problem computed properties."""
        problem1 = Problem(
            uid="test1",
            localId="1",
            problemText="Test Problem 1",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )
        problem2 = Problem(
            uid="test2",
            localId="2",
            problemText="Test Problem 2",
            statusCode="urn:sct:73425007",
            statusName="INACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        # Test active problem properties
        assert problem1.is_active is True
        assert problem1.is_inactive is False

        # Test inactive problem properties
        assert problem2.is_active is False
        assert problem2.is_inactive is True

    def test_problem_acuity_properties(self):
        """Test Problem acuity properties."""
        chronic_problem = Problem(
            uid="test",
            localId="1",
            problemText="Chronic Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            acuityName="chronic",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test Hospital",
        )

        acute_problem = Problem(
            uid="test2",
            localId="2",
            problemText="Acute Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            acuityName="acute",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test Hospital",
        )

        # Test chronic problem properties
        assert chronic_problem.is_chronic is True
        assert chronic_problem.is_acute is False
        assert chronic_problem.acuity_name == ProblemAcuity.CHRONIC

        # Test acute problem properties
        assert acute_problem.is_chronic is False
        assert acute_problem.is_acute is True
        assert acute_problem.acuity_name == ProblemAcuity.ACUTE

    def test_problem_has_icd_code(self):
        """Test has_icd_code property."""
        problem_with_icd = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            icdCode="urn:icd:401.9",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        problem_without_icd = Problem(
            uid="test2",
            localId="2",
            problemText="Test Problem 2",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert problem_with_icd.has_icd_code is True
        assert problem_without_icd.has_icd_code is False

    def test_problem_service_connected(self):
        """Test service connected property."""
        service_connected_problem = Problem(
            uid="test",
            localId="1",
            problemText="Service Connected Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            serviceConnected=True,
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        non_service_connected_problem = Problem(
            uid="test2",
            localId="2",
            problemText="Non-Service Connected Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            serviceConnected=False,
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert service_connected_problem.is_service_connected is True
        assert non_service_connected_problem.is_service_connected is False

    def test_problem_datetime_parsing(self):
        """Test datetime parsing from VistA format."""
        problem = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered="20230101",
            updated="20230101",
            onset="20220101",
            facilityCode="500",
            facilityName="Test",
        )

        assert isinstance(problem.entered, datetime)
        assert isinstance(problem.updated, datetime)
        assert isinstance(problem.onset, datetime)
        assert problem.onset.year == 2022
        assert problem.entered.year == 2023

    def test_problem_field_validation(self):
        """Test Problem field validation."""
        problem = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
            removed=False,
            unverified=False,
        )

        assert problem.removed is False
        assert problem.unverified is False

    def test_problem_with_comments(self):
        """Test Problem with comments."""
        problem = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
            comments=[
                ProblemComment(
                    comment="Test comment",
                    entered=datetime.now(UTC),
                    enteredByCode="123",
                    enteredByName="Test User",
                )
            ],
        )

        assert len(problem.comments) == 1
        assert problem.comments[0].comment == "Test comment"


class TestProblemsResponseModels:
    """Test Problem response models."""

    def test_problems_response_data_creation(self):
        """Test creating Problems response data."""
        problem = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        summary = ProblemSummary(total_problems=1, active_count=1, inactive_count=0)

        data = ProblemsResponseData(
            problems=[problem],
            summary=summary,
            by_status={"ACTIVE": 1, "INACTIVE": 0},
            by_acuity={"CHRONIC": 0, "ACUTE": 0},
            active_problems=["test"],
            inactive_problems=[],
            service_connected_problems=[],
        )

        assert len(data.problems) == 1
        assert data.summary.total_problems == 1
        assert data.by_status["ACTIVE"] == 1

    def test_problems_response_creation(self):
        """Test creating Problems response."""
        problem = Problem(
            uid="test",
            localId="1",
            problemText="Test Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        summary = ProblemSummary(total_problems=1, active_count=1, inactive_count=0)

        data = ProblemsResponseData(
            problems=[problem],
            summary=summary,
            by_status={"ACTIVE": 1, "INACTIVE": 0},
            by_acuity={"CHRONIC": 0, "ACUTE": 0},
            active_problems=["test"],
            inactive_problems=[],
            service_connected_problems=[],
        )

        response = ProblemsResponse(success=True, data=data)

        assert response.success is True
        assert response.data is not None
        assert len(response.data.problems) == 1


class TestProblemParsing:
    """Test Problem parsing from VistA data."""

    def test_parse_problems_with_invalid_data(self):
        """Test parsing Problems with invalid data."""
        parser = PatientDataParser(station="500", icn="123456")

        raw_problems = [
            {
                "uid": "urn:va:problem:84F0:237:268",
                "localId": "268",
                "problemText": "Problem with comments",
                "statusCode": "urn:sct:73425007",
                "statusName": "INACTIVE",
                "entered": "20040330",
                "updated": "20040330",
                "facilityCode": "500",
                "facilityName": "CAMP MASTER",
                "comments": [
                    {
                        "comment": "Anterior",
                        "entered": "20000523",
                        "enteredByCode": "urn:va:user:84F0:20001",
                        "enteredByName": "VEHU,ONE",
                    }
                ],
            }
        ]

        problems = parser._parse_problems(raw_problems)

        # Now returns dict keyed by UID
        assert isinstance(problems, dict)
        assert len(problems) == 1
        assert "urn:va:problem:84F0:237:268" in problems
        prob = list(problems.values())[0]
        assert prob.uid == "urn:va:problem:84F0:237:268"
        assert len(prob.comments) == 1

    def test_parse_problems_with_comments(self):
        """Test parsing Problems with comments."""
        parser = PatientDataParser(station="500", icn="123456")

        raw_problems = [
            {
                "uid": "urn:va:problem:84F0:237:268",
                "localId": "268",
                "problemText": "Problem with comments",
                "statusCode": "urn:sct:73425007",
                "statusName": "INACTIVE",
                "entered": "20040330",
                "updated": "20040330",
                "facilityCode": "500",
                "facilityName": "CAMP MASTER",
                "comments": [
                    {
                        "comment": "Anterior",
                        "entered": "20000523",
                        "enteredByCode": "urn:va:user:84F0:20001",
                        "enteredByName": "VEHU,ONE",
                    }
                ],
            }
        ]

        problems = parser._parse_problems(raw_problems)

        assert isinstance(problems, dict)
        assert len(problems) == 1
        assert "urn:va:problem:84F0:237:268" in problems
        prob = list(problems.values())[0]
        assert prob.uid == "urn:va:problem:84F0:237:268"
        assert len(prob.comments) == 1
        assert prob.comments[0].comment == "Anterior"


class TestProblemStatusClassification:
    """Test Problem status classification and filtering."""

    def test_active_problem_identification(self):
        """Test identifying active Problems."""
        active_problem = Problem(
            uid="test",
            localId="1",
            problemText="Active Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert active_problem.is_active is True
        assert active_problem.is_inactive is False

    def test_inactive_problem_identification(self):
        """Test identifying inactive Problems."""
        inactive_problem = Problem(
            uid="test",
            localId="1",
            problemText="Inactive Problem",
            statusCode="urn:sct:73425007",
            statusName="INACTIVE",
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert inactive_problem.is_active is False
        assert inactive_problem.is_inactive is True

    def test_service_connected_problem_identification(self):
        """Test identifying service connected Problems."""
        service_connected_problem = Problem(
            uid="test",
            localId="1",
            problemText="Service Connected Problem",
            statusCode="urn:sct:55561003",
            statusName="ACTIVE",
            serviceConnected=True,
            entered=datetime.now(UTC),
            updated=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert service_connected_problem.is_service_connected is True
