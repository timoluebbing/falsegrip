"""Supabase repository implementation."""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Any

from falsegrip.config import AppConfig
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


class SupabaseRepository(FalseGripRepository):
    """Supabase-backed repository implementation."""

    def __init__(self, config: AppConfig) -> None:
        """Store Supabase-related runtime configuration and init client."""
        self._config = config
        self._client: Any = None
        self._user_id: Any = None

    def initialize(self) -> None:
        """Initialize backend resources and set context from session."""
        import streamlit as st
        from falsegrip.components.auth import get_supabase_client

        self._client = get_supabase_client()

        session = st.session_state.get("supabase_session")
        if session and session.user:
            self._user_id = session.user.id
            if hasattr(self._client.auth, "set_session"):
                try:
                    self._client.auth.set_session(
                        session.access_token, session.refresh_token
                    )
                except Exception:
                    pass

            # Ensure exercises are seeded once per session
            if "supabase_seeded_checked" not in st.session_state:
                try:
                    self._ensure_seeded_exercises()
                    st.session_state["supabase_seeded_checked"] = True
                except Exception:
                    pass

    def _ensure_seeded_exercises(self):
        """Seed predefined exercises if the user's list is completely empty."""
        res = self._client.table("exercise_definitions").select("id").limit(1).execute()
        if not res.data:
            from falsegrip.repositories.sqlite.seeds import predefined_exercises
            import uuid

            seeds = []
            for ex in predefined_exercises():
                ex_id = ex.id or str(uuid.uuid4())
                seeds.append(
                    {
                        "id": ex_id,
                        "user_id": self._user_id,
                        "name": ex.name,
                        "category": ex.category.value,
                        "exercise_type": ex.exercise_type.value,
                        "is_predefined": True,
                    }
                )
            if seeds:
                self._client.table("exercise_definitions").upsert(seeds).execute()

    def _check_client(self):
        if not self._client:
            raise RuntimeError("Supabase client not initialized")
        if not self._user_id:
            raise RuntimeError("User not authenticated")

    def _ensure_uuid(self, id_val: str) -> str:
        """Format an ID (e.g. from local tests) or just return it."""
        try:
            uuid.UUID(id_val)
            return id_val
        except ValueError:
            return str(uuid.uuid4())

    def list_workouts(self, limit: int, offset: int) -> list[Workout]:
        self._check_client()
        res = (
            self._client.table("workouts")
            .select("*")
            .eq("is_draft", False)
            .order("workout_date", desc=True)
            .limit(limit)
            .execute()
        )
        return [w for row in res.data if (w := self.get_workout(row["id"])) is not None]

    def get_workout(self, workout_id: str) -> Workout | None:
        self._check_client()
        w_res = (
            self._client.table("workouts").select("*").eq("id", workout_id).execute()
        )
        if not w_res.data:
            return None

        w_row = w_res.data[0]

        ex_res = (
            self._client.table("workout_exercises")
            .select("*")
            .eq("workout_id", workout_id)
            .order("order_index")
            .execute()
        )

        exercises = []
        for ex_row in ex_res.data:
            s_res = (
                self._client.table("workout_sets")
                .select("*")
                .eq("workout_exercise_id", ex_row["id"])
                .order("order_index")
                .execute()
            )

            sets = []
            for s in s_res.data:
                sets.append(
                    WorkoutSet(
                        id=s["id"],
                        order_index=s["order_index"],
                        weight_kg=s.get("weight_kg"),
                        reps=s.get("reps"),
                        duration_seconds=s.get("duration_seconds"),
                    )
                )

            exercises.append(
                WorkoutExerciseEntry(
                    id=ex_row["id"],
                    exercise_definition_id=ex_row["exercise_definition_id"],
                    exercise_name=ex_row["exercise_name"],
                    category=ExerciseCategory(ex_row["category"]),
                    exercise_type=ExerciseType(ex_row["exercise_type"]),
                    sets=sets,
                )
            )

        return Workout(
            id=w_row["id"],
            name=w_row["name"],
            workout_date=date.fromisoformat(w_row["workout_date"]),
            notes=w_row.get("notes", ""),
            is_draft=w_row.get("is_draft", False),
            exercises=exercises,
        )

    def create_workout(self, workout: Workout) -> str:
        self._check_client()
        workout_id = workout.id or str(uuid.uuid4())

        self._client.table("workouts").upsert(
            {
                "id": workout_id,
                "user_id": self._user_id,
                "name": workout.name,
                "workout_date": workout.workout_date.isoformat(),
                "notes": workout.notes,
                "is_draft": workout.is_draft,
            }
        ).execute()

        self._insert_sets(workout_id, workout.exercises)
        return workout_id

    def _insert_sets(self, workout_id: str, exercises: list[WorkoutExerciseEntry]):
        for order_idx, ex in enumerate(exercises):
            ex_id = ex.id or str(uuid.uuid4())
            self._client.table("workout_exercises").upsert(
                {
                    "id": ex_id,
                    "user_id": self._user_id,
                    "workout_id": workout_id,
                    "exercise_definition_id": ex.exercise_definition_id,
                    "exercise_name": ex.exercise_name,
                    "category": ex.category.value,
                    "exercise_type": ex.exercise_type.value,
                    "order_index": order_idx,
                }
            ).execute()

            sets_data = []
            for s_idx, s in enumerate(ex.sets):
                sets_data.append(
                    {
                        "id": s.id or str(uuid.uuid4()),
                        "user_id": self._user_id,
                        "workout_exercise_id": ex_id,
                        "order_index": s_idx,
                        "weight_kg": s.weight_kg,
                        "reps": s.reps,
                        "duration_seconds": s.duration_seconds,
                    }
                )

            if sets_data:
                self._client.table("workout_sets").upsert(sets_data).execute()

    def update_workout(self, workout: Workout) -> None:
        self._check_client()
        self._client.table("workouts").update(
            {
                "name": workout.name,
                "workout_date": workout.workout_date.isoformat(),
                "notes": workout.notes,
                "is_draft": workout.is_draft,
            }
        ).eq("id", workout.id).execute()

        self._client.table("workout_exercises").delete().eq(
            "workout_id", workout.id
        ).execute()
        self._insert_sets(workout.id, workout.exercises)

    def delete_workout(self, workout_id: str) -> None:
        self._check_client()
        self._client.table("workouts").delete().eq("id", workout_id).execute()

    def list_workout_plans(self) -> list[WorkoutPlan]:
        self._check_client()
        res = (
            self._client.table("workout_plans")
            .select("*")
            .order("order_index")
            .execute()
        )
        return [
            p for row in res.data if (p := self.get_workout_plan(row["id"])) is not None
        ]

    def get_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        self._check_client()
        p_res = (
            self._client.table("workout_plans").select("*").eq("id", plan_id).execute()
        )
        if not p_res.data:
            return None

        p_row = p_res.data[0]

        e_res = (
            self._client.table("workout_plan_exercises")
            .select("*")
            .eq("workout_plan_id", plan_id)
            .order("order_index")
            .execute()
        )

        exercises = []
        for ex_row in e_res.data:
            s_res = (
                self._client.table("workout_plan_sets")
                .select("*")
                .eq("workout_plan_exercise_id", ex_row["id"])
                .order("order_index")
                .execute()
            )

            sets = []
            for s in s_res.data:
                sets.append(
                    WorkoutSet(
                        id=s["id"],
                        order_index=s["order_index"],
                        weight_kg=s.get("weight_kg"),
                        reps=s.get("reps"),
                        duration_seconds=s.get("duration_seconds"),
                    )
                )

            exercises.append(
                WorkoutExerciseEntry(
                    id=ex_row["id"],
                    exercise_definition_id=ex_row["exercise_definition_id"],
                    exercise_name=ex_row["exercise_name"],
                    category=ExerciseCategory(ex_row["category"]),
                    exercise_type=ExerciseType(ex_row["exercise_type"]),
                    sets=sets,
                )
            )

        return WorkoutPlan(
            id=p_row["id"],
            name=p_row["name"],
            notes=p_row.get("notes", ""),
            exercises=exercises,
        )

    def create_workout_plan(self, workout_plan: WorkoutPlan) -> str:
        self._check_client()
        plan_id = workout_plan.id or str(uuid.uuid4())

        self._client.table("workout_plans").upsert(
            {
                "id": plan_id,
                "user_id": self._user_id,
                "name": workout_plan.name,
                "notes": workout_plan.notes,
            }
        ).execute()

        self._insert_plan_exercises(plan_id, workout_plan.exercises)
        return plan_id

    def _insert_plan_exercises(
        self, plan_id: str, exercises: list[WorkoutExerciseEntry]
    ):
        for i, ex in enumerate(exercises):
            ex_id = ex.id or str(uuid.uuid4())
            self._client.table("workout_plan_exercises").upsert(
                {
                    "id": ex_id,
                    "user_id": self._user_id,
                    "workout_plan_id": plan_id,
                    "exercise_definition_id": ex.exercise_definition_id,
                    "exercise_name": ex.exercise_name,
                    "category": ex.category.value,
                    "exercise_type": ex.exercise_type.value,
                    "order_index": i,
                }
            ).execute()

            sets_data = []
            for s_idx, s in enumerate(ex.sets):
                sets_data.append(
                    {
                        "id": s.id or str(uuid.uuid4()),
                        "user_id": self._user_id,
                        "workout_plan_exercise_id": ex_id,
                        "order_index": s_idx,
                        "weight_kg": s.weight_kg,
                        "reps": s.reps,
                        "duration_seconds": s.duration_seconds,
                    }
                )

            if sets_data:
                self._client.table("workout_plan_sets").upsert(sets_data).execute()

    def update_workout_plan(self, workout_plan: WorkoutPlan) -> None:
        self._check_client()
        self._client.table("workout_plans").update(
            {"name": workout_plan.name, "notes": workout_plan.notes}
        ).eq("id", workout_plan.id).execute()

        self._client.table("workout_plan_exercises").delete().eq(
            "workout_plan_id", workout_plan.id
        ).execute()
        self._insert_plan_exercises(workout_plan.id, workout_plan.exercises)

    def delete_workout_plan(self, plan_id: str) -> None:
        self._check_client()
        self._client.table("workout_plans").delete().eq("id", plan_id).execute()

    def list_exercise_definitions(self) -> list[ExerciseDefinition]:
        self._check_client()
        res = (
            self._client.table("exercise_definitions")
            .select("*")
            .order("name")
            .execute()
        )
        return [
            ExerciseDefinition(
                id=r["id"],
                name=r["name"],
                category=ExerciseCategory(r["category"]),
                exercise_type=ExerciseType(r["exercise_type"]),
                created_at=datetime.fromisoformat(r["created_at"])
                if r.get("created_at")
                else datetime.now(),
            )
            for r in res.data
        ]

    def create_exercise_definition(self, exercise: ExerciseDefinition) -> str:
        self._check_client()
        ex_id = exercise.id or str(uuid.uuid4())
        self._client.table("exercise_definitions").upsert(
            {
                "id": ex_id,
                "user_id": self._user_id,
                "name": exercise.name,
                "category": exercise.category.value,
                "exercise_type": exercise.exercise_type.value,
            }
        ).execute()
        return ex_id

    def delete_exercise_definition(self, exercise_id: str) -> None:
        self._check_client()
        self._client.table("exercise_definitions").delete().eq(
            "id", exercise_id
        ).execute()

    def get_last_logged_exercise_entry(
        self, exercise_definition_id: str
    ) -> WorkoutExerciseEntry | None:
        self._check_client()
        res = (
            self._client.table("workout_exercises")
            .select("workout_id, workouts!inner(workout_date)")
            .eq("exercise_definition_id", exercise_definition_id)
            .order("workout_date", foreign_table="workouts", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None

        workout = self.get_workout(res.data[0]["workout_id"])
        if not workout:
            return None

        for ex in workout.exercises:
            if ex.exercise_definition_id == exercise_definition_id:
                return ex
        return None

    def get_draft_workout(self) -> Workout | None:
        self._check_client()
        res = (
            self._client.table("workouts")
            .select("id")
            .eq("is_draft", True)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        return self.get_workout(res.data[0]["id"])

    def reorder_workout_plans(self, plan_ids: list[str]) -> None:
        self._check_client()
        for i, pid in enumerate(plan_ids):
            self._client.table("workout_plans").update({"order_index": i}).eq(
                "id", pid
            ).execute()

    def get_workout_frequency(self, period: Period) -> list[WorkoutFrequencyPoint]:
        from collections import defaultdict
        from datetime import date

        self._check_client()
        res = (
            self._client.table("workouts")
            .select("workout_date")
            .eq("is_draft", False)
            .execute()
        )

        counts = defaultdict(int)
        for row in res.data:
            d = date.fromisoformat(row["workout_date"])
            if period == "week":
                y, w, _ = d.isocalendar()
                label = f"{y}-W{w:02d}"
            else:
                label = d.strftime("%Y-%m")
            counts[label] += 1

        return [
            WorkoutFrequencyPoint(label, count)
            for label, count in sorted(counts.items())
        ]

    def get_volume_progression(self, exercise_definition_id: str) -> list[VolumePoint]:
        from collections import defaultdict

        self._check_client()
        res = (
            self._client.table("workout_exercises")
            .select(
                "exercise_type, workout_sets(weight_kg, reps, duration_seconds), workouts!inner(workout_date, is_draft)"
            )
            .eq("exercise_definition_id", exercise_definition_id)
            .eq("workouts.is_draft", False)
            .execute()
        )

        stats = defaultdict(
            lambda: {"volume": 0.0, "max_w": 0.0, "max_r": 0, "sum_r": 0, "count_r": 0}
        )

        for row in res.data:
            w_info = row.get("workouts", {})
            if isinstance(w_info, list):
                if not w_info:
                    continue
                w_info = w_info[0]

            w_date = w_info.get("workout_date")
            if not w_date:
                continue

            e_type = row.get("exercise_type")
            sets = row.get("workout_sets") or []
            s = stats[w_date]

            for st in sets:
                w = float(st.get("weight_kg") or 0.0)
                r = int(st.get("reps") or 0)
                d = float(st.get("duration_seconds") or 0.0)

                vol = 0.0
                if e_type == "Weight, Reps":
                    vol = w * r
                elif e_type == "Bodyweight, Reps":
                    vol = float(r)
                else:
                    vol = d

                s["volume"] += vol
                if w > s["max_w"]:
                    s["max_w"] = w
                if r > s["max_r"]:
                    s["max_r"] = r

                s["sum_r"] += r
                s["count_r"] += 1

        result = []
        for d in sorted(stats.keys()):
            s = stats[d]
            result.append(
                VolumePoint(
                    workout_date=d,
                    total_volume=s["volume"],
                    max_weight=s["max_w"] if s["max_w"] > 0 else None,
                    max_reps=int(s["max_r"]) if s["max_r"] > 0 else None,
                    mean_reps=(s["sum_r"] / s["count_r"]) if s["count_r"] > 0 else None,
                )
            )
        return result

    def get_exercise_distribution(self) -> list[DistributionPoint]:
        from collections import defaultdict

        self._check_client()
        res = (
            self._client.table("workout_exercises")
            .select("category, workouts!inner(is_draft)")
            .eq("workouts.is_draft", False)
            .execute()
        )

        counts = defaultdict(int)
        for row in res.data:
            counts[row["category"]] += 1

        result = [DistributionPoint(category=k, count=v) for k, v in counts.items()]
        return sorted(result, key=lambda x: x.count, reverse=True)

    def get_exercise_name_distribution(self) -> list[DistributionPoint]:
        from collections import defaultdict

        self._check_client()
        res = (
            self._client.table("workout_exercises")
            .select("exercise_name, workouts!inner(is_draft)")
            .eq("workouts.is_draft", False)
            .execute()
        )

        counts = defaultdict(int)
        for row in res.data:
            counts[row["exercise_name"]] += 1

        result = [DistributionPoint(category=k, count=v) for k, v in counts.items()]
        return sorted(result, key=lambda x: x.count, reverse=True)
