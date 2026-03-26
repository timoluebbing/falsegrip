"""Graphs page renderer."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from falsegrip.models.enums import ExerciseType
from falsegrip.repositories.base import FalseGripRepository
from falsegrip.services.analytics_service import AnalyticsService
from falsegrip.services.workout_service import WorkoutService


def render(repository: FalseGripRepository) -> None:
    """Render the graphs page."""
    analytics_service = AnalyticsService(repository=repository)
    workout_service = WorkoutService(repository=repository)

    graph_type = st.selectbox(
        "Graph type",
        options=("Volume Progression", "Exercise Distribution"),
        index=0,
    )

    if graph_type == "Volume Progression":
        definitions = workout_service.list_exercise_definitions()
        if not definitions:
            st.info("No exercises available yet.")
            return

        available_types = sorted(
            {definition.exercise_type for definition in definitions},
            key=lambda exercise_type: exercise_type.value,
        )
        selected_type = st.selectbox(
            "Exercise type",
            options=available_types,
            format_func=lambda exercise_type: exercise_type.value,
        )

        filtered_definitions = [
            definition
            for definition in definitions
            if definition.exercise_type == selected_type
        ]
        if not filtered_definitions:
            st.info("No exercises available for this type yet.")
            return

        default_names = [definition.name for definition in filtered_definitions]
        selected_names = st.multiselect(
            "Exercises",
            options=default_names,
            default=default_names,
        )
        if not selected_names:
            st.info("Select at least one exercise.")
            return

        selected_definitions = [
            definition
            for definition in filtered_definitions
            if definition.name in selected_names
        ]
        selections = [
            (definition.id, definition.name) for definition in selected_definitions
        ]
        dataframe = analytics_service.multi_volume_progression_dataframe(
            selections=selections
        )
        if dataframe.empty:
            st.info("No volume data available for the selected exercises yet.")
            return

        y_label = "Progress"
        if selected_type == ExerciseType.WEIGHT_REPS:
            y_label = "kg"
        elif selected_type == ExerciseType.BODYWEIGHT_REPS:
            y_label = "total reps"
        else:
            y_label = "seconds"

        figure = px.line(
            dataframe,
            x="date",
            y="volume",
            color="exercise",
            markers=True,
            title=f"Volume Progression ({y_label})",
            labels={"volume": y_label, "date": "Date", "exercise": "Exercise"},
        )
        figure.update_traces(mode="lines+markers")
        st.plotly_chart(figure, width="stretch")
    else:
        category_dataframe = analytics_service.exercise_distribution_dataframe()
        if category_dataframe.empty:
            st.info("No exercise distribution data available yet.")
            return

        category_figure = px.pie(
            category_dataframe,
            names="category",
            values="count",
            title="Exercise Distribution by Category",
        )
        st.plotly_chart(category_figure, width="stretch")

        exercise_dataframe = analytics_service.exercise_name_distribution_dataframe()
        exercise_figure = px.pie(
            exercise_dataframe,
            names="exercise",
            values="count",
            title="Exercise Distribution by Exercise",
        )
        st.plotly_chart(exercise_figure, width="stretch")
