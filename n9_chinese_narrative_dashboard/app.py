"""
PRN — Dashboard Pemantauan Naratif Komuniti
Halaman 1: Ringkasan Eksekutif
"""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from components.metrics import compute_overview_kpis
from components.negeri_selector import get_selected_negeri
from components.ui.cards import empty_state, render_community_chips, render_executive_summary, render_kpi_row, status_from_kpis, badge_html
from components.ui.charts import district_bar, issues_bar, platform_bar, sentiment_donut, trend_line
from components.ui.styles import plotly_chart
from utils.community import COMMUNITY_LABELS

init_dashboard("Ringkasan", "Ringkasan")
render_page_shell("Ringkasan")

df, filtered, _ = load_dashboard_data()
if filtered is None or filtered.empty:
    empty_state("📊", "Tiada Data", "Pilih negeri lain atau muatkan crawl terkini.")
    st.stop()

k = compute_overview_kpis(filtered)
code, _ = status_from_kpis(k)
comm_counts = filtered["community"].value_counts().to_dict() if "community" in filtered.columns else {}

render_community_chips(comm_counts)
render_executive_summary(filtered, k)

if st.session_state.pop("trigger_report", False):
    from utils.state_report_generator import generate_state_reports
    negeri = get_selected_negeri()
    with st.spinner("Menjana laporan…"):
        generate_state_reports(df, states=[negeri], executive=True, response_kit=True, appendix=False)
    st.success("Laporan dijana — lihat sidebar atau Data & Laporan")

st.markdown(f'<div style="margin:12px 0;">Status keseluruhan: {badge_html(code)}</div>', unsafe_allow_html=True)

render_kpi_row([
    ("📨", "Jumlah Hantaran", f"{k['total_posts']:,}", "Rekod dipantau", True),
    ("💬", "Interaksi", f"{k['total_engagement']:,}", "Jumlah engagement", False),
    ("😟", "Sentimen Negatif", f"{k['pct_negative']}%", f"Positif {k['pct_positive']}%", False),
    ("⚠️", "Risiko Tinggi", f"{k['high_risk']:,}", "Perlu semakan", False),
    ("🚫", "Maklumat Salah", f"{k['misinfo']:,}", "Fact check", False),
    ("📡", "Sumber Aktif", f"{k['active_sources']:,}", "Akaun unik", False),
])

c1, c2 = st.columns(2)
with c1:
    plotly_chart(sentiment_donut(filtered))
    plotly_chart(issues_bar(filtered))
with c2:
    plotly_chart(trend_line(filtered))
    plotly_chart(platform_bar(filtered))

plotly_chart(district_bar(filtered))
