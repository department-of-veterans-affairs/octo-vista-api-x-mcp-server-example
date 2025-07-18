"""Lab result filtering utilities"""

from collections.abc import Callable

from ...models.patient.clinical import (
    InterpretationCode,
    LabResult,
)


class LabFilter:
    """Filter lab results by various criteria"""

    def __init__(
        self,
        test_name: str | None = None,
        abnormal_only: bool = False,
        critical_only: bool = False,
        custom_filter: Callable[[LabResult], bool] | None = None,
    ):
        """Initialize lab filter

        Args:
            test_name: Filter by test name (case-insensitive partial match)
            abnormal_only: Only include abnormal results
            critical_only: Only include critical results
            custom_filter: Custom filter function
        """
        self.test_name = test_name.lower() if test_name else None
        self.abnormal_only = abnormal_only
        self.critical_only = critical_only
        self.custom_filter = custom_filter

    def matches(self, lab: LabResult) -> bool:
        """Check if lab result matches filter criteria

        Args:
            lab: Lab result to check

        Returns:
            True if matches all criteria
        """
        # Check test name
        if self.test_name and self.test_name not in lab.type_name.lower():
            return False

        # Check abnormal status
        if self.abnormal_only and not lab.is_abnormal:
            return False

        # Check critical status
        if self.critical_only and lab.interpretation_code not in [
            InterpretationCode.CRITICAL_HIGH,
            InterpretationCode.CRITICAL_LOW,
        ]:
            return False

        # Apply custom filter
        return not (self.custom_filter and not self.custom_filter(lab))

    def filter(self, labs: list[LabResult]) -> list[LabResult]:
        """Filter lab results

        Args:
            labs: List of lab results

        Returns:
            Filtered lab results
        """
        return [lab for lab in labs if self.matches(lab)]


def filter_abnormal_labs(
    labs: list[LabResult], critical_only: bool = False
) -> list[LabResult]:
    """Filter for abnormal lab results

    Args:
        labs: List of lab results
        critical_only: Only include critical results

    Returns:
        Abnormal lab results
    """
    filter = LabFilter(abnormal_only=True, critical_only=critical_only)
    return filter.filter(labs)


def filter_labs_by_type(labs: list[LabResult], test_name: str) -> list[LabResult]:
    """Filter labs by test type/name

    Args:
        labs: List of lab results
        test_name: Test name to filter by (partial match)

    Returns:
        Matching lab results
    """
    filter = LabFilter(test_name=test_name)
    return filter.filter(labs)
