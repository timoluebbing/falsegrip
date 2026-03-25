"""Domain enums for FalseGrip models."""

from __future__ import annotations

from enum import Enum


class ExerciseCategory(str, Enum):
    """Supported exercise categories."""

    UPPER_BODY = "Upper Body"
    LOWER_BODY = "Lower Body"
    CORE = "Core"
    CARDIO = "Cardio"
    OTHER = "Other"


class ExerciseType(str, Enum):
    """Supported exercise metric types."""

    WEIGHT_REPS = "Weight, Reps"
    BODYWEIGHT_REPS = "Bodyweight, Reps"
    BODYWEIGHT_TIME = "Bodyweight, Time"
