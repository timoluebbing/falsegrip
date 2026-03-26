"""Seed data for SQLite backend."""

from __future__ import annotations

from datetime import datetime, UTC

from falsegrip.models.enums import ExerciseCategory, ExerciseType
from falsegrip.models.workout import ExerciseDefinition


def predefined_exercises() -> list[ExerciseDefinition]:
    """Return predefined exercises required for initial app use."""
    created_at = datetime.now(UTC)
    return [
        ExerciseDefinition(
            id="pikes",
            name="Pikes",
            category=ExerciseCategory.SHOULDERS,
            exercise_type=ExerciseType.BODYWEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="deadlift",
            name="Deadlift",
            category=ExerciseCategory.LEGS,
            exercise_type=ExerciseType.WEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="squat",
            name="Squat",
            category=ExerciseCategory.LEGS,
            exercise_type=ExerciseType.WEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="rdl",
            name="RDL",
            category=ExerciseCategory.LEGS,
            exercise_type=ExerciseType.WEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="pullups",
            name="Pull-ups",
            category=ExerciseCategory.BACK,
            exercise_type=ExerciseType.BODYWEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="weighted_pullups",
            name="Weighted Pull-ups",
            category=ExerciseCategory.BACK,
            exercise_type=ExerciseType.WEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="ring_rows",
            name="Ring Rows",
            category=ExerciseCategory.BACK,
            exercise_type=ExerciseType.BODYWEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="ring_dips",
            name="Ring Dips",
            category=ExerciseCategory.CHEST,
            exercise_type=ExerciseType.BODYWEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="ring_pushups",
            name="Ring Push-ups",
            category=ExerciseCategory.CHEST,
            exercise_type=ExerciseType.BODYWEIGHT_REPS,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="hollow_body_hold",
            name="Hollow Body Hold",
            category=ExerciseCategory.CORE,
            exercise_type=ExerciseType.BODYWEIGHT_TIME,
            created_at=created_at,
        ),
        ExerciseDefinition(
            id="lunges",
            name="Lunges",
            category=ExerciseCategory.LEGS,
            exercise_type=ExerciseType.WEIGHT_REPS,
            created_at=created_at,
        ),
    ]
