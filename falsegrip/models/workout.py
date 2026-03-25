"""Core domain models for workouts and plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from falsegrip.models.enums import ExerciseCategory, ExerciseType


@dataclass(slots=True)
class ExerciseDefinition:
    """Stored exercise metadata."""

    id: str
    name: str
    category: ExerciseCategory
    exercise_type: ExerciseType
    created_at: datetime


@dataclass(slots=True)
class WorkoutSet:
    """A single logged set for an exercise entry."""

    id: str
    order_index: int
    weight_kg: float | None = None
    reps: int | None = None
    duration_seconds: int | None = None


@dataclass(slots=True)
class WorkoutExerciseEntry:
    """An exercise and its sets inside a workout."""

    id: str
    exercise_definition_id: str
    exercise_name: str
    category: ExerciseCategory
    exercise_type: ExerciseType
    sets: list[WorkoutSet] = field(default_factory=list)


@dataclass(slots=True)
class Workout:
    """A workout log entry with exercises and sets."""

    id: str
    name: str
    workout_date: date
    notes: str
    exercises: list[WorkoutExerciseEntry] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutPlan:
    """A reusable workout template."""

    id: str
    name: str
    notes: str
    exercises: list[WorkoutExerciseEntry] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
