"""Validation helpers for domain models."""

from __future__ import annotations

from falsegrip.models.enums import ExerciseType
from falsegrip.models.workout import Workout, WorkoutExerciseEntry, WorkoutSet


class ValidationError(ValueError):
    """Raised when a model instance has invalid field values."""


def validate_set(exercise_type: ExerciseType, workout_set: WorkoutSet) -> None:
    """Validate one set against its exercise type."""
    if exercise_type == ExerciseType.WEIGHT_REPS:
        if workout_set.weight_kg is None or workout_set.reps is None:
            raise ValidationError("Weight/Reps sets require both weight_kg and reps.")
    elif exercise_type == ExerciseType.BODYWEIGHT_REPS:
        if workout_set.reps is None:
            raise ValidationError("Bodyweight/Reps sets require reps.")
    elif exercise_type == ExerciseType.BODYWEIGHT_TIME:
        if workout_set.duration_seconds is None:
            raise ValidationError("Bodyweight/Time sets require duration_seconds.")


def validate_exercise_entry(entry: WorkoutExerciseEntry) -> None:
    """Validate an exercise entry and all of its sets."""
    if not entry.exercise_name.strip():
        raise ValidationError("Exercise name is required.")

    if not entry.sets:
        raise ValidationError("Each exercise entry must have at least one set.")

    for workout_set in entry.sets:
        validate_set(entry.exercise_type, workout_set)


def validate_workout(workout: Workout) -> None:
    """Validate workout-level required fields and nested entries."""
    if workout.is_draft:
        return

    if not workout.name.strip():
        raise ValidationError("Workout name is required.")

    if not workout.exercises:
        raise ValidationError("Workout must contain at least one exercise entry.")

    for entry in workout.exercises:
        validate_exercise_entry(entry)
