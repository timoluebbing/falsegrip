"""Centralized Workout Editor Component."""

from __future__ import annotations

import time
from datetime import date

import streamlit as st

from falsegrip.models import ValidationError
from falsegrip.models.enums import ExerciseType
from falsegrip.models.workout import (
    Workout,
    WorkoutExerciseEntry,
    WorkoutSet,
    WorkoutPlan,
)
from falsegrip.models.drafts import WorkoutDraft, ExerciseDraft, SetDraft
from falsegrip.models.ui_enums import EditorMode
from falsegrip.services.workout_service import WorkoutService


def bound_text_input(label: str, obj: object, attr: str, key: str, **kwargs) -> str:
    if key not in st.session_state:
        st.session_state[key] = getattr(obj, attr)
    val = st.text_input(label, key=key, **kwargs)
    setattr(obj, attr, val)
    return val


def bound_date_input(label: str, obj: object, attr: str, key: str, **kwargs) -> date:
    if key not in st.session_state:
        st.session_state[key] = getattr(obj, attr)
    val = st.date_input(label, key=key, **kwargs)
    setattr(obj, attr, val)
    return val


def bound_text_area(label: str, obj: object, attr: str, key: str, **kwargs) -> str:
    if key not in st.session_state:
        st.session_state[key] = getattr(obj, attr)
    val = st.text_area(label, key=key, **kwargs)
    setattr(obj, attr, val)
    return val


def _parse_float(raw_value: str) -> float:
    value = raw_value.strip()
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _parse_int(raw_value: str) -> int:
    value = raw_value.strip()
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def workout_to_draft(workout: Workout, service: WorkoutService) -> WorkoutDraft:
    draft = WorkoutDraft(
        id=workout.id,
        name=workout.name,
        workout_date=workout.workout_date,
        notes=workout.notes,
        exercises=[],
        autosaved_id="",
    )

    for entry in workout.exercises:
        previous_sets: list[WorkoutSet] = []
        if entry.exercise_definition_id:
            last_logged_entry = service.get_last_logged_exercise_entry(
                entry.exercise_definition_id
            )
            if last_logged_entry is not None:
                previous_sets = last_logged_entry.sets

        ex_draft = ExerciseDraft(
            configured=True,
            name=entry.exercise_name,
            category=entry.category,
            exercise_type=entry.exercise_type,
            definition_id=entry.exercise_definition_id,
            sets=[],
        )

        set_count = max(1, len(entry.sets))
        for set_idx in range(set_count):
            default_set = entry.sets[set_idx] if set_idx < len(entry.sets) else None

            s_draft = SetDraft(
                weight_kg=str(default_set.weight_kg)
                if default_set and default_set.weight_kg is not None
                else "",
                reps=str(default_set.reps)
                if default_set and default_set.reps is not None
                else "",
                duration_seconds=str(default_set.duration_seconds)
                if default_set and default_set.duration_seconds is not None
                else "",
            )

            has_explicit = bool(
                default_set
                and (
                    default_set.weight_kg is not None
                    or default_set.reps is not None
                    or default_set.duration_seconds is not None
                )
            )

            if not has_explicit and set_idx < len(previous_sets):
                prev = previous_sets[set_idx]
                s_draft.placeholder_weight = (
                    str(prev.weight_kg) if prev.weight_kg is not None else ""
                )
                s_draft.placeholder_reps = (
                    str(prev.reps) if prev.reps is not None else ""
                )
                s_draft.placeholder_duration = (
                    str(prev.duration_seconds)
                    if prev.duration_seconds is not None
                    else ""
                )

            ex_draft.sets.append(s_draft)

        draft.exercises.append(ex_draft)

    return draft


