"""Exercise settings page."""

from __future__ import annotations

import streamlit as st

from falsegrip.models.enums import ExerciseCategory, ExerciseType
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.workout_service import WorkoutService
from falsegrip.components.dialogs import confirm_deletion


def render(repository: FalseGripRepository) -> None:
    """Render exercise definition management page."""
    service = WorkoutService(repository=repository)

    with st.expander("Add exercise", expanded=False):
        with st.form("exercise_settings_add_form"):
            name = st.text_input("Exercise name")
            category_options = [category.value for category in ExerciseCategory]
            category = st.selectbox("Category", options=category_options)
            exercise_type_options = [
                exercise_type.value for exercise_type in ExerciseType
            ]
            exercise_type = st.selectbox("Exercise type", options=exercise_type_options)
            submitted = st.form_submit_button("Save exercise", width="stretch")

            if submitted:
                normalized_name = name.strip()
                if not normalized_name:
                    st.warning("Exercise name is required.")
                else:
                    service.create_exercise_definition(
                        name=normalized_name,
                        category=ExerciseCategory(category),
                        exercise_type=ExerciseType(exercise_type),
                    )
                    st.success(f"Saved {normalized_name}.")
                    st.rerun()

    definitions = service.list_exercise_definitions()
    if not definitions:
        st.info("No exercises defined yet.")
        return

    for definition in definitions:
        with st.container(border=True):
            details_col, actions_col = st.columns([4, 1])
            with details_col:
                st.markdown(f"**{definition.name}**")
                st.caption(
                    f"{definition.category.value} • {definition.exercise_type.value}"
                )
            with actions_col:
                if st.button(
                    "Delete",
                    key=f"exercise_settings_delete_{definition.id}",
                    type="secondary",
                    width="stretch",
                ):

                    def do_delete(d_id=definition.id):
                        try:
                            service.delete_exercise_definition(d_id)
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))

                    confirm_deletion(
                        "Are you sure you want to delete this exercise? It will affect historical analytics.",
                        do_delete,
                    )
