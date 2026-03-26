"""SQLite repository implementation for FalseGrip."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, UTC
from pathlib import Path
from uuid import uuid4

from falsegrip.models.enums import ExerciseCategory, ExerciseType
from falsegrip.models.workout import (
    ExerciseDefinition,
    Workout,
    WorkoutExerciseEntry,
    WorkoutPlan,
    WorkoutSet,
)
from falsegrip.repositories.base import (
    DistributionPoint,
    FalseGripRepository,
    Period,
    VolumePoint,
    WorkoutFrequencyPoint,
)
from falsegrip.repositories.sqlite.database import connect, initialize_schema
from falsegrip.repositories.sqlite.seeds import predefined_exercises


class SQLiteRepository(FalseGripRepository):
    """Concrete SQLite-backed data repository."""

    def __init__(self, sqlite_path: Path) -> None:
        """Store database path for future operations."""
        self._sqlite_path = sqlite_path

    def initialize(self) -> None:
        """Ensure schema and predefined exercise rows exist."""
        with connect(self._sqlite_path) as connection:
            initialize_schema(connection)
            self._seed_exercises(connection)

    def list_workouts(self, limit: int, offset: int) -> list[Workout]:
        """Return workouts sorted by date descending."""
        query = """
            SELECT id, name, workout_date, notes, created_at, updated_at
            FROM workouts
            ORDER BY workout_date DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query, (limit, offset)).fetchall()
            return [self._load_workout(connection, row["id"]) for row in rows]

    def get_workout(self, workout_id: str) -> Workout | None:
        """Return one workout by id if present."""
        with connect(self._sqlite_path) as connection:
            row = connection.execute(
                "SELECT id FROM workouts WHERE id = ?", (workout_id,)
            ).fetchone()
            if row is None:
                return None
            return self._load_workout(connection, workout_id)

    def create_workout(self, workout: Workout) -> str:
        """Persist a workout with nested exercises and sets."""
        workout_id = workout.id or str(uuid4())
        now = datetime.now(UTC).isoformat()

        with connect(self._sqlite_path) as connection:
            connection.execute(
                """
                INSERT INTO workouts (id, name, workout_date, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    workout_id,
                    workout.name,
                    workout.workout_date.isoformat(),
                    workout.notes,
                    now,
                    now,
                ),
            )
            self._insert_workout_entries(connection, workout_id, workout.exercises)
            connection.commit()

        return workout_id

    def update_workout(self, workout: Workout) -> None:
        """Update workout and replace nested entries."""
        now = datetime.now(UTC).isoformat()

        with connect(self._sqlite_path) as connection:
            connection.execute(
                """
                UPDATE workouts
                SET name = ?, workout_date = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    workout.name,
                    workout.workout_date.isoformat(),
                    workout.notes,
                    now,
                    workout.id,
                ),
            )
            connection.execute(
                "DELETE FROM workout_exercises WHERE workout_id = ?",
                (workout.id,),
            )
            self._insert_workout_entries(connection, workout.id, workout.exercises)
            connection.commit()

    def delete_workout(self, workout_id: str) -> None:
        """Delete a workout by id."""
        with connect(self._sqlite_path) as connection:
            connection.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
            connection.commit()

    def list_workout_plans(self) -> list[WorkoutPlan]:
        """Return all workout plans."""
        query = """
            SELECT id
            FROM workout_plans
            ORDER BY updated_at DESC, created_at DESC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query).fetchall()
            return [self._load_workout_plan(connection, row["id"]) for row in rows]

    def get_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        """Return one workout plan by id if present."""
        with connect(self._sqlite_path) as connection:
            row = connection.execute(
                "SELECT id FROM workout_plans WHERE id = ?", (plan_id,)
            ).fetchone()
            if row is None:
                return None
            return self._load_workout_plan(connection, plan_id)

    def create_workout_plan(self, workout_plan: WorkoutPlan) -> str:
        """Persist a workout plan with nested exercises and sets."""
        plan_id = workout_plan.id or str(uuid4())
        now = datetime.now(UTC).isoformat()

        with connect(self._sqlite_path) as connection:
            connection.execute(
                """
                INSERT INTO workout_plans (id, name, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (plan_id, workout_plan.name, workout_plan.notes, now, now),
            )
            self._insert_workout_plan_entries(
                connection, plan_id, workout_plan.exercises
            )
            connection.commit()

        return plan_id

    def update_workout_plan(self, workout_plan: WorkoutPlan) -> None:
        """Update workout plan and replace nested entries."""
        now = datetime.now(UTC).isoformat()

        with connect(self._sqlite_path) as connection:
            connection.execute(
                """
                UPDATE workout_plans
                SET name = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (workout_plan.name, workout_plan.notes, now, workout_plan.id),
            )
            connection.execute(
                "DELETE FROM workout_plan_exercises WHERE workout_plan_id = ?",
                (workout_plan.id,),
            )
            self._insert_workout_plan_entries(
                connection, workout_plan.id, workout_plan.exercises
            )
            connection.commit()

    def delete_workout_plan(self, plan_id: str) -> None:
        """Delete a workout plan by id."""
        with connect(self._sqlite_path) as connection:
            connection.execute("DELETE FROM workout_plans WHERE id = ?", (plan_id,))
            connection.commit()

    def list_exercise_definitions(self) -> list[ExerciseDefinition]:
        """Return all exercise definitions sorted by name."""
        query = """
            SELECT id, name, category, exercise_type, created_at
            FROM exercise_definitions
            ORDER BY name ASC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query).fetchall()

        return [
            ExerciseDefinition(
                id=row["id"],
                name=row["name"],
                category=ExerciseCategory(row["category"]),
                exercise_type=ExerciseType(row["exercise_type"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def create_exercise_definition(self, exercise: ExerciseDefinition) -> str:
        """Persist and return exercise definition id."""
        exercise_id = exercise.id or str(uuid4())
        with connect(self._sqlite_path) as connection:
            connection.execute(
                """
                INSERT INTO exercise_definitions (id, name, category, exercise_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    exercise_id,
                    exercise.name,
                    exercise.category.value,
                    exercise.exercise_type.value,
                    exercise.created_at.isoformat(),
                ),
            )
            connection.commit()
        return exercise_id

    def delete_exercise_definition(self, exercise_id: str) -> None:
        """Delete one exercise definition by id."""
        try:
            with connect(self._sqlite_path) as connection:
                cursor = connection.execute(
                    "DELETE FROM exercise_definitions WHERE id = ?",
                    (exercise_id,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Exercise definition does not exist.")
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Exercise is used in existing workouts or plans and cannot be deleted."
            ) from error

    def get_last_logged_exercise_entry(
        self, exercise_definition_id: str
    ) -> WorkoutExerciseEntry | None:
        """Return the latest logged workout exercise entry for one definition."""
        query = """
            SELECT we.id,
                   we.exercise_definition_id,
                   we.exercise_name,
                   we.category,
                   we.exercise_type
            FROM workout_exercises we
            INNER JOIN workouts w ON w.id = we.workout_id
            WHERE we.exercise_definition_id = ?
            ORDER BY w.workout_date DESC, w.created_at DESC, we.order_index DESC
            LIMIT 1
        """
        with connect(self._sqlite_path) as connection:
            entry_row = connection.execute(query, (exercise_definition_id,)).fetchone()
            if entry_row is None:
                return None

            set_rows = connection.execute(
                """
                SELECT id, order_index, weight_kg, reps, duration_seconds
                FROM workout_sets
                WHERE workout_exercise_id = ?
                ORDER BY order_index ASC
                """,
                (entry_row["id"],),
            ).fetchall()

        sets = [
            WorkoutSet(
                id=set_row["id"],
                order_index=set_row["order_index"],
                weight_kg=set_row["weight_kg"],
                reps=set_row["reps"],
                duration_seconds=set_row["duration_seconds"],
            )
            for set_row in set_rows
        ]

        return WorkoutExerciseEntry(
            id=entry_row["id"],
            exercise_definition_id=entry_row["exercise_definition_id"],
            exercise_name=entry_row["exercise_name"],
            category=ExerciseCategory(entry_row["category"]),
            exercise_type=ExerciseType(entry_row["exercise_type"]),
            sets=sets,
        )

    def get_workout_frequency(self, period: Period) -> list[WorkoutFrequencyPoint]:
        """Return grouped workout count by period."""
        if period == "month":
            grouping = "strftime('%Y-%m', workout_date)"
        else:
            grouping = "strftime('%Y-W%W', workout_date)"

        query = f"""
            SELECT {grouping} AS period_label, COUNT(*) AS count
            FROM workouts
            GROUP BY period_label
            ORDER BY period_label ASC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query).fetchall()

        return [
            WorkoutFrequencyPoint(period_label=row["period_label"], count=row["count"])
            for row in rows
        ]

    def get_volume_progression(self, exercise_definition_id: str) -> list[VolumePoint]:
        """Return volume progression points for one exercise definition."""
        query = """
            SELECT w.workout_date AS workout_date,
                   SUM(
                       CASE
                           WHEN we.exercise_type = 'Weight, Reps' THEN COALESCE(ws.weight_kg, 0) * COALESCE(ws.reps, 0)
                           WHEN we.exercise_type = 'Bodyweight, Reps' THEN COALESCE(ws.reps, 0)
                           ELSE COALESCE(ws.duration_seconds, 0)
                       END
                   ) AS total_volume
            FROM workouts w
            INNER JOIN workout_exercises we ON we.workout_id = w.id
            INNER JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            WHERE we.exercise_definition_id = ?
            GROUP BY w.workout_date
            ORDER BY w.workout_date ASC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query, (exercise_definition_id,)).fetchall()

        return [
            VolumePoint(
                workout_date=row["workout_date"],
                total_volume=float(row["total_volume"] or 0.0),
            )
            for row in rows
        ]

    def get_exercise_distribution(self) -> list[DistributionPoint]:
        """Return distribution points by category from logged workout exercises."""
        query = """
            SELECT category, COUNT(*) AS count
            FROM workout_exercises
            GROUP BY category
            ORDER BY category ASC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query).fetchall()

        return [
            DistributionPoint(category=row["category"], count=row["count"])
            for row in rows
        ]

    def get_exercise_name_distribution(self) -> list[DistributionPoint]:
        """Return distribution points by exercise name from logged workout exercises."""
        query = """
            SELECT exercise_name AS category, COUNT(*) AS count
            FROM workout_exercises
            GROUP BY exercise_name
            ORDER BY count DESC, exercise_name ASC
        """
        with connect(self._sqlite_path) as connection:
            rows = connection.execute(query).fetchall()

        return [
            DistributionPoint(category=row["category"], count=row["count"])
            for row in rows
        ]

    def _seed_exercises(self, connection: sqlite3.Connection) -> None:
        """Insert predefined exercise definitions when table is empty."""
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM exercise_definitions"
        ).fetchone()
        if row is None or row["count"] > 0:
            return

        for exercise in predefined_exercises():
            connection.execute(
                """
                INSERT INTO exercise_definitions (id, name, category, exercise_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    exercise.id,
                    exercise.name,
                    exercise.category.value,
                    exercise.exercise_type.value,
                    exercise.created_at.isoformat(),
                ),
            )
        connection.commit()

    def _load_workout(self, connection: sqlite3.Connection, workout_id: str) -> Workout:
        """Load one workout with nested entries and sets."""
        workout_row = connection.execute(
            """
            SELECT id, name, workout_date, notes, created_at, updated_at
            FROM workouts
            WHERE id = ?
            """,
            (workout_id,),
        ).fetchone()
        if workout_row is None:
            raise ValueError(f"Workout not found: {workout_id}")

        entries = self._load_workout_entries(connection, workout_id)
        return Workout(
            id=workout_row["id"],
            name=workout_row["name"],
            workout_date=date.fromisoformat(workout_row["workout_date"]),
            notes=workout_row["notes"],
            exercises=entries,
            created_at=datetime.fromisoformat(workout_row["created_at"]),
            updated_at=datetime.fromisoformat(workout_row["updated_at"]),
        )

    def _load_workout_entries(
        self, connection: sqlite3.Connection, workout_id: str
    ) -> list[WorkoutExerciseEntry]:
        """Load workout exercise entries with nested sets."""
        entry_rows = connection.execute(
            """
            SELECT id, exercise_definition_id, exercise_name, category, exercise_type, order_index
            FROM workout_exercises
            WHERE workout_id = ?
            ORDER BY order_index ASC
            """,
            (workout_id,),
        ).fetchall()

        entries: list[WorkoutExerciseEntry] = []
        for entry_row in entry_rows:
            set_rows = connection.execute(
                """
                SELECT id, order_index, weight_kg, reps, duration_seconds
                FROM workout_sets
                WHERE workout_exercise_id = ?
                ORDER BY order_index ASC
                """,
                (entry_row["id"],),
            ).fetchall()
            workout_sets = [
                WorkoutSet(
                    id=set_row["id"],
                    order_index=set_row["order_index"],
                    weight_kg=set_row["weight_kg"],
                    reps=set_row["reps"],
                    duration_seconds=set_row["duration_seconds"],
                )
                for set_row in set_rows
            ]
            entries.append(
                WorkoutExerciseEntry(
                    id=entry_row["id"],
                    exercise_definition_id=entry_row["exercise_definition_id"],
                    exercise_name=entry_row["exercise_name"],
                    category=ExerciseCategory(entry_row["category"]),
                    exercise_type=ExerciseType(entry_row["exercise_type"]),
                    sets=workout_sets,
                )
            )
        return entries

    def _insert_workout_entries(
        self,
        connection: sqlite3.Connection,
        workout_id: str,
        entries: list[WorkoutExerciseEntry],
    ) -> None:
        """Insert workout entries and sets for one workout."""
        for entry_index, entry in enumerate(entries):
            entry_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO workout_exercises (
                    id, workout_id, exercise_definition_id, exercise_name,
                    category, exercise_type, order_index
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    workout_id,
                    entry.exercise_definition_id,
                    entry.exercise_name,
                    entry.category.value,
                    entry.exercise_type.value,
                    entry_index,
                ),
            )

            for set_index, workout_set in enumerate(entry.sets):
                set_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO workout_sets (
                        id, workout_exercise_id, order_index, weight_kg, reps, duration_seconds
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        set_id,
                        entry_id,
                        set_index,
                        workout_set.weight_kg,
                        workout_set.reps,
                        workout_set.duration_seconds,
                    ),
                )

    def _load_workout_plan(
        self, connection: sqlite3.Connection, plan_id: str
    ) -> WorkoutPlan:
        """Load one workout plan with nested entries and sets."""
        row = connection.execute(
            """
            SELECT id, name, notes, created_at, updated_at
            FROM workout_plans
            WHERE id = ?
            """,
            (plan_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Workout plan not found: {plan_id}")

        entries = self._load_workout_plan_entries(connection, plan_id)
        return WorkoutPlan(
            id=row["id"],
            name=row["name"],
            notes=row["notes"],
            exercises=entries,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _load_workout_plan_entries(
        self, connection: sqlite3.Connection, plan_id: str
    ) -> list[WorkoutExerciseEntry]:
        """Load workout plan exercise entries with nested sets."""
        entry_rows = connection.execute(
            """
            SELECT id, exercise_definition_id, exercise_name, category, exercise_type, order_index
            FROM workout_plan_exercises
            WHERE workout_plan_id = ?
            ORDER BY order_index ASC
            """,
            (plan_id,),
        ).fetchall()

        entries: list[WorkoutExerciseEntry] = []
        for entry_row in entry_rows:
            set_rows = connection.execute(
                """
                SELECT id, order_index, weight_kg, reps, duration_seconds
                FROM workout_plan_sets
                WHERE workout_plan_exercise_id = ?
                ORDER BY order_index ASC
                """,
                (entry_row["id"],),
            ).fetchall()
            workout_sets = [
                WorkoutSet(
                    id=set_row["id"],
                    order_index=set_row["order_index"],
                    weight_kg=set_row["weight_kg"],
                    reps=set_row["reps"],
                    duration_seconds=set_row["duration_seconds"],
                )
                for set_row in set_rows
            ]
            entries.append(
                WorkoutExerciseEntry(
                    id=entry_row["id"],
                    exercise_definition_id=entry_row["exercise_definition_id"],
                    exercise_name=entry_row["exercise_name"],
                    category=ExerciseCategory(entry_row["category"]),
                    exercise_type=ExerciseType(entry_row["exercise_type"]),
                    sets=workout_sets,
                )
            )
        return entries

    def _insert_workout_plan_entries(
        self,
        connection: sqlite3.Connection,
        plan_id: str,
        entries: list[WorkoutExerciseEntry],
    ) -> None:
        """Insert workout plan entries and sets for one plan."""
        for entry_index, entry in enumerate(entries):
            entry_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO workout_plan_exercises (
                    id, workout_plan_id, exercise_definition_id, exercise_name,
                    category, exercise_type, order_index
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    plan_id,
                    entry.exercise_definition_id,
                    entry.exercise_name,
                    entry.category.value,
                    entry.exercise_type.value,
                    entry_index,
                ),
            )

            for set_index, workout_set in enumerate(entry.sets):
                set_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO workout_plan_sets (
                        id, workout_plan_exercise_id, order_index, weight_kg, reps, duration_seconds
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        set_id,
                        entry_id,
                        set_index,
                        workout_set.weight_kg,
                        workout_set.reps,
                        workout_set.duration_seconds,
                    ),
                )
