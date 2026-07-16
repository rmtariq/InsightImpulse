"""Negeri selector — sidebar only, satu negeri aktif."""
from __future__ import annotations

import streamlit as st

NEGERI_ORDER = ["Negeri Sembilan", "Johor", "Melaka"]
NEGERI_SHORT = {
    "Negeri Sembilan": "N9",
    "Johor": "Johor",
    "Melaka": "Melaka",
}


def _counts(df) -> dict[str, int]:
    if df is None or df.empty or "state" not in df.columns:
        return {n: 0 for n in NEGERI_ORDER}
    vc = df["state"].astype(str).value_counts()
    return {n: int(vc.get(n, 0)) for n in NEGERI_ORDER}


def init_negeri_state():
    if "selected_negeri" not in st.session_state:
        st.session_state.selected_negeri = NEGERI_ORDER[0]


def get_selected_negeri() -> str:
    init_negeri_state()
    sel = st.session_state.get("selected_negeri", NEGERI_ORDER[0])
    return sel if sel in NEGERI_ORDER else NEGERI_ORDER[0]


def render_negeri_sidebar(df) -> str:
    """Compact negeri picker — sidebar only."""
    init_negeri_state()
    counts = _counts(df)
    current = get_selected_negeri()

    st.sidebar.markdown("### 🗺️ Pilih Negeri")
    st.sidebar.caption("Satu negeri pada satu masa — data tidak dicampur")

    for negeri in NEGERI_ORDER:
        short = NEGERI_SHORT[negeri]
        is_active = negeri == current
        if st.sidebar.button(
            f"{'● ' if is_active else ''}{short} — {counts[negeri]:,} rekod",
            key=f"negeri_btn_{negeri}",
            type="primary" if is_active else "secondary",
            width="stretch",
        ):
            if not is_active:
                st.session_state.selected_negeri = negeri
                st.rerun()

    st.sidebar.markdown(f"**Aktif:** {current}")
    st.sidebar.markdown("---")
    return current


def filter_by_negeri(df, negeri: str | None = None):
    if df is None or df.empty or "state" not in df.columns:
        return df
    n = negeri or get_selected_negeri()
    return df[df["state"].astype(str) == n].copy()


# Legacy — no-op on main area (revamp: sidebar only)
def render_negeri_selector(df) -> str:
    return get_selected_negeri()
