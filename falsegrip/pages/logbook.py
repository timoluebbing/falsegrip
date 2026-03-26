"""Logbook page renderer."""

from __future__ import annotations

import json
import time
from datetime import date
from uuid import uuid4

import streamlit as st

from falsegrip.models import ValidationError
from falsegrip.models.enums import ExerciseCategory, ExerciseType
from falsegrip.models.workout import Workout, WorkoutExerciseEntry, WorkoutSet
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.workout_service import WorkoutService

PAGE_SIZE = 10


def _initialize_page_state() -> None:
    """Initialize page-level state keys."""
    st.session_state.setdefault("logbook_limit", PAGE_SIZE)
    st.session_state.setdefault("logbook_dialog_mode", None)
    st.session_state.setdefault("logbook_edit_id", "")
    st.session_state.setdefault("logbook_dialog_nonce", "")
    st.session_state.setdefault("logbook_template_workout", None)
    st.session_state.setdefault("logbook_autosave_workout_id", "")
    st.session_state.setdefault("logbook_autosave_last_hash", "")
    st.session_state.setdefault("logbook_autosave_last_ts", 0.0)
    st.session_state.setdefault("logbook_autosave_status", "")


def _exercise_summary(workout: Workout) -> str:
    """Return multiline exercise summary for a workout card."""
    return "\n".join(
        f"{len(entry.sets)}x {entry.exercise_name}" for entry in workout.exercises
    )


def _ensure_exercise_state(prefix: str, exercise_index: int) -> None:
    """Ensure session-state keys for one exercise section exist."""
    exercise_base = f"{prefix}_exercise_{exercise_index}"
    st.session_state.setdefault(f"{exercise_base}_configured", False)
    st.session_state.setdefault(f"{exercise_base}_name", "")
    st.session_state.setdefault(
        f"{exercise_base}_category", ExerciseCategory.OTHER.value
    )
    st.session_state.setdefault(f"{exercise_base}_type", ExerciseType.WEIGHT_REPS.value)
    st.session_state.setdefault(
        f"{exercise_base}_saved_category", ExerciseCategory.OTHER.value
    )
    st.session_state.setdefault(
        f"{exercise_base}_saved_type", ExerciseType.WEIGHT_REPS.value
    )
    st.session_state.setdefault(f"{exercise_base}_set_count", 1)
    st.session_state.setdefault(f"{exercise_base}_saved_name", "")
    st.session_state.setdefault(f"{exercise_base}_definition_id", "")


def _ensure_set_state(prefix: str, exercise_index: int, set_index: int) -> None:
    """Ensure session-state keys for one set row exist."""
    set_base = f"{prefix}_exercise_{exercise_index}_set_{set_index}"
    st.session_state.setdefault(f"{set_base}_weight", "")
    st.session_state.setdefault(f"{set_base}_reps", "")
    st.session_state.setdefault(f"{set_base}_duration", "")
    st.session_state.setdefault(f"{set_base}_placeholder_weight", "")
    st.session_state.setdefault(f"{set_base}_placeholder_reps", "")
    st.session_state.setdefault(f"{set_base}_placeholder_duration", "")


def _set_exercise_defaults(prefix: str, exercise_index: int) -> None:
    """Hard-reset one exercise section to clean defaults."""
    exercise_base = f"{prefix}_exercise_{exercise_index}"
    st.session_state[f"{exercise_base}_configured"] = False
    st.session_state[f"{exercise_base}_name"] = ""
    st.session_state[f"{exercise_base}_category"] = ExerciseCategory.OTHER.value
    st.session_state[f"{exercise_base}_type"] = ExerciseType.WEIGHT_REPS.value
    st.session_state[f"{exercise_base}_saved_category"] = ExerciseCategory.OTHER.value
    st.session_state[f"{exercise_base}_saved_type"] = ExerciseType.WEIGHT_REPS.value
    st.session_state[f"{exercise_base}_set_count"] = 1
    st.session_state[f"{exercise_base}_saved_name"] = ""
    st.session_state[f"{exercise_base}_definition_id"] = ""
    st.session_state[f"{exercise_base}_set_0_weight"] = ""
    st.session_state[f"{exercise_base}_set_0_reps"] = ""
    st.session_state[f"{exercise_base}_set_0_duration"] = ""
    st.session_state[f"{exercise_base}_set_0_placeholder_weight"] = ""
    st.session_state[f"{exercise_base}_set_0_placeholder_reps"] = ""
    st.session_state[f"{exercise_base}_set_0_placeholder_duration"] = ""