def draft_to_workout(
    draft: WorkoutDraft, service: WorkoutService, is_draft: bool = False
) -> Workout:
    entries: list[WorkoutExerciseEntry] = []
    for ex in draft.exercises:
        if not ex.configured or not ex.name.strip():
            continue

        definition = service.ensure_exercise_definition(
            name=ex.name.strip(), category=ex.category, exercise_type=ex.exercise_type
        )

        sets: list[WorkoutSet] = []
        for i, s in enumerate(ex.sets):
            w_set = WorkoutSet(id="", order_index=i)
            if ex.exercise_type == ExerciseType.WEIGHT_REPS:
                w_set.weight_kg = _parse_float(s.weight_kg)
                w_set.reps = _parse_int(s.reps)
            elif ex.exercise_type == ExerciseType.BODYWEIGHT_REPS:
                w_set.reps = _parse_int(s.reps)
            else:
                w_set.duration_seconds = _parse_int(s.duration_seconds)
            sets.append(w_set)

        entries.append(
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
        id=draft.id,
        name=draft.name,
        workout_date=draft.workout_date,
        notes=draft.notes,
        is_draft=is_draft,
        exercises=entries,
    )


def render_workout_editor(
    service: WorkoutService, mode: EditorMode, on_close: callable
):
    if "current_workout_draft" not in st.session_state:
        st.warning("No active draft. Please close and re-open.")
        if st.button("Close"):
            on_close()
        return

    draft: WorkoutDraft = st.session_state["current_workout_draft"]

    if mode == EditorMode.EDIT:
        top_left, top_right = st.columns([7, 1])
        with top_right:
            with st.popover("⋮"):
                if st.button("Delete Workout", width="stretch"):
                    service.delete_workout(draft.id)
                    st.session_state["logbook_autosave_last_hash"] = ""
                    st.session_state["logbook_autosave_last_ts"] = 0.0
                    on_close()
                    st.rerun()

                if st.button("Save as workout plan", width="stretch"):
                    w_for_plan = draft_to_workout(draft, service, is_draft=False)
                    service.save_workout_as_plan(w_for_plan)
                    on_close()
                    st.rerun()

    with st.container(horizontal=True):
        bound_text_input(
            "Workout Name" if mode != EditorMode.PLAN_EDIT else "Plan Name",
            draft,
            "name",
            key=f"draft_name_{getattr(draft, 'key_id', '')}",
        )
        if mode != EditorMode.PLAN_EDIT:
            bound_date_input(
                "Date",
                draft,
                "workout_date",
                key=f"draft_date_{getattr(draft, 'key_id', '')}",
            )
    bound_text_area(
        "Notes",
        draft,
        "notes",
        key=f"draft_notes_{getattr(draft, 'key_id', '')}",
        height=32,
    )

    indices_to_remove = []

    for i, ex in enumerate(draft.exercises):
        with st.container(border=True):
            header_left, header_right = st.columns([8, 1])
            with header_right:
                if st.button("❌", key=f"rm_{ex.key_id}", width="content"):
                    indices_to_remove.append(i)

            if not ex.configured:
                header_left.markdown("#### Exercise")
                continue

            header_left.markdown(f"#### {ex.name if ex.name else 'Exercise'}")
            st.caption(f"{ex.category.value} • {ex.exercise_type.value}")

            for s_idx, s in enumerate(ex.sets):
                with st.container(horizontal=True):
                    st.markdown(f"**{s_idx + 1}**")

                    if ex.exercise_type == ExerciseType.WEIGHT_REPS:
                        bound_text_input(
                            "kg",
                            s,
                            "weight_kg",
                            key=f"w_{s.key_id}",
                            label_visibility="collapsed",
                            placeholder=s.placeholder_weight,
                        )
                        bound_text_input(
                            "reps",
                            s,
                            "reps",
                            key=f"r_{s.key_id}",
                            label_visibility="collapsed",
                            placeholder=s.placeholder_reps,
                        )
                    elif ex.exercise_type == ExerciseType.BODYWEIGHT_REPS:
                        bound_text_input(
                            "reps",
                            s,
                            "reps",
                            key=f"r_{s.key_id}",
                            label_visibility="collapsed",
                            placeholder=s.placeholder_reps,
                        )
                    else:
                        bound_text_input(
                            "duration",
                            s,
                            "duration_seconds",
                            key=f"d_{s.key_id}",
                            label_visibility="collapsed",
                            placeholder=s.placeholder_duration or "seconds",
                        )

            if st.button("Add Set", key=f"add_{ex.key_id}", width="stretch"):
                ex.sets.append(SetDraft())
                st.rerun()

    if indices_to_remove:
        for idx in reversed(indices_to_remove):
            ex_to_remove = draft.exercises.pop(idx)
            # Remove keys associated with deleted exercise to avoid memory leak
            for s in ex_to_remove.sets:
                for suffix in ["w_", "r_", "d_"]:
                    st.session_state.pop(f"{suffix}{s.key_id}", None)
        st.rerun()

    definitions = service.list_exercise_definitions()
    if not definitions:
        st.info(
            "No exercise definitions available. Add exercises in Exercise settings."
        )
    else:
        with st.popover("Add Exercise", use_container_width=True):
            for dfn in definitions:
                if st.button(
                    f"{dfn.name} ({dfn.category.value})",
                    key=f"def_{dfn.id}",
                    width="stretch",
                ):
                    prev = service.get_last_logged_exercise_entry(dfn.id)
                    new_ex = ExerciseDraft(
                        configured=True,
                        name=dfn.name,
                        category=dfn.category,
                        exercise_type=dfn.exercise_type,
                        definition_id=dfn.id,
                        sets=[],
                    )
                    p_sets = prev.sets if prev else []
                    set_count = max(1, len(p_sets))
                    for p_idx in range(set_count):
                        sd = SetDraft()
                        if p_idx < len(p_sets):
                            p = p_sets[p_idx]
                            sd.placeholder_weight = (
                                str(p.weight_kg) if p.weight_kg is not None else ""
                            )
                            sd.placeholder_reps = (
                                str(p.reps) if p.reps is not None else ""
                            )
                            sd.placeholder_duration = (
                                str(p.duration_seconds)
                                if p.duration_seconds is not None
                                else ""
                            )
                        new_ex.sets.append(sd)
                    draft.exercises.append(new_ex)
                    st.rerun()

    def try_autosave():
        if mode == EditorMode.PLAN_EDIT:
            return

        if draft.is_empty():
            return

        current_hash = draft.data_hash
        last_hash = st.session_state.get("logbook_autosave_last_hash", "")
        if current_hash == last_hash:
            return

        now_ts = time.monotonic()
        last_ts = st.session_state.get("logbook_autosave_last_ts", 0.0)

        if now_ts - last_ts < 1.5:
            return

        is_draft_save = mode != EditorMode.EDIT
        temp_workout = draft_to_workout(draft, service, is_draft=is_draft_save)
        if draft.autosaved_id and not temp_workout.id:
            temp_workout.id = draft.autosaved_id

        try:
            saved_id = service.save_workout(temp_workout)
            draft.autosaved_id = saved_id
            if not draft.id and mode == EditorMode.CREATE:
                draft.id = saved_id
            st.session_state["logbook_autosave_last_hash"] = current_hash
            st.session_state["logbook_autosave_last_ts"] = now_ts
            st.session_state["logbook_autosave_status"] = (
                f"Autosaved at {time.strftime('%H:%M:%S')}"
            )
        except ValidationError:
            pass

    try_autosave()

    autosave_status = st.session_state.get("logbook_autosave_status", "")
    if autosave_status:
        st.caption(autosave_status)

    save_label = "Save Workout" if mode != EditorMode.EDIT else "Finish Workout"
    if mode == EditorMode.PLAN_EDIT:
        save_label = "Save Plan"

    if st.button(save_label, width="stretch"):
        final_workout = draft_to_workout(draft, service, is_draft=False)

        try:
            if mode == EditorMode.PLAN_EDIT:
                plan = WorkoutPlan(
                    id=draft.id,
                    name=final_workout.name,
                    notes=final_workout.notes,
                    exercises=final_workout.exercises,
                )
                service.save_workout_plan(plan)
            else:
                if draft.autosaved_id and not final_workout.id:
                    final_workout.id = draft.autosaved_id
                service.save_workout(final_workout)

            st.session_state["logbook_autosave_last_hash"] = ""
            st.session_state["logbook_autosave_last_ts"] = 0.0
            st.session_state["logbook_autosave_status"] = ""
            on_close()
            st.rerun()
        except ValidationError as error:
            st.error(str(error))
