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
        options=("Workout Frequency", "Volume Progression", "Exercise Distribution"),
        index=0,
    )

    if graph_type == "Workout Frequency":
        period = st.selectbox("Period", options=("week", "month"), index=0)
        dataframe = analytics_service.workout_frequency_dataframe(period=period)
        if dataframe.empty:
            st.info("No workout data available yet.")
            return
        figure = px.bar(dataframe, x="period", y="count", title="Workout Frequency")
        st.plotly_chart(figure, width="stretch")
    elif graph_type == "Volume Progression":
        definitions = workout_service.list_exercise_definitions()
        if not definitions:
            st.info("No exercises available yet.")
            return

        definitions_by_name = {
            definition.name: definition for definition in definitions
        }
        selected_name = st.selectbox(
            "Exercise", options=list(definitions_by_name.keys())
        )
        selected_definition = definitions_by_name[selected_name]
        dataframe = analytics_service.volume_progression_dataframe(
            exercise_definition_id=selected_definition.id,
        )
        if dataframe.empty:
            st.info("No volume data available for this exercise yet.")
            return

        y_label = "Progress"
        if selected_definition.exercise_type == ExerciseType.WEIGHT_REPS:
            y_label = "kg"
        elif selected_definition.exercise_type == ExerciseType.BODYWEIGHT_REPS:
            y_label = "total reps"
        else:
            y_label = "seconds"

        figure = px.bar(
            dataframe,
            x="date",
            y="volume",
            title=f"Volume Progression ({y_label})",
            labels={"volume": y_label, "date": "Date"},
        )
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
