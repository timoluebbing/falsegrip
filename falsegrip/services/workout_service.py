"""Workout service orchestration layer."""

from __future__ import annotations

import csv
import io
from dataclasses import replace
from datetime import date, datetime, UTC
from uuid import uuid4

from falsegrip.models import validate_workout
from falsegrip.models.enums import ExerciseCategory, ExerciseType
from falsegrip.models.workout import (
    ExerciseDefinition,
    Workout,
    WorkoutExerciseEntry,
    WorkoutPlan,
    WorkoutSet,
)
from falsegrip.repositories.base import FalseGripRepository


class WorkoutService:
    """Encapsulates workout and workout-plan business operations."""

    def __init__(self, repository: FalseGripRepository) -> None:
        """Initialize service with a persistence repository."""
        self._repository = repository

    def list_workouts(self, limit: int, offset: int = 0) -> list[Workout]:
        """List workouts with pagination controls."""
        return self._repository.list_workouts(limit=limit, offset=offset)

    def get_workout(self, workout_id: str) -> Workout | None:
        """Return one workout by id when available."""
        return self._repository.get_workout(workout_id)

    def save_workout(self, workout: Workout) -> str:
        """Create or update a workout after validation."""
        validate_workout(workout)
        now = datetime.now(UTC)

        if not workout.id:
            created = replace(workout, id=str(uuid4()), created_at=now, updated_at=now)
            return self._repository.create_workout(created)

        updated = replace(workout, updated_at=now)
        self._repository.update_workout(updated)
        return updated.id

    def list_exercise_definitions(self) -> list[ExerciseDefinition]:
        """Return all known exercise definitions."""
        return self._repository.list_exercise_definitions()

    def create_exercise_definition(
        self,
        name: str,
        category: ExerciseCategory,
        exercise_type: ExerciseType,
    ) -> ExerciseDefinition:
        """Create one exercise definition when missing and return it."""
        return self.ensure_exercise_definition(
            name=name,
            category=category,
            exercise_type=exercise_type,
        )

    def delete_exercise_definition(self, exercise_id: str) -> None:
        """Delete one exercise definition by id."""
        self._repository.delete_exercise_definition(exercise_id)

    def get_last_logged_exercise_entry(
        self, exercise_definition_id: str
    ) -> WorkoutExerciseEntry | None:
        """Return the latest logged exercise entry for one exercise definition."""
        return self._repository.get_last_logged_exercise_entry(exercise_definition_id)

    def ensure_exercise_definition(
        self,
        name: str,
        category: ExerciseCategory,
        exercise_type: ExerciseType,
    ) -> ExerciseDefinition:
        """Return an existing exercise definition by name or create a new one."""
        normalized_name = name.strip().lower()
        for definition in self._repository.list_exercise_definitions():
            if definition.name.strip().lower() == normalized_name:
                return definition

        definition = ExerciseDefinition(
            id=str(uuid4()),
            name=name.strip(),
            category=category,
            exercise_type=exercise_type,
            created_at=datetime.now(UTC),
        )
        self._repository.create_exercise_definition(definition)
        return definition

    def delete_workout(self, workout_id: str) -> None:
        """Delete a workout by id."""
        self._repository.delete_workout(workout_id)

    def list_workout_plans(self) -> list[WorkoutPlan]:
        """List available workout plans."""
        return self._repository.list_workout_plans()

    def get_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        """Return one workout plan by id when available."""
        return self._repository.get_workout_plan(plan_id)

    def save_workout_plan(self, workout_plan: WorkoutPlan) -> str:
        """Create or update a workout plan."""
        now = datetime.now(UTC)
        if not workout_plan.id:
            created = replace(
                workout_plan, id=str(uuid4()), created_at=now, updated_at=now
            )
            return self._repository.create_workout_plan(created)

        updated = replace(workout_plan, updated_at=now)
        self._repository.update_workout_plan(updated)
        return updated.id

    def delete_workout_plan(self, plan_id: str) -> None:
        """Delete a workout plan."""
        self._repository.delete_workout_plan(plan_id)

    def save_workout_as_plan(self, workout: Workout) -> str:
        """Convert a workout instance into a workout plan."""
        plan_entries: list[WorkoutExerciseEntry] = []
        for entry in workout.exercises:
            plan_sets = [
                WorkoutSet(
                    id="",
                    order_index=workout_set.order_index,
                    weight_kg=None,
                    reps=None,
                    duration_seconds=None,
                )
                for workout_set in entry.sets
            ]
            plan_entries.append(
                WorkoutExerciseEntry(
                    id="",
                    exercise_definition_id=entry.exercise_definition_id,
                    exercise_name=entry.exercise_name,
                    category=entry.category,
                    exercise_type=entry.exercise_type,
                    sets=plan_sets,
                )
            )

        plan = WorkoutPlan(
            id="",
            name=workout.name,
            notes=workout.notes,
            exercises=plan_entries,
        )
        return self.save_workout_plan(plan)

    def start_workout_from_plan(
        self, plan: WorkoutPlan, workout_date: date | None = None
    ) -> Workout:
        """Create a workout draft from a workout plan template."""
        cloned_entries: list[WorkoutExerciseEntry] = []
        for entry in plan.exercises:
            cloned_sets = [
                WorkoutSet(
                    id="",
                    order_index=workout_set.order_index,
                    weight_kg=None,
                    reps=None,
                    duration_seconds=None,
                )
                for workout_set in entry.sets
            ]
            cloned_entries.append(
                WorkoutExerciseEntry(
                    id="",
                    exercise_definition_id=entry.exercise_definition_id,
                    exercise_name=entry.exercise_name,
                    category=entry.category,
                    exercise_type=entry.exercise_type,
                    sets=cloned_sets,
                )
            )

        return Workout(
            id="",
            name=plan.name,
            workout_date=workout_date or date.today(),
            notes=plan.notes,
            exercises=cloned_entries,
        )

    def export_workouts_csv(self, limit: int = 10000) -> str:
        """Export workouts into CSV text for download."""
        workouts = self._repository.list_workouts(limit=limit, offset=0)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "workout_id",
                "workout_name",
                "date",
                "notes",
                "exercise",
                "set_index",
                "weight_kg",
                "reps",
                "duration_seconds",
            ]
        )

        for workout in workouts:
            for entry in workout.exercises:
                for set_index, workout_set in enumerate(entry.sets, start=1):
                    writer.writerow(
                        [
                            workout.id,
                            workout.name,
                            workout.workout_date.isoformat(),
                            workout.notes,
                            entry.exercise_name,
                            set_index,
                            workout_set.weight_kg,
                            workout_set.reps,
                            workout_set.duration_seconds,
                        ]
                    )

        return buffer.getvalue()