def _clear_exercise_state(prefix: str, exercise_index: int) -> None:
    """Delete all known session-state keys for one exercise section."""
    exercise_base = f"{prefix}_exercise_{exercise_index}"
    set_count = int(st.session_state.get(f"{exercise_base}_set_count", 0))

    keys_to_remove = [
        f"{exercise_base}_configured",
        f"{exercise_base}_name",
        f"{exercise_base}_saved_name",
        f"{exercise_base}_category",
        f"{exercise_base}_type",
        f"{exercise_base}_saved_category",
        f"{exercise_base}_saved_type",
        f"{exercise_base}_set_count",
        f"{exercise_base}_definition_id",
    ]

    for set_index in range(set_count + 2):
        set_base = f"{exercise_base}_set_{set_index}"
        keys_to_remove.extend(
            [
                f"{set_base}_weight",
                f"{set_base}_reps",
                f"{set_base}_duration",
                f"{set_base}_placeholder_weight",
                f"{set_base}_placeholder_reps",
                f"{set_base}_placeholder_duration",
            ]
        )

    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def _initialize_workout_form_state(
    prefix: str,
    initial_workout: Workout,
    service: WorkoutService,
) -> None:
    """Initialize workout form widget state from a workout draft."""
    nonce = st.session_state.get("logbook_dialog_nonce", "")
    initialized_nonce_key = f"{prefix}_initialized_nonce"
    if st.session_state.get(initialized_nonce_key) == nonce:
        return

    previous_count = int(st.session_state.get(f"{prefix}_exercise_count", 0))
    for previous_index in range(previous_count):
        _clear_exercise_state(prefix=prefix, exercise_index=previous_index)

    st.session_state[f"{prefix}_name"] = initial_workout.name
    st.session_state[f"{prefix}_date"] = initial_workout.workout_date
    st.session_state[f"{prefix}_notes"] = initial_workout.notes

    exercise_count = len(initial_workout.exercises)
    st.session_state[f"{prefix}_exercise_count"] = exercise_count

    for exercise_index in range(exercise_count):
        _ensure_exercise_state(prefix=prefix, exercise_index=exercise_index)
        exercise_base = f"{prefix}_exercise_{exercise_index}"

        entry = initial_workout.exercises[exercise_index]
        st.session_state[f"{exercise_base}_configured"] = True
        st.session_state[f"{exercise_base}_name"] = entry.exercise_name
        st.session_state[f"{exercise_base}_saved_name"] = entry.exercise_name
        st.session_state[f"{exercise_base}_category"] = entry.category.value
        st.session_state[f"{exercise_base}_type"] = entry.exercise_type.value
        st.session_state[f"{exercise_base}_saved_category"] = entry.category.value
        st.session_state[f"{exercise_base}_saved_type"] = entry.exercise_type.value
        st.session_state[f"{exercise_base}_definition_id"] = (
            entry.exercise_definition_id
        )

        previous_sets: list[WorkoutSet] = []
        if entry.exercise_definition_id:
            last_logged_entry = service.get_last_logged_exercise_entry(
                entry.exercise_definition_id
            )
            if last_logged_entry is not None:
                previous_sets = last_logged_entry.sets

        set_count = max(1, len(entry.sets))
        st.session_state[f"{exercise_base}_set_count"] = set_count
        for set_index in range(set_count):
            _ensure_set_state(
                prefix=prefix, exercise_index=exercise_index, set_index=set_index
            )
            set_base = f"{exercise_base}_set_{set_index}"
            default_set = entry.sets[set_index] if set_index < len(entry.sets) else None
            st.session_state[f"{set_base}_weight"] = (
                str(default_set.weight_kg)
                if default_set and default_set.weight_kg is not None
                else ""
            )
            st.session_state[f"{set_base}_reps"] = (
                str(default_set.reps)
                if default_set and default_set.reps is not None
                else ""
            )
            st.session_state[f"{set_base}_duration"] = (
                str(default_set.duration_seconds)
                if default_set and default_set.duration_seconds is not None
                else ""
            )

            has_explicit_values = bool(
                default_set
                and (
                    default_set.weight_kg is not None
                    or default_set.reps is not None
                    or default_set.duration_seconds is not None
                )
            )
            if has_explicit_values or set_index >= len(previous_sets):
                st.session_state[f"{set_base}_placeholder_weight"] = ""
                st.session_state[f"{set_base}_placeholder_reps"] = ""
                st.session_state[f"{set_base}_placeholder_duration"] = ""
            else:
                previous_set = previous_sets[set_index]
                st.session_state[f"{set_base}_placeholder_weight"] = (
                    str(previous_set.weight_kg)
                    if previous_set.weight_kg is not None
                    else ""
                )
                st.session_state[f"{set_base}_placeholder_reps"] = (
                    str(previous_set.reps) if previous_set.reps is not None else ""
                )
                st.session_state[f"{set_base}_placeholder_duration"] = (
                    str(previous_set.duration_seconds)
                    if previous_set.duration_seconds is not None
                    else ""
                )

    st.session_state[initialized_nonce_key] = nonce


