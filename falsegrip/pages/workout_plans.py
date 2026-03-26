"""Workout plans page renderer."""

from __future__ import annotations

from uuid import uuid4

import streamlit as st

from falsegrip.models.workout import WorkoutPlan
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.workout_service import WorkoutService


def _plan_summary(plan: WorkoutPlan) -> str:
    """Return multiline set-count summary for a workout plan."""
    return "\n".join(
        f"{len(entry.sets)}x {entry.exercise_name}" for entry in plan.exercises
    )


def render(repository: FalseGripRepository) -> None:
    """Render the workout plans page."""
    service = WorkoutService(repository=repository)
    plans = service.list_workout_plans()

    if st.button("+ New Workout", key="plans_new_workout", width="stretch"):
        st.session_state["logbook_template_workout"] = None
        st.session_state["logbook_dialog_mode"] = "create"
        st.session_state["logbook_dialog_nonce"] = str(uuid4())
        st.rerun()

    if not plans:
        st.info("No workout plans yet. Save a workout as a plan from the Logbook page.")
        return

    for plan in plans:
        with st.container(border=True):
            header_left, header_right = st.columns([8, 1])
            header_left.subheader(plan.name)
            with header_right:
                with st.popover("❌", use_container_width=True):
                    st.warning("Delete this workout plan?")
                    if st.button(
                        "Delete Workout Plan",
                        key=f"delete_plan_confirm_{plan.id}",
                        width="stretch",
                    ):
                        service.delete_workout_plan(plan.id)
                        st.rerun()

            st.text(_plan_summary(plan))

            if st.button("Start Workout", key=f"start_{plan.id}", width="stretch"):
                workout = service.start_workout_from_plan(plan)
                st.session_state["logbook_template_workout"] = workout
                st.session_state["logbook_dialog_mode"] = "create_from_plan"
                st.session_state["logbook_dialog_nonce"] = str(uuid4())
                st.info(
                    "Workout form opened with plan data. Save it from the Logbook tab."
                )
                st.rerun()
