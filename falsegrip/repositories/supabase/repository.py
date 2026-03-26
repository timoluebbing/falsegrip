"""Supabase repository placeholder implementation."""

from __future__ import annotations

from falsegrip.config import AppConfig
from falsegrip.repositories.base import (
    DistributionPoint,
    FalseGripRepository,
    Period,
    VolumePoint,
    WorkoutFrequencyPoint,
)
from falsegrip.models.workout import ExerciseDefinition, Workout, WorkoutPlan


class SupabaseRepository(FalseGripRepository):
    """Supabase-backed repository skeleton for later implementation."""

    def __init__(self, config: AppConfig) -> None:
        """Store Supabase-related runtime configuration."""
        self._config = config

    def initialize(self) -> None:
        """Initialize backend resources."""

    def list_workouts(self, limit: int, offset: int) -> list[Workout]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_workout(self, workout_id: str) -> Workout | None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def create_workout(self, workout: Workout) -> str:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def update_workout(self, workout: Workout) -> None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def delete_workout(self, workout_id: str) -> None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def list_workout_plans(self) -> list[WorkoutPlan]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def create_workout_plan(self, workout_plan: WorkoutPlan) -> str:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def update_workout_plan(self, workout_plan: WorkoutPlan) -> None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def delete_workout_plan(self, plan_id: str) -> None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def list_exercise_definitions(self) -> list[ExerciseDefinition]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def create_exercise_definition(self, exercise: ExerciseDefinition) -> str:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def delete_exercise_definition(self, exercise_id: str) -> None:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_workout_frequency(self, period: Period) -> list[WorkoutFrequencyPoint]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_volume_progression(self, exercise_definition_id: str) -> list[VolumePoint]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_exercise_distribution(self) -> list[DistributionPoint]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )

    def get_exercise_name_distribution(self) -> list[DistributionPoint]:
        raise NotImplementedError(
            "Supabase repository is planned for a following step."
        )