def _add_exercise_from_definition(
    prefix: str,
    exercise_definition_id: str,
    exercise_name: str,
    category: ExerciseCategory,
    exercise_type: ExerciseType,
    placeholder_sets: list[WorkoutSet],
) -> None:
    """Add a new configured exercise section from one definition."""
    count_key = f"{prefix}_exercise_count"
    exercise_index = int(st.session_state[count_key])
    st.session_state[count_key] = exercise_index + 1
    _set_exercise_defaults(prefix=prefix, exercise_index=exercise_index)

    exercise_base = f"{prefix}_exercise_{exercise_index}"
    st.session_state[f"{exercise_base}_configured"] = True
    st.session_state[f"{exercise_base}_name"] = exercise_name
    st.session_state[f"{exercise_base}_saved_name"] = exercise_name
    st.session_state[f"{exercise_base}_category"] = category.value
    st.session_state[f"{exercise_base}_saved_category"] = category.value
    st.session_state[f"{exercise_base}_type"] = exercise_type.value
    st.session_state[f"{exercise_base}_saved_type"] = exercise_type.value
    st.session_state[f"{exercise_base}_definition_id"] = exercise_definition_id

    set_count = max(1, len(placeholder_sets))
    st.session_state[f"{exercise_base}_set_count"] = set_count
    for set_index in range(set_count):
        _ensure_set_state(
            prefix=prefix, exercise_index=exercise_index, set_index=set_index
        )
        set_base = f"{exercise_base}_set_{set_index}"
        if set_index < len(placeholder_sets):
            previous_set = placeholder_sets[set_index]
            st.session_state[f"{set_base}_placeholder_weight"] = (
                str(previous_set.weight_kg)
                if previous_set.weight_kg is not None
                else ""
            )
            st.session_state[f"{set_base}_placeholder_reps"] = (
                str(previous_set.reps) if previous_set.reps is not None else ""
            )
            st.session_state[f"{set_base}_placeholder_duration"] = (
                str(previous_set.duration_seconds)
                if previous_set.duration_seconds is not None
                else ""
            )


def _add_set(prefix: str, exercise_index: int) -> None:
    """Add a new set row to one exercise section."""
    set_count_key = f"{prefix}_exercise_{exercise_index}_set_count"
    current_count = int(st.session_state.get(set_count_key, 1))
    st.session_state[set_count_key] = current_count + 1
    _ensure_set_state(
        prefix=prefix, exercise_index=exercise_index, set_index=current_count
    )


