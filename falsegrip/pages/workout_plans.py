"""Workout plans page renderer."""

from __future__ import annotations


import streamlit as st

from falsegrip.models.workout import WorkoutPlan
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.workout_service import WorkoutService
from falsegrip.components.dialogs import confirm_deletion


from falsegrip.models.ui_enums import EditorMode


def _plan_summary(plan: WorkoutPlan) -> str:
    """Return multiline set-count summary for a workout plan."""
    return "\n".join(
        f"{len(entry.sets)}x {entry.exercise_name}" for entry in plan.exercises
    )


def render(repository: FalseGripRepository) -> None:
    """Render the workout plans page."""
    service = WorkoutService(repository=repository)
    plans = service.list_workout_plans()

    if st.button("+ New Workout Plan", key="plans_new_workout", width="stretch"):
        st.session_state["workout_plan_edit_id"] = ""
        st.session_state["logbook_dialog_mode"] = EditorMode.PLAN_EDIT.value
        if "current_workout_draft" in st.session_state:
            del st.session_state["current_workout_draft"]
        st.rerun()

    if not plans:
        st.info("No workout plans yet. Save a workout as a plan from the Logbook page.")
        return

    for plan in plans:
        with st.container(border=True):
            header_left, header_right = st.columns([8, 1])
            header_left.subheader(plan.name)
            with header_right:
                if st.button(
                    "❌", key=f"delete_plan_trigger_{plan.id}", use_container_width=True
                ):

                    def do_delete(p_id=plan.id):
                        service.delete_workout_plan(p_id)

                    confirm_deletion(
                        "Are you sure you want to delete this workout plan?", do_delete
                    )

            st.text(_plan_summary(plan))

            with st.container(horizontal=True):
                if st.button("Start Workout", key=f"start_{plan.id}", width="stretch"):
                    workout = service.start_workout_from_plan(plan)
                    st.session_state["logbook_template_workout"] = workout
                    st.session_state["logbook_dialog_mode"] = EditorMode.FROM_PLAN.value
                    if "current_workout_draft" in st.session_state:
                        del st.session_state["current_workout_draft"]
                    st.rerun()

                if st.button("Edit Plan", key=f"edit_{plan.id}", width="stretch"):
                    st.session_state["workout_plan_edit_id"] = plan.id
                    st.session_state["logbook_dialog_mode"] = EditorMode.PLAN_EDIT.value
                    if "current_workout_draft" in st.session_state:
                        del st.session_state["current_workout_draft"]
                    st.rerun()
