"""Consult filtering utilities"""

from collections.abc import Callable

from ...models.patient.base import ConsultStatus, Urgency
from ...models.patient.clinical import Consult


class ConsultFilter:
    """Filter consults by various criteria"""

    def __init__(
        self,
        status: ConsultStatus | None = None,
        urgency: Urgency | None = None,
        service: str | None = None,
        custom_filter: Callable[[Consult], bool] | None = None,
    ):
        """Initialize consult filter

        Args:
            status: Filter by status
            urgency: Filter by urgency
            service: Filter by service (case-insensitive partial match)
            custom_filter: Custom filter function
        """
        self.status = status
        self.urgency = urgency
        self.service = service.lower() if service else None
        self.custom_filter = custom_filter

    def matches(self, consult: Consult) -> bool:
        """Check if consult matches filter criteria

        Args:
            consult: Consult to check

        Returns:
            True if matches all criteria
        """
        # Check status
        if self.status and consult.status != self.status:
            return False

        # Check urgency
        if self.urgency and consult.urgency != self.urgency:
            return False

        # Check service
        if self.service and self.service not in consult.service.lower():
            return False

        # Apply custom filter
        return not (self.custom_filter and not self.custom_filter(consult))

    def filter(self, consults: list[Consult]) -> list[Consult]:
        """Filter consults

        Args:
            consults: List of consults

        Returns:
            Filtered consults
        """
        return [consult for consult in consults if self.matches(consult)]


def filter_consults_by_status(
    consults: list[Consult], status: ConsultStatus
) -> list[Consult]:
    """Filter consults by status

    Args:
        consults: List of consults
        status: Status to filter by

    Returns:
        Matching consults
    """
    filter = ConsultFilter(status=status)
    return filter.filter(consults)


def filter_urgent_consults(consults: list[Consult]) -> list[Consult]:
    """Filter for urgent/stat consults

    Args:
        consults: List of consults

    Returns:
        Urgent consults
    """
    filter = ConsultFilter(urgency=Urgency.STAT)
    return filter.filter(consults)