def _remove_exercise(prefix: str, exercise_index: int) -> None:
    """Remove one exercise from the form and compact remaining sections."""
    exercise_count = int(st.session_state.get(f"{prefix}_exercise_count", 0))
    if exercise_index < 0 or exercise_index >= exercise_count:
        return

    for index in range(exercise_index, exercise_count - 1):
        source_base = f"{prefix}_exercise_{index + 1}"
        target_base = f"{prefix}_exercise_{index}"

        st.session_state[f"{target_base}_configured"] = st.session_state.get(
            f"{source_base}_configured", False
        )
        st.session_state[f"{target_base}_name"] = st.session_state.get(
            f"{source_base}_name", ""
        )
        st.session_state[f"{target_base}_saved_name"] = st.session_state.get(
            f"{source_base}_saved_name", ""
        )
        st.session_state[f"{target_base}_category"] = st.session_state.get(
            f"{source_base}_category", ExerciseCategory.OTHER.value
        )
        st.session_state[f"{target_base}_type"] = st.session_state.get(
            f"{source_base}_type", ExerciseType.WEIGHT_REPS.value
        )
        st.session_state[f"{target_base}_saved_category"] = st.session_state.get(
            f"{source_base}_saved_category", ExerciseCategory.OTHER.value
        )
        st.session_state[f"{target_base}_saved_type"] = st.session_state.get(
            f"{source_base}_saved_type", ExerciseType.WEIGHT_REPS.value
        )
        st.session_state[f"{target_base}_definition_id"] = st.session_state.get(
            f"{source_base}_definition_id", ""
        )
        st.session_state[f"{target_base}_set_count"] = st.session_state.get(
            f"{source_base}_set_count", 1
        )

        set_count = int(st.session_state[f"{target_base}_set_count"])
        for set_index in range(set_count):
            source_set_base = f"{source_base}_set_{set_index}"
            target_set_base = f"{target_base}_set_{set_index}"
            st.session_state[f"{target_set_base}_weight"] = st.session_state.get(
                f"{source_set_base}_weight", ""
            )
            st.session_state[f"{target_set_base}_reps"] = st.session_state.get(
                f"{source_set_base}_reps", ""
            )
            st.session_state[f"{target_set_base}_duration"] = st.session_state.get(
                f"{source_set_base}_duration", ""
            )
            st.session_state[f"{target_set_base}_placeholder_weight"] = (
                st.session_state.get(f"{source_set_base}_placeholder_weight", "")
            )
            st.session_state[f"{target_set_base}_placeholder_reps"] = (
                st.session_state.get(f"{source_set_base}_placeholder_reps", "")
            )
            st.session_state[f"{target_set_base}_placeholder_duration"] = (
                st.session_state.get(f"{source_set_base}_placeholder_duration", "")
            )

    trailing_index = exercise_count - 1
    _clear_exercise_state(prefix=prefix, exercise_index=trailing_index)
    st.session_state[f"{prefix}_exercise_count"] = max(0, exercise_count - 1)


def _rerun_keep_dialog(mode: str, workout_id: str = "") -> None:
    """Rerun while keeping the workout dialog open."""
    st.session_state["logbook_dialog_mode"] = mode
    if workout_id:
        st.session_state["logbook_edit_id"] = workout_id
    st.rerun()


def _parse_float(raw_value: str) -> float:
    """Parse float from text input with safe fallback."""
    value = raw_value.strip()
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _parse_int(raw_value: str) -> int:
    """Parse int from text input with safe fallback."""
    value = raw_value.strip()
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def _parse_duration_to_seconds(raw_value: str) -> int:
    """Parse duration text in seconds to int."""
    value = raw_value.strip()
    if not value:
        return 0
    return _parse_int(value)


