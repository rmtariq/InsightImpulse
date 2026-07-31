"""Peta Isu — interactive hotspot map."""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from components.ui.cards import empty_state
from components.ui.map_view import action_map, build_map_df, issue_map
from components.ui.styles import plotly_chart
from utils.action_engine import build_action_candidates
from utils.ensure_templates import merge_actions

init_dashboard("Peta Isu", "Peta Isu")
render_page_shell("Peta Isu")

df, filtered, _ = load_dashboard_data()
if filtered is None or filtered.empty:
    empty_state("🗺️", "Tiada Data Peta", "Muatkan data dengan maklumat daerah.")
    st.stop()

view = st.radio("Paparan peta", ["🗺️ Peta Isu", "✅ Peta Tindakan"], horizontal=True)
actions = merge_actions(build_action_candidates(filtered))

if view.startswith("🗺️"):
    fig = issue_map(filtered, "Peta Hotspot Isu — klik marker untuk butiran")
else:
    fig = action_map(filtered, actions, "Peta Tindakan — lokasi dengan tindakan")

if fig:
    plotly_chart(fig)
else:
    empty_state("📍", "Peta Tidak Tersedia", "Tiada koordinat daerah untuk negeri ini.")

st.markdown("#### Legenda")
c1, c2, c3, c4 = st.columns(4)
c1.markdown("🟢 **Stabil** — sentimen negatif rendah")
c2.markdown("🟡 **Perhatian** — sentimen sederhana")
c3.markdown("🟠 **Tindakan** — negatif tinggi")
c4.markdown("🔴 **Kritikal** — risiko tinggi")

mdf = build_map_df(filtered)
if not mdf.empty:
    st.markdown("#### Senarai hotspot")
    st.dataframe(
        mdf[["location", "count", "neg_pct", "high_risk", "top_issue", "community"]].sort_values("count", ascending=False),
        width="stretch", hide_index=True,
    )

    sel = st.selectbox("Pilih lokasi untuk butiran", mdf["location"].tolist())
    row = mdf[mdf["location"] == sel].iloc[0]
    st.markdown(
        f"""
<div class="copy-panel">
  <b>{row['location']}</b> · {row['count']} hantaran · {row['neg_pct']}% negatif<br>
  Isu utama: <b>{row['top_issue']}</b> · Komuniti: {row['community']}<br>
  → Buka <b>Pusat Tindakan</b> untuk cadangan copy dan tindakan setempat.
</div>
        """,
        unsafe_allow_html=True,
    )
