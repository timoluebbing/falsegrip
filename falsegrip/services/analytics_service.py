"""Analytics service utilities for graph pages."""

from __future__ import annotations

import pandas as pd

from falsegrip.repositories.base import FalseGripRepository


class AnalyticsService:
    """Converts repository analytics data into DataFrames for plotting."""

    def __init__(self, repository: FalseGripRepository) -> None:
        """Initialize service with a persistence repository."""
        self._repository = repository

    def workout_frequency_dataframe(self, period: str) -> pd.DataFrame:
        """Return frequency data as a DataFrame."""
        points = self._repository.get_workout_frequency(
            period="month" if period == "month" else "week"
        )
        return pd.DataFrame(
            [{"period": point.period_label, "count": point.count} for point in points]
        )

    def volume_progression_dataframe(self, exercise_definition_id: str) -> pd.DataFrame:
        """Return volume progression data as a DataFrame."""
        points = self._repository.get_volume_progression(
            exercise_definition_id=exercise_definition_id
        )
        return pd.DataFrame(
            [
                {"date": point.workout_date, "volume": point.total_volume}
                for point in points
            ]
        )

    def exercise_distribution_dataframe(self) -> pd.DataFrame:
        """Return exercise category distribution as a DataFrame."""
        points = self._repository.get_exercise_distribution()
        return pd.DataFrame(
            [{"category": point.category, "count": point.count} for point in points]
        )

    def exercise_name_distribution_dataframe(self) -> pd.DataFrame:
        """Return exercise-name distribution as a DataFrame."""
        points = self._repository.get_exercise_name_distribution()
        return pd.DataFrame(
            [{"exercise": point.category, "count": point.count} for point in points]
        )