def _build_workout_from_form(
    service: WorkoutService,
    form_prefix: str,
    existing_workout: Workout | None,
) -> Workout:
    """Create a workout model from form widget state."""
    workout_name = str(st.session_state[f"{form_prefix}_name"]).strip()
    workout_date = st.session_state[f"{form_prefix}_date"]
    workout_notes = str(st.session_state[f"{form_prefix}_notes"]).strip()
    exercise_count = int(st.session_state[f"{form_prefix}_exercise_count"])

    exercise_entries: list[WorkoutExerciseEntry] = []
    for exercise_index in range(exercise_count):
        _ensure_exercise_state(prefix=form_prefix, exercise_index=exercise_index)
        base = f"{form_prefix}_exercise_{exercise_index}"
        if not st.session_state.get(f"{base}_configured", False):
            continue

        selected_name = str(st.session_state.get(f"{base}_saved_name", "")).strip()
        if not selected_name:
            selected_name = str(st.session_state.get(f"{base}_name", "")).strip()
        if not selected_name:
            continue

        category_value = str(
            st.session_state.get(
                f"{base}_saved_category",
                st.session_state.get(f"{base}_category", ExerciseCategory.OTHER.value),
            )
        )
        type_value = str(
            st.session_state.get(
                f"{base}_saved_type",
                st.session_state.get(f"{base}_type", ExerciseType.WEIGHT_REPS.value),
            )
        )

        category = ExerciseCategory(category_value)
        exercise_type = ExerciseType(type_value)

        definition = service.ensure_exercise_definition(
            name=selected_name,
            category=category,
            exercise_type=exercise_type,
        )

        set_count = int(st.session_state[f"{base}_set_count"])
        sets: list[WorkoutSet] = []
        for set_index in range(set_count):
            _ensure_set_state(
                prefix=form_prefix, exercise_index=exercise_index, set_index=set_index
            )
            set_base = f"{base}_set_{set_index}"
            if exercise_type == ExerciseType.WEIGHT_REPS:
                sets.append(
                    WorkoutSet(
                        id="",
                        order_index=set_index,
                        weight_kg=_parse_float(
                            str(st.session_state[f"{set_base}_weight"])
                        ),
                        reps=_parse_int(str(st.session_state[f"{set_base}_reps"])),
                    )
                )
            elif exercise_type == ExerciseType.BODYWEIGHT_REPS:
                sets.append(
                    WorkoutSet(
                        id="",
                        order_index=set_index,
                        reps=_parse_int(str(st.session_state[f"{set_base}_reps"])),
                    )
                )
            else:
                sets.append(
                    WorkoutSet(
                        id="",
                        order_index=set_index,
                        duration_seconds=_parse_duration_to_seconds(
                            str(st.session_state[f"{set_base}_duration"])
                        ),
                    )
                )

        exercise_entries.append(
            WorkoutExerciseEntry(
                id="",
                exercise_definition_id=definition.id,
                exercise_name=definition.name,
                category=definition.category,
                exercise_type=definition.exercise_type,
                sets=sets,
            )
        )

    return Workout(
        id=existing_workout.id if existing_workout else "",
        name=workout_name,
        workout_date=workout_date,
        notes=workout_notes,
        exercises=exercise_entries,
    )


def _render_set_inputs(
    prefix: str, exercise_index: int, exercise_type: ExerciseType
) -> None:
    """Render set rows for one exercise section in one-line rows."""
    set_count = int(st.session_state[f"{prefix}_exercise_{exercise_index}_set_count"])
    for set_index in range(set_count):
        _ensure_set_state(
            prefix=prefix, exercise_index=exercise_index, set_index=set_index
        )
        row = st.columns([1, 3, 3])
        row[0].markdown(f"**{set_index + 1}**")
        set_base = f"{prefix}_exercise_{exercise_index}_set_{set_index}"

        if exercise_type == ExerciseType.WEIGHT_REPS:
            row[1].text_input(
                "kg",
                key=f"{set_base}_weight",
                label_visibility="collapsed",
                placeholder=str(
                    st.session_state.get(f"{set_base}_placeholder_weight", "")
                ),
            )
            row[2].text_input(
                "reps",
                key=f"{set_base}_reps",
                label_visibility="collapsed",
                placeholder=str(
                    st.session_state.get(f"{set_base}_placeholder_reps", "")
                ),
            )
        elif exercise_type == ExerciseType.BODYWEIGHT_REPS:
            row[1].text_input(
                "reps",
                key=f"{set_base}_reps",
                label_visibility="collapsed",
                placeholder=str(
                    st.session_state.get(f"{set_base}_placeholder_reps", "")
                ),
            )
        else:
            row[1].text_input(
                "duration",
                key=f"{set_base}_duration",
                label_visibility="collapsed",
                placeholder=str(
                    st.session_state.get(f"{set_base}_placeholder_duration", "")
                )
                or "seconds",
            )


