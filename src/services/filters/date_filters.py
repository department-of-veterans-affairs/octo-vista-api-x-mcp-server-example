"""Date range filtering utilities"""

from datetime import datetime
from typing import Any, TypeVar

from ...models.patient.collection import (
    PatientDataCollection,
)

T = TypeVar("T", bound=Any)


class DateRangeFilter:
    """Filter items by date range"""

    def __init__(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ):
        """Initialize date range filter

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        """
        self.start_date = start_date
        self.end_date = end_date

    def filter(self, items: list[T]) -> list[T]:
        """Filter items by date range

        Args:
            items: List of items with datetime field

        Returns:
            Filtered items within date range
        """
        filtered = []
        for item in items:
            # Get the datetime attribute - try different names
            dt = None
            if hasattr(item, "datetime"):
                dt = item.datetime
            elif hasattr(item, "observed"):
                dt = item.observed
            elif hasattr(item, "date_time"):
                dt = item.date_time

            if dt is None:
                continue

            if self.start_date and dt < self.start_date:
                continue

            if self.end_date and dt > self.end_date:
                continue

            filtered.append(item)

        return filtered

    def filter_collection(
        self, collection: PatientDataCollection
    ) -> PatientDataCollection:
        """Filter entire patient data collection by date range

        Args:
            collection: Patient data collection

        Returns:
            New collection with filtered data
        """
        return PatientDataCollection(
            demographics=collection.demographics,
            vital_signs=self.filter(collection.vital_signs),
            lab_results=self.filter(collection.lab_results),
            consults=self.filter(collection.consults),
            source_station=collection.source_station,
            source_dfn=collection.source_dfn,
            total_items=collection.total_items,
            cache_version=collection.cache_version,
            retrieved_at=collection.retrieved_at,
        )


def filter_by_date_range(
    items: list[T],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[T]:
    """Convenience function to filter items by date range

    Args:
        items: List of items with datetime field
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)

    Returns:
        Filtered items within date range
    """
    filter = DateRangeFilter(start_date, end_date)
    return filter.filter(items)
