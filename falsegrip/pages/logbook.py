"""Logbook page renderer."""

from __future__ import annotations

from datetime import date

import streamlit as st

from falsegrip.models.workout import Workout
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.workout_service import WorkoutService
from falsegrip.models.ui_enums import EditorMode
from falsegrip.components.workout_editor import workout_to_draft, render_workout_editor


PAGE_SIZE = 10


def _initialize_page_state() -> None:
    """Initialize page-level state keys."""
    if "logbook_limit" not in st.session_state:
        st.session_state["logbook_limit"] = PAGE_SIZE
    if "logbook_dialog_mode" not in st.session_state:
        st.session_state["logbook_dialog_mode"] = None
    if "logbook_edit_id" not in st.session_state:
        st.session_state["logbook_edit_id"] = ""
    # These legacy vars are kept for fallback if needed, but not heavily used now
    if "logbook_template_workout" not in st.session_state:
        st.session_state["logbook_template_workout"] = None
    if "logbook_autosave_workout_id" not in st.session_state:
        st.session_state["logbook_autosave_workout_id"] = ""
    if "logbook_autosave_last_hash" not in st.session_state:
        st.session_state["logbook_autosave_last_hash"] = ""
    if "logbook_autosave_last_ts" not in st.session_state:
        st.session_state["logbook_autosave_last_ts"] = 0.0
    if "logbook_autosave_status" not in st.session_state:
        st.session_state["logbook_autosave_status"] = ""


def _exercise_summary(workout: Workout) -> str:
    """Return multiline exercise summary for a workout card."""
    return "\n".join(
        f"{len(entry.sets)}x {entry.exercise_name}" for entry in workout.exercises
    )


def close_dialog():
    st.session_state["logbook_dialog_mode"] = None
    if "current_workout_draft" in st.session_state:
        del st.session_state["current_workout_draft"]


@st.dialog("Workout")
def _workout_dialog(service: WorkoutService, mode: EditorMode) -> None:
    render_workout_editor(service=service, mode=mode, on_close=close_dialog)


def _open_dialog_if_requested(service: WorkoutService) -> None:
    """Open dialog only once per trigger, avoiding reopen loops across tabs."""
    dialog_mode = st.session_state.get("logbook_dialog_mode")
    if not dialog_mode:
        return

    mode = EditorMode(dialog_mode)

    if "current_workout_draft" not in st.session_state:
        if mode == EditorMode.CREATE:
            draft = Workout(
                id="", name="", workout_date=date.today(), notes="", exercises=[]
            )
            st.session_state["current_workout_draft"] = workout_to_draft(draft, service)

        elif mode == EditorMode.EDIT:
            workout_id = st.session_state.get("logbook_edit_id", "")
            workout = service.get_workout(workout_id) if workout_id else None
            if workout is not None:
                st.session_state["current_workout_draft"] = workout_to_draft(
                    workout, service
                )

        elif mode == EditorMode.FROM_PLAN:
            workout_template: Workout | None = st.session_state.get(
                "logbook_template_workout"
            )
            if workout_template is not None:
                st.session_state["current_workout_draft"] = workout_to_draft(
                    workout_template, service
                )

        elif mode == EditorMode.PLAN_EDIT:
            plan_id = st.session_state.get("workout_plan_edit_id", "")
            if plan_id:
                plan = service.get_workout_plan(plan_id)
                if plan is not None:
                    dummy_workout = Workout(
                        id=plan.id,
                        name=plan.name,
                        workout_date=date.today(),
                        notes=plan.notes,
                        exercises=plan.exercises,
                    )
                    st.session_state["current_workout_draft"] = workout_to_draft(
                        dummy_workout, service
                    )
            else:
                dummy_workout = Workout(
                    id="", name="", workout_date=date.today(), notes="", exercises=[]
                )
                st.session_state["current_workout_draft"] = workout_to_draft(
                    dummy_workout, service
                )

    if "current_workout_draft" in st.session_state:
        _workout_dialog(service=service, mode=mode)


def render(repository: FalseGripRepository) -> None:
    """Render the logbook page."""
    _initialize_page_state()
    service = WorkoutService(repository=repository)
    workouts = service.list_workouts(limit=st.session_state["logbook_limit"], offset=0)

    if st.button("+ Add Workout", key="logbook_add_above", width="stretch"):
        st.session_state["logbook_dialog_mode"] = EditorMode.CREATE.value
        st.session_state["logbook_edit_id"] = ""
        if "current_workout_draft" in st.session_state:
            del st.session_state["current_workout_draft"]
        st.rerun()

    for workout in workouts:
        with st.container(border=True):
            left, right = st.columns([1, 3])
            left.write(workout.workout_date.strftime("%Y-%m-%d"))
            right.subheader(workout.name)
            right.text(_exercise_summary(workout))
            if st.button("Edit Workout", key=f"open_{workout.id}", width="stretch"):
                st.session_state["logbook_dialog_mode"] = EditorMode.EDIT.value
                st.session_state["logbook_edit_id"] = workout.id
                # clear legacy draft just in case
                if "current_workout_draft" in st.session_state:
                    del st.session_state["current_workout_draft"]
                st.rerun()

    if len(workouts) == st.session_state["logbook_limit"]:
        if st.button("Load More", width="stretch"):
            st.session_state["logbook_limit"] += PAGE_SIZE
            st.rerun()

    _open_dialog_if_requested(service=service)