def _collect_form_snapshot(form_prefix: str) -> str:
    """Collect current form widget state into a deterministic string payload."""
    exercise_count = int(st.session_state.get(f"{form_prefix}_exercise_count", 0))
    snapshot: dict[str, object] = {
        "name": str(st.session_state.get(f"{form_prefix}_name", "")),
        "date": str(st.session_state.get(f"{form_prefix}_date", "")),
        "notes": str(st.session_state.get(f"{form_prefix}_notes", "")),
        "exercise_count": exercise_count,
        "exercises": [],
    }

    exercises: list[dict[str, object]] = []
    for exercise_index in range(exercise_count):
        _ensure_exercise_state(prefix=form_prefix, exercise_index=exercise_index)
        exercise_base = f"{form_prefix}_exercise_{exercise_index}"
        set_count = int(st.session_state.get(f"{exercise_base}_set_count", 0))

        sets: list[dict[str, str]] = []
        for set_index in range(set_count):
            _ensure_set_state(
                prefix=form_prefix,
                exercise_index=exercise_index,
                set_index=set_index,
            )
            set_base = f"{exercise_base}_set_{set_index}"
            sets.append(
                {
                    "weight": str(st.session_state.get(f"{set_base}_weight", "")),
                    "reps": str(st.session_state.get(f"{set_base}_reps", "")),
                    "duration": str(st.session_state.get(f"{set_base}_duration", "")),
                }
            )

        exercises.append(
            {
                "configured": bool(
                    st.session_state.get(f"{exercise_base}_configured", False)
                ),
                "name": str(st.session_state.get(f"{exercise_base}_saved_name", "")),
                "category": str(
                    st.session_state.get(f"{exercise_base}_saved_category", "")
                ),
                "type": str(st.session_state.get(f"{exercise_base}_saved_type", "")),
                "set_count": set_count,
                "sets": sets,
            }
        )

    snapshot["exercises"] = exercises
    return json.dumps(snapshot, sort_keys=True)


def _is_empty_form(form_prefix: str) -> bool:
    """Return whether form currently contains no meaningful workout content."""
    if str(st.session_state.get(f"{form_prefix}_name", "")).strip():
        return False
    if str(st.session_state.get(f"{form_prefix}_notes", "")).strip():
        return False

    exercise_count = int(st.session_state.get(f"{form_prefix}_exercise_count", 0))
    for exercise_index in range(exercise_count):
        _ensure_exercise_state(prefix=form_prefix, exercise_index=exercise_index)
        exercise_base = f"{form_prefix}_exercise_{exercise_index}"
        if st.session_state.get(f"{exercise_base}_configured", False):
            return False
    return True


def _autosave_workout_form(
    service: WorkoutService,
    form_prefix: str,
    existing_workout: Workout | None,
) -> None:
    """Autosave the workout form when changed and valid."""
    if _is_empty_form(form_prefix):
        return

    snapshot = _collect_form_snapshot(form_prefix)
    last_hash = str(st.session_state.get("logbook_autosave_last_hash", ""))
    if snapshot == last_hash:
        return

    now_monotonic = time.monotonic()
    last_save_ts = float(st.session_state.get("logbook_autosave_last_ts", 0.0))
    if now_monotonic - last_save_ts < 1.5:
        return

    autosave_workout_id = str(st.session_state.get("logbook_autosave_workout_id", ""))
    build_context = existing_workout
    if build_context is None and autosave_workout_id:
        build_context = Workout(
            id=autosave_workout_id,
            name="",
            workout_date=date.today(),
            notes="",
            exercises=[],
        )

    draft = _build_workout_from_form(
        service=service,
        form_prefix=form_prefix,
        existing_workout=build_context,
    )

    try:
        saved_id = service.save_workout(draft)
    except ValidationError:
        return

    st.session_state["logbook_autosave_workout_id"] = saved_id
    st.session_state["logbook_autosave_last_hash"] = snapshot
    st.session_state["logbook_autosave_last_ts"] = now_monotonic
    st.session_state["logbook_autosave_status"] = (
        f"Autosaved at {time.strftime('%H:%M:%S')}"
    )


