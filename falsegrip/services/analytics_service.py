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

    def multi_volume_progression_dataframe(
        self, selections: list[tuple[str, str]]
    ) -> pd.DataFrame:
        """Return combined volume progression for multiple exercises."""
        rows: list[dict[str, object]] = []
        for exercise_id, exercise_name in selections:
            points = self._repository.get_volume_progression(
                exercise_definition_id=exercise_id
            )
            rows.extend(
                {
                    "date": point.workout_date,
                    "volume": point.total_volume,
                    "max_weight": point.max_weight,
                    "max_reps": point.max_reps,
                    "mean_reps": point.mean_reps,
                    "exercise": exercise_name,
                }
                for point in points
            )
        dataframe = pd.DataFrame(rows)
        if dataframe.empty:
            return dataframe

        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
        dataframe["volume"] = pd.to_numeric(dataframe["volume"], errors="coerce")
        dataframe["max_weight"] = pd.to_numeric(
            dataframe["max_weight"], errors="coerce"
        )
        dataframe["max_reps"] = pd.to_numeric(dataframe["max_reps"], errors="coerce")
        dataframe["mean_reps"] = pd.to_numeric(dataframe["mean_reps"], errors="coerce")
        # Ensure we only drop if the key field we are visualizing is NaN.
        # But we visualize volume by default, let's just drop on date and keep NaN for others if they don't apply.
        dataframe = dataframe.dropna(subset=["date"])
        return dataframe.sort_values(["exercise", "date"]).reset_index(drop=True)

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
