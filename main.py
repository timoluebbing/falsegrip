"""Streamlit application entrypoint for FalseGrip."""

from __future__ import annotations

import streamlit as st

from falsegrip.pages import exercise_settings, graphs, logbook, settings, workout_plans
from falsegrip.repositories.factory import get_repository
from falsegrip.services.workout_service import WorkoutService
from falsegrip.components.auth import render_auth


def _get_repository():
    """Return a cached repository instance in session state."""
    # Never cache the repository if using supabase, as auth state changes
    from falsegrip.config import load_config

    if load_config().backend == "supabase":
        return get_repository()

    if "repository" not in st.session_state:
        st.session_state["repository"] = get_repository()
    return st.session_state["repository"]


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="FalseGrip", layout="centered")

    st.sidebar.title("FalseGrip")
    is_authenticated = render_auth()

    if not is_authenticated:
        st.info("Please log in to continue.")
        return

    repository = _get_repository()
    workout_service = WorkoutService(repository=repository)

    st.sidebar.divider()

    from falsegrip.config import load_config

    if load_config().backend == "sqlite":
        st.sidebar.info("Single-user local mode")

    if st.sidebar.button("Toggle Settings", width="stretch"):
        current = st.session_state.get("show_settings", False)
        st.session_state["show_settings"] = not current

    csv_content = workout_service.export_workouts_csv()
    st.sidebar.download_button(
        "Export CSV",
        data=csv_content,
        file_name="falsegrip-workouts.csv",
        mime="text/csv",
        width="stretch",
    )

    logbook_tab, plans_tab, graphs_tab, exercises_tab = st.tabs(
        ["Logbook", "Workout Plans", "Graphs", "Exercise Editor"]
    )

    with logbook_tab:
        logbook.render(repository)

    with plans_tab:
        workout_plans.render(repository)

    with graphs_tab:
        graphs.render(repository)

    with exercises_tab:
        exercise_settings.render(repository)

    if st.session_state.get("show_settings", False):
        st.divider()
        settings.render(repository)


if __name__ == "__main__":
    main()