@st.dialog("Workout")
def _workout_dialog(
    service: WorkoutService,
    mode: str,
    initial_workout: Workout,
    existing_workout: Workout | None,
) -> None:
    """Render create/edit workout dialog."""
    form_prefix = "workout_form"
    _initialize_workout_form_state(
        prefix=form_prefix,
        initial_workout=initial_workout,
        service=service,
    )

    definitions = service.list_exercise_definitions()

    if mode == "edit" and existing_workout is not None:
        top_left, top_right = st.columns([7, 1])
        with top_left:
            st.write("")
        with top_right:
            with st.popover("⋮"):
                if st.button("Delete Workout", width="stretch"):
                    service.delete_workout(existing_workout.id)
                    st.session_state["logbook_template_workout"] = None
                    st.session_state["logbook_autosave_workout_id"] = ""
                    st.session_state["logbook_autosave_last_hash"] = ""
                    st.session_state["logbook_autosave_last_ts"] = 0.0
                    st.session_state["logbook_autosave_status"] = ""
                    st.rerun()

                if st.button("Save as workout plan", width="stretch"):
                    workout_for_plan = _build_workout_from_form(
                        service=service,
                        form_prefix=form_prefix,
                        existing_workout=existing_workout,
                    )
                    service.save_workout_as_plan(workout_for_plan)
                    st.session_state["logbook_template_workout"] = None
                    st.rerun()

    dialog_mode_for_rerun = (
        "edit" if mode == "edit" and existing_workout is not None else "create"
    )
    dialog_workout_id = existing_workout.id if existing_workout is not None else ""

    with st.container(horizontal=True):
        st.text_input("Workout Name", key=f"{form_prefix}_name")
        st.date_input("Date", key=f"{form_prefix}_date")
    st.text_area("Notes", key=f"{form_prefix}_notes", height=32)

    _autosave_workout_form(
        service=service,
        form_prefix=form_prefix,
        existing_workout=existing_workout,
    )

    exercise_count = int(st.session_state[f"{form_prefix}_exercise_count"])
    for exercise_index in range(exercise_count):
        _ensure_exercise_state(prefix=form_prefix, exercise_index=exercise_index)
        exercise_base = f"{form_prefix}_exercise_{exercise_index}"

        with st.container(border=True):
            header_left, header_right = st.columns([8, 1])
            with header_right:
                if st.button("❌", key=f"{exercise_base}_remove", width="content"):
                    _remove_exercise(prefix=form_prefix, exercise_index=exercise_index)
                    _rerun_keep_dialog(
                        mode=dialog_mode_for_rerun, workout_id=dialog_workout_id
                    )

            if not st.session_state.get(f"{exercise_base}_configured", False):
                header_left.markdown("#### Exercise")
                st.info("Exercise entry is not configured. Remove it and add again.")
                continue

            exercise_name = str(
                st.session_state.get(f"{exercise_base}_saved_name", "")
            ).strip()
            if not exercise_name:
                exercise_name = str(
                    st.session_state.get(f"{exercise_base}_name", "")
                ).strip()
            if not exercise_name:
                exercise_name = "Exercise"
            header_left.markdown(f"#### {exercise_name}")
            category_label = str(
                st.session_state.get(
                    f"{exercise_base}_saved_category",
                    st.session_state.get(
                        f"{exercise_base}_category", ExerciseCategory.OTHER.value
                    ),
                )
            )
            type_label = str(
                st.session_state.get(
                    f"{exercise_base}_saved_type",
                    st.session_state.get(
                        f"{exercise_base}_type", ExerciseType.WEIGHT_REPS.value
                    ),
                )
            )
            st.caption(f"{category_label} • {type_label}")

            selected_type = ExerciseType(type_label)
            _render_set_inputs(
                prefix=form_prefix,
                exercise_index=exercise_index,
                exercise_type=selected_type,
            )

            if st.button("Add Set", key=f"{exercise_base}_add_set", width="stretch"):
                _add_set(prefix=form_prefix, exercise_index=exercise_index)
                _rerun_keep_dialog(
                    mode=dialog_mode_for_rerun, workout_id=dialog_workout_id
                )

    if not definitions:
        st.info(
            "No exercise definitions available. Add exercises in Exercise settings."
        )
    else:
        with st.popover("Add Exercise", use_container_width=True):
            for definition in definitions:
                button_label = f"{definition.name} ({definition.category.value})"
                if st.button(
                    button_label,
                    key=f"{form_prefix}_add_definition_{definition.id}",
                    width="stretch",
                ):
                    previous_entry = service.get_last_logged_exercise_entry(
                        definition.id
                    )
                    placeholder_sets = previous_entry.sets if previous_entry else []
                    _add_exercise_from_definition(
                        prefix=form_prefix,
                        exercise_definition_id=definition.id,
                        exercise_name=definition.name,
                        category=definition.category,
                        exercise_type=definition.exercise_type,
                        placeholder_sets=placeholder_sets,
                    )
                    _rerun_keep_dialog(
                        mode=dialog_mode_for_rerun,
                        workout_id=dialog_workout_id,
                    )

    autosave_status = str(st.session_state.get("logbook_autosave_status", "")).strip()
    if autosave_status:
        st.caption(autosave_status)

    save_label = "Save Workout" if mode != "edit" else "Finish Workout"
    if st.button(save_label, width="stretch"):
        build_context = existing_workout
        autosave_workout_id = str(
            st.session_state.get("logbook_autosave_workout_id", "")
        )
        if build_context is None and autosave_workout_id:
            build_context = Workout(
                id=autosave_workout_id,
                name="",
                workout_date=date.today(),
                notes="",
                exercises=[],
            )

        workout = _build_workout_from_form(
            service=service,
            form_prefix=form_prefix,
            existing_workout=build_context,
        )
        try:
            service.save_workout(workout)
        except ValidationError as error:
            st.error(str(error))
            return

        st.session_state["logbook_template_workout"] = None
        st.session_state["logbook_autosave_workout_id"] = ""
        st.session_state["logbook_autosave_last_hash"] = ""
        st.session_state["logbook_autosave_last_ts"] = 0.0
        st.session_state["logbook_autosave_status"] = ""
        st.rerun()


