"""Authentication component for Supabase login."""

import streamlit as st
import supabase
from supabase import ClientOptions


def get_supabase_client():
    from falsegrip.config import load_config

    config = load_config()
    if config.supabase_url and config.supabase_key:
        return supabase.create_client(
            config.supabase_url,
            config.supabase_key,
            options=ClientOptions(persist_session=False),
        )
    return None


def render_auth() -> bool:
    """Render the authentication UI in the sidebar.
    Returns True if the user is authenticated (or using local mode)."""
    from falsegrip.config import load_config

    config = load_config()

    if config.backend != "supabase":
        # Bypass auth entirely for local SQLite
        return True

    client = get_supabase_client()
    if not client:
        st.sidebar.error("Supabase config missing.")
        return False

    if "supabase_session" not in st.session_state:
        st.session_state["supabase_session"] = None

    if st.session_state["supabase_session"] is not None:
        st.sidebar.success("Logged in")
        if st.sidebar.button("Logout", width="stretch"):
            try:
                client.auth.sign_out()
            except Exception:
                pass
            st.session_state["supabase_session"] = None
            st.rerun()
        return True

    st.sidebar.markdown("### Login")
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_password")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Login", width="stretch"):
            if not email or not password:
                st.sidebar.warning("Please provide email and password.")
            else:
                try:
                    res = client.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    if res.user:
                        st.session_state["supabase_session"] = res.session
                        st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Login failed: {e}")

    with col2:
        if st.button("Sign Up", width="stretch"):
            if not email or not password:
                st.sidebar.warning("Please provide email and password.")
            else:
                try:
                    res = client.auth.sign_up(
                        {
                            "email": email,
                            "password": password,
                            "options": {
                                "email_redirect_to": "http://localhost:8502"
                            },  # Currently disabled email confirmation in supabase settings
                        }
                    )
                    if res.user:
                        st.sidebar.success(
                            "Sign up successful, try logging in now (auto-confirmed)."
                        )
                except Exception as e:
                    st.sidebar.error(f"Sign up failed: {e}")

    return False
