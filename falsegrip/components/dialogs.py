"""Reusable dialog components."""

import streamlit as st
from typing import Callable


@st.dialog("Confirm Deletion")
def confirm_deletion(
    warning_message: str,
    on_confirm: Callable[[], None],
    on_cancel: Callable[[], None] = lambda: None,
) -> None:
    st.warning(warning_message)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width="stretch"):
            on_cancel()
            st.rerun()
    with col2:
        if st.button("Delete", width="stretch", type="primary"):
            on_confirm()
            st.rerun()
