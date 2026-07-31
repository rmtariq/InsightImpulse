"""Action Center — table + kanban views."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui.design_tokens import PRIORITY_COLORS
from utils.reporting.response_kit_payload import build_response_kit_payload
from utils.state_report_generator import STATE_META


KANBAN_COLUMNS = [
    ("Belum Bermula", ["Baharu", ""]),
    ("Sedang Dilaksanakan", ["Sedang Dilaksanakan", "Dalam Semakan"]),
    ("Menunggu Maklum Balas", ["Menunggu Kelulusan", "Fakta Sedang Disahkan"]),
    ("Selesai", ["Selesai"]),
]


def _prio_class(row) -> str:
    score = float(row.get("priority_score", 0) or 0)
    if score >= 0.75:
        return "p1"
    if score >= 0.5:
        return "p2"
    return "p3"


def render_table_view(actions: pd.DataFrame):
    if actions.empty:
        return
    show = [c for c in [
        "issue_cluster", "location", "platform", "negative_percentage", "priority_score",
        "recommended_action", "responsible_team", "due_date", "action_status",
    ] if c in actions.columns]
    st.dataframe(actions[show].head(20), width="stretch", hide_index=True)


def render_kanban_view(actions: pd.DataFrame):
    if actions.empty:
        st.info("Tiada tindakan.")
        return
    cols = st.columns(4)
    for col, (title, statuses) in zip(cols, KANBAN_COLUMNS):
        with col:
            st.markdown(f"**{title}**")
            st.markdown(f'<div class="kanban-col">', unsafe_allow_html=True)
            sub = actions[actions["action_status"].astype(str).isin(statuses)] if statuses != [""] else actions.head(0)
            if statuses == [""]:
                sub = actions[~actions["action_status"].astype(str).isin(
                    [s for _, sts in KANBAN_COLUMNS for s in sts if s])].head(5)
            else:
                sub = actions[actions["action_status"].astype(str).isin(statuses)].head(5)
            for _, row in sub.iterrows():
                pc = _prio_class(row)
                prog = min(int(float(row.get("priority_score", 0.5) or 0.5) * 100), 100)
                st.markdown(
                    f"""
<div class="kanban-card {pc}">
  <div class="kanban-title">{row.get('issue_cluster', '—')}</div>
  <div class="kanban-meta">📍 {row.get('location', '—')} · {row.get('platform', '—')}</div>
  <div class="kanban-meta">👤 {row.get('responsible_team', '—')} · 📅 {row.get('due_date', '—')}</div>
  <div class="progress-bar"><div class="progress-fill" style="width:{prog}%;"></div></div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


def render_copy_panel(item: dict | None):
    if not item:
        return
    st.markdown('<div class="copy-panel">', unsafe_allow_html=True)
    st.markdown(f"### ✍️ Cadangan Posting — {item.get('issue', '')}")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Platform:** {', '.join(p['platform'] for p in item.get('platforms', [])[:2])}")
    c2.markdown("**Bahasa:** BM + 中文")
    c3.markdown(f"**Prioriti:** {item.get('priority', '—')}")

    st.markdown("**Copy BM (post ringkas)**")
    st.markdown(f'<div class="copy-block">{item.get("copy_bm_social", "")}</div>', unsafe_allow_html=True)
    if st.button("📋 Copy BM", key=f"copy_bm_{item.get('rank', 0)}"):
        st.code(item.get("copy_bm_social", ""))

    st.markdown("**Copy 中文**")
    st.markdown(f'<div class="copy-block">{item.get("copy_zh_social", "")}</div>', unsafe_allow_html=True)

    cp = item.get("counter_plan") or {}
    st.markdown("**CTA / Hashtag**")
    st.markdown(f"`{' '.join(item.get('hashtags', []))}`")

    st.markdown("**Langkah edar**")
    for i, step in enumerate(cp.get("steps") or [], 1):
        st.markdown(f"{i}. {step}")

    st.markdown("**JANGAN:** " + cp.get("dont", "—"))
    st.markdown("</div>", unsafe_allow_html=True)


def get_kit_items(df, state: str) -> list[dict]:
    meta = STATE_META.get(state, {"short": state, "slug": "x"})
    payload = build_response_kit_payload(df, state, meta)
    return payload.get("items") or []
