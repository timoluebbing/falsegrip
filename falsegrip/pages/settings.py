"""Settings page renderer."""

from __future__ import annotations

import streamlit as st

from falsegrip.config import load_config
from falsegrip.repositories.base import FalseGripRepository


def render(repository: FalseGripRepository) -> None:
    """Render the settings page."""
    _ = repository
    config = load_config()

    st.title("Settings")
    st.subheader("Runtime")
    st.write(f"Backend: {config.backend}")
    st.write(f"SQLite file: {config.sqlite_path}")

    st.subheader("Account")
    st.info("Single-user local mode is active. Multi-user auth will be added later.")
