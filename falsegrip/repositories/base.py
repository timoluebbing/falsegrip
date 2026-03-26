"""Repository interfaces for FalseGrip persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from falsegrip.models.workout import (
    ExerciseDefinition,
    Workout,
    WorkoutExerciseEntry,
    WorkoutPlan,
)

Period = Literal["week", "month"]


@dataclass(frozen=True)
class WorkoutFrequencyPoint:
    """Aggregate point for workout frequency graphs."""

    period_label: str
    count: int


@dataclass(frozen=True)
class VolumePoint:
    """Aggregate point for volume progression graphs."""

    workout_date: str
    total_volume: float
    max_weight: float | None = None
    max_reps: int | None = None
    mean_reps: float | None = None


@dataclass(frozen=True)
class DistributionPoint:
    """Aggregate point for exercise distribution graphs."""

    category: str
    count: int


class FalseGripRepository(ABC):
    """Unified persistence contract for all app data operations."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize storage schema and required seed data."""

    @abstractmethod
    def list_workouts(self, limit: int, offset: int) -> list[Workout]:
        """Return workouts sorted by date descending."""

    @abstractmethod
    def get_workout(self, workout_id: str) -> Workout | None:
        """Return one workout by id if present."""

    @abstractmethod
    def create_workout(self, workout: Workout) -> str:
        """Persist and return the workout id."""

    @abstractmethod
    def update_workout(self, workout: Workout) -> None:
        """Persist updates for an existing workout."""

    @abstractmethod
    def delete_workout(self, workout_id: str) -> None:
        """Delete a workout and related nested entities."""

    @abstractmethod
    def list_workout_plans(self) -> list[WorkoutPlan]:
        """Return all workout plans."""

    @abstractmethod
    def get_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        """Return one workout plan by id if present."""

    @abstractmethod
    def create_workout_plan(self, workout_plan: WorkoutPlan) -> str:
        """Persist and return the plan id."""

    @abstractmethod
    def update_workout_plan(self, workout_plan: WorkoutPlan) -> None:
        """Persist updates for an existing workout plan."""

    @abstractmethod
    def delete_workout_plan(self, plan_id: str) -> None:
        """Delete a workout plan and related nested entities."""

    @abstractmethod
    def list_exercise_definitions(self) -> list[ExerciseDefinition]:
        """Return all exercise definitions."""

    @abstractmethod
    def create_exercise_definition(self, exercise: ExerciseDefinition) -> str:
        """Persist and return the exercise definition id."""

    @abstractmethod
    def delete_exercise_definition(self, exercise_id: str) -> None:
        """Delete one exercise definition by id."""

    @abstractmethod
    def get_last_logged_exercise_entry(
        self, exercise_definition_id: str
    ) -> WorkoutExerciseEntry | None:
        """Return the most recent logged exercise entry for one exercise definition."""

    @abstractmethod
    def get_workout_frequency(self, period: Period) -> list[WorkoutFrequencyPoint]:
        """Return frequency data grouped by week or month."""

    @abstractmethod
    def get_volume_progression(self, exercise_definition_id: str) -> list[VolumePoint]:
        """Return total volume points by workout date for one exercise."""

    @abstractmethod
    def get_exercise_distribution(self) -> list[DistributionPoint]:
        """Return category distribution points across logged exercise entries."""

    @abstractmethod
    def get_exercise_name_distribution(self) -> list[DistributionPoint]:
        """Return distribution points across concrete exercise names."""