def _open_dialog_if_requested(service: WorkoutService) -> None:
    """Open dialog only once per trigger, avoiding reopen loops across tabs."""
    dialog_mode = st.session_state.get("logbook_dialog_mode")
    if not dialog_mode:
        return

    st.session_state["logbook_dialog_mode"] = None

    if dialog_mode == "create":
        st.session_state["logbook_autosave_workout_id"] = ""
        st.session_state["logbook_autosave_last_hash"] = ""
        st.session_state["logbook_autosave_last_ts"] = 0.0
        st.session_state["logbook_autosave_status"] = ""
        draft = Workout(
            id="", name="", workout_date=date.today(), notes="", exercises=[]
        )
        _workout_dialog(
            service=service, mode="create", initial_workout=draft, existing_workout=None
        )
        return

    if dialog_mode == "edit":
        workout_id = st.session_state.get("logbook_edit_id", "")
        st.session_state["logbook_autosave_workout_id"] = workout_id
        st.session_state["logbook_autosave_last_hash"] = ""
        st.session_state["logbook_autosave_last_ts"] = 0.0
        st.session_state["logbook_autosave_status"] = ""
        workout = service.get_workout(workout_id) if workout_id else None
        if workout is not None:
            _workout_dialog(
                service=service,
                mode="edit",
                initial_workout=workout,
                existing_workout=workout,
            )
        return

    if dialog_mode == "create_from_plan":
        st.session_state["logbook_autosave_workout_id"] = ""
        st.session_state["logbook_autosave_last_hash"] = ""
        st.session_state["logbook_autosave_last_ts"] = 0.0
        st.session_state["logbook_autosave_status"] = ""
        workout_template = st.session_state.get("logbook_template_workout")
        if workout_template is not None:
            _workout_dialog(
                service=service,
                mode="create",
                initial_workout=workout_template,
                existing_workout=None,
            )


def render(repository: FalseGripRepository) -> None:
    """Render the logbook page."""
    _initialize_page_state()
    service = WorkoutService(repository=repository)
    workouts = service.list_workouts(limit=st.session_state["logbook_limit"], offset=0)

    if st.button("+ Add Workout", key="logbook_add_above", width="stretch"):
        st.session_state["logbook_dialog_mode"] = "create"
        st.session_state["logbook_edit_id"] = ""
        st.session_state["logbook_dialog_nonce"] = str(uuid4())
        st.rerun()

    for workout in workouts:
        with st.container(border=True):
            left, right = st.columns([1, 3])
            left.write(workout.workout_date.strftime("%Y-%m-%d"))
            right.subheader(workout.name)
            right.text(_exercise_summary(workout))
            if st.button("Open", key=f"open_{workout.id}", width="stretch"):
                st.session_state["logbook_dialog_mode"] = "edit"
                st.session_state["logbook_edit_id"] = workout.id
                st.session_state["logbook_dialog_nonce"] = str(uuid4())
                st.rerun()

    if len(workouts) == st.session_state["logbook_limit"]:
        if st.button("Load More", width="stretch"):
            st.session_state["logbook_limit"] += PAGE_SIZE
            st.rerun()

    _open_dialog_if_requested(service=service)
