"""Role selector for MVP demonstration."""
from __future__ import annotations

import streamlit as st

ROLES = ["Analyst", "Fact Checker", "Operations", "Communications", "Management"]

ROLE_SECTIONS = {
    "Analyst": ["detection", "prioritisation", "workflow"],
    "Fact Checker": ["evidence", "verification", "misinformation"],
    "Operations": ["local_action", "assignments"],
    "Communications": ["responses", "drafts", "approval"],
    "Management": ["executive_brief"],
}


def render_role_selector() -> str:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Peranan (Demo)")
    role = st.sidebar.selectbox(
        "Peranan pengguna",
        ROLES,
        index=ROLES.index(st.session_state.get("user_role", "Analyst")),
        help="Kawalan paparan MVP — bukan sistem pengesahan penuh.",
    )
    st.session_state["user_role"] = role
    return role


def role_can(role: str, section: str) -> bool:
    return section in ROLE_SECTIONS.get(role, [])
