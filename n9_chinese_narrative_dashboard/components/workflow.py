"""Operational workflow and Kanban views."""
from __future__ import annotations

import streamlit as st

WORKFLOW_STEPS = [
    ("Detect", "Kesan"),
    ("Cluster", "Kluster"),
    ("Prioritise", "Utamakan"),
    ("Verify", "Sahkan"),
    ("Assign", "Tugaskan"),
    ("Respond or Act", "Balas/Tindak"),
    ("Record Evidence", "Rekod Bukti"),
    ("Monitor Impact", "Pantau Impak"),
    ("Close or Continue Monitoring", "Tutup/Pantau"),
]

KANBAN_COLUMNS = [
    "Baharu", "Dalam Semakan", "Perlu Pengesahan", "Tindakan Dirancang",
    "Sedang Dilaksanakan", "Selesai",
]


def render_workflow(actions_df, complaints_df, evidence_df):
    st.markdown("#### Aliran Kerja Operasi Harian")
    counts = {}
    if actions_df is not None and not actions_df.empty and "action_status" in actions_df.columns:
        status_map = {
            "Baharu": "Baharu",
            "Dalam Semakan": "Dalam Semakan",
            "Fakta Sedang Disahkan": "Perlu Pengesahan",
            "Tindakan Dirancang": "Tindakan Dirancang",
            "Sedang Dilaksanakan": "Sedang Dilaksanakan",
            "Selesai": "Selesai",
        }
        for s, c in actions_df["action_status"].value_counts().items():
            col = status_map.get(s, "Baharu")
            counts[col] = counts.get(col, 0) + c
    counts.setdefault("Detect", len(complaints_df) if complaints_df is not None else 0)
    counts.setdefault("Verify", len(evidence_df) if evidence_df is not None else 0)

    cols = st.columns(len(WORKFLOW_STEPS))
    for i, (en, bm) in enumerate(WORKFLOW_STEPS):
        n = counts.get(en, counts.get(bm, 0))
        with cols[i]:
            st.metric(bm, n)

    st.markdown("#### Paparan Kanban")
    kcols = st.columns(len(KANBAN_COLUMNS))
    for i, col_name in enumerate(KANBAN_COLUMNS):
        with kcols[i]:
            st.markdown(f"**{col_name}**")
            n = counts.get(col_name, 0)
            st.caption(f"{n} rekod")


def render_raci_table(action_id: str = "—"):
    st.markdown("#### Matriks Tanggungjawab (RACI)")
    raci = [
        {"Team": "Social Listening", "R": "●", "A": "", "C": "●", "I": ""},
        {"Team": "Data Analysis", "R": "●", "A": "", "C": "●", "I": ""},
        {"Team": "Fact Checking", "R": "", "A": "", "C": "●", "I": ""},
        {"Team": "Policy", "R": "", "A": "", "C": "●", "I": ""},
        {"Team": "Communications", "R": "●", "A": "", "C": "", "I": "●"},
        {"Team": "Local Operations", "R": "●", "A": "●", "C": "", "I": ""},
        {"Team": "Community Engagement", "R": "", "A": "", "C": "●", "I": ""},
        {"Team": "Legal Review", "R": "", "A": "", "C": "●", "I": ""},
        {"Team": "Management Approval", "R": "", "A": "●", "C": "", "I": "●"},
    ]
    import pandas as pd
    st.dataframe(pd.DataFrame(raci), width="stretch", hide_index=True)
    st.caption(f"Contoh untuk tindakan: {action_id}")
