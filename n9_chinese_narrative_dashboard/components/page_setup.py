"""Shared page setup — delegates to dashboard_shell."""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from utils.data_loader import get_quality_report


def configure_page(title: str = "PRN Naratif Cina", page_key: str = "Ringkasan"):
    init_dashboard(page_key, title)
    render_page_shell(page_key)


def render_header(page_key: str = "Ringkasan"):
    render_page_shell(page_key)


def load_filtered_data():
    return load_dashboard_data()


def get_user_role() -> str:
    return st.session_state.get("user_role", "Analyst")


def render_data_quality(df):
    if df is None or df.empty:
        return
    q = get_quality_report(df)
    with st.expander("📋 Kualiti Data"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tiada sentimen", q.get("missing_sentiment", 0))
        c2.metric("URL tidak sah", q.get("invalid_urls", 0))
        c3.metric("Tiada lokasi", q.get("missing_location", 0))
        c4.metric("Tiada teks", q.get("missing_post_text", 0))
