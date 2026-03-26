"""Mutable draft models for UI state management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

from falsegrip.models.enums import ExerciseCategory, ExerciseType


@dataclass
class SetDraft:
    """A draft for a single set."""

    weight_kg: str = ""
    reps: str = ""
    duration_seconds: str = ""
    placeholder_weight: str = ""
    placeholder_reps: str = ""
    placeholder_duration: str = ""
    key_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ExerciseDraft:
    """A draft for a single exercise entry."""

    configured: bool = False
    name: str = ""
    category: ExerciseCategory = ExerciseCategory.OTHER
    exercise_type: ExerciseType = ExerciseType.WEIGHT_REPS
    definition_id: str = ""
    sets: list[SetDraft] = field(default_factory=lambda: [SetDraft()])
    key_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class WorkoutDraft:
    """A draft representing an in-progress workout or plan modification."""

    id: str = ""
    name: str = ""
    workout_date: date = field(default_factory=date.today)
    notes: str = ""
    exercises: list[ExerciseDraft] = field(default_factory=list)
    autosaved_id: str = ""
    key_id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def data_hash(self) -> str:
        """Return a deterministic hash of the workout content to detect changes."""
        dump_dict = {
            "name": self.name.strip(),
            "date": str(self.workout_date),
            "notes": self.notes.strip(),
            "exercises": [
                {
                    "configured": ex.configured,
                    "name": ex.name.strip(),
                    "category": ex.category.value,
                    "type": ex.exercise_type.value,
                    "definition_id": ex.definition_id,
                    "sets": [
                        {
                            "weight": s.weight_kg.strip(),
                            "reps": s.reps.strip(),
                            "duration": s.duration_seconds.strip(),
                        }
                        for s in ex.sets
                    ],
                }
                for ex in self.exercises
            ],
        }
        return json.dumps(dump_dict, sort_keys=True)

    def is_empty(self) -> bool:
        """Return True if no meaningful content is configured."""
        if self.name.strip() or self.notes.strip():
            return False
        for ex in self.exercises:
            if ex.configured:
                return False
        return True
