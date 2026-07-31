"""Unified dashboard shell — premium colourful theme."""
from __future__ import annotations

import streamlit as st

from components.filters import render_sidebar_filters
from components.negeri_selector import get_selected_negeri, render_negeri_sidebar
from components.ui.cards import render_premium_header
from components.ui.styles import inject_premium_css
from utils.community import add_community_column
from utils.data_loader import get_data_source_label, load_posts, load_seed_list
from utils.ensure_templates import ensure_all_templates


PAGE_GUIDE = {
    "Ringkasan": "Mulai di sini — status, KPI, ringkasan eksekutif, carta utama",
    "Naratif Cina": "Suara & isu komuniti Cina — merah/rose theme",
    "Naratif India": "Suara & isu komuniti India — ungu/amber theme",
    "Peta Isu": "Hotspot daerah — peta interaktif isu & tindakan",
    "Pusat Tindakan": "Kanban + jadual tindakan + cadangan copy",
    "Data & Laporan": "Jadual hantaran + muat turun PDF/DOCX",
}


from utils.quiet_console import silence_console_noise


def init_dashboard(page_key: str, page_title: str):
    silence_console_noise()
    st.set_page_config(
        page_title=f"PRN Naratif — {page_title}",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    ensure_all_templates()
    dark = st.session_state.get("dark_mode", False)
    inject_premium_css(dark=dark)


def load_dashboard_data():
    try:
        df = load_posts()
        seed = load_seed_list()
    except Exception as exc:
        st.error(f"Ralat memuatkan data: {exc}")
        return None, None, None

    if df is not None and not df.empty:
        df = add_community_column(df)
        render_negeri_sidebar(df)

    st.sidebar.markdown("---")
    prev = st.session_state.get("dark_mode", False)
    dark = st.sidebar.toggle("🌙 Dark mode", value=prev)
    if dark != prev:
        st.session_state["dark_mode"] = dark
        st.rerun()
    st.session_state["dark_mode"] = dark

    filtered = render_sidebar_filters(df)
    if filtered is not None and not filtered.empty and "community" not in filtered.columns:
        filtered = add_community_column(filtered)

    st.sidebar.caption(f"📂 {get_data_source_label()}")
    st.sidebar.caption("⚠️ Bukan polling undi · semak manusia sebelum pos")
    return df, filtered, seed


def render_page_shell(page_key: str):
    negeri = get_selected_negeri()
    render_premium_header(negeri)
    hint = PAGE_GUIDE.get(page_key, "")
    if hint:
        st.markdown(f'<div class="nav-pill">📍 <b>{page_key}</b> — {hint}</div>', unsafe_allow_html=True)
