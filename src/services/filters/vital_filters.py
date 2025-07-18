"""Vital sign filtering utilities"""

from collections.abc import Callable

from ...models.patient.base import VitalType
from ...models.patient.clinical import VitalSign


class VitalFilter:
    """Filter vital signs by various criteria"""

    def __init__(
        self,
        vital_type: VitalType | None = None,
        custom_filter: Callable[[VitalSign], bool] | None = None,
    ):
        """Initialize vital filter

        Args:
            vital_type: Filter by vital type
            custom_filter: Custom filter function
        """
        self.vital_type = vital_type
        self.custom_filter = custom_filter

    def matches(self, vital: VitalSign) -> bool:
        """Check if vital sign matches filter criteria

        Args:
            vital: Vital sign to check

        Returns:
            True if matches all criteria
        """
        # Check vital type
        if self.vital_type and vital.vital_type != self.vital_type:
            return False

        # Apply custom filter
        return not (self.custom_filter and not self.custom_filter(vital))

    def filter(self, vitals: list[VitalSign]) -> list[VitalSign]:
        """Filter vital signs

        Args:
            vitals: List of vital signs

        Returns:
            Filtered vital signs
        """
        return [vital for vital in vitals if self.matches(vital)]


def filter_vitals_by_type(
    vitals: list[VitalSign], vital_type: VitalType
) -> list[VitalSign]:
    """Filter vitals by type

    Args:
        vitals: List of vital signs
        vital_type: Type to filter by

    Returns:
        Matching vital signs
    """
    filter = VitalFilter(vital_type=vital_type)
    return filter.filter(vitals)


def get_latest_vital(
    vitals: list[VitalSign], vital_type: VitalType | None = None
) -> VitalSign | None:
    """Get the most recent vital sign

    Args:
        vitals: List of vital signs
        vital_type: Optional type to filter by

    Returns:
        Most recent vital sign or None
    """
    # Filter by type if specified
    if vital_type:
        vitals = filter_vitals_by_type(vitals, vital_type)

    if not vitals:
        return None

    # Sort by datetime (most recent first)
    sorted_vitals = sorted(
        [v for v in vitals if v.observed], key=lambda v: v.observed, reverse=True
    )

    return sorted_vitals[0] if sorted_vitals else None
