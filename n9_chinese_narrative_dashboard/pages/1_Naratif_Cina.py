"""Naratif Cina — community-focused view."""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from components.metrics import compute_overview_kpis
from utils.translator import posts_display_columns
from components.ui.cards import empty_state, render_kpi_row
from components.ui.charts import issues_bar, platform_bar, sentiment_donut, trend_line
from components.ui.design_tokens import GRADIENTS
from components.ui.styles import plotly_chart
from utils.community import filter_community

init_dashboard("Naratif Cina", "Naratif Cina")
render_page_shell("Naratif Cina")

df, filtered, _ = load_dashboard_data()
sub = filter_community(filtered, "chinese") if filtered is not None else None

st.markdown(
    f'<div style="background:{GRADIENTS["chinese"]};border-radius:12px;padding:14px 18px;margin-bottom:14px;border:1px solid #fecdd3;">'
    f'<span class="badge badge-chinese">🇨🇳 Naratif Cina</span> '
    f'<span style="color:#881337;font-size:0.85rem;">Suara komuniti Cina — media Cina, Facebook, komuniti</span></div>',
    unsafe_allow_html=True,
)

if sub is None or sub.empty:
    empty_state("🇨🇳", "Tiada Naratif Cina", "Data India/Umum mungkin dominan. Muatkan crawl media Cina atau laraskan penapis.")
    st.stop()

k = compute_overview_kpis(sub)
render_kpi_row([
    ("📨", "Hantaran Cina", f"{k['total_posts']:,}", "Dalam tempoh", True),
    ("💬", "Interaksi", f"{k['total_engagement']:,}", "Engagement", False),
    ("😟", "Negatif", f"{k['pct_negative']}%", "Sentimen", False),
    ("⚠️", "Risiko", f"{k['high_risk']:,}", "Tinggi/kritikal", False),
])

c1, c2 = st.columns(2)
with c1:
    plotly_chart(sentiment_donut(sub, "Sentimen naratif Cina"))
    plotly_chart(issues_bar(sub, title="Isu panas komuniti Cina"))
with c2:
    plotly_chart(trend_line(sub, "Trend naratif Cina"))
    plotly_chart(platform_bar(sub, "Platform naratif Cina"))

st.markdown("#### 📋 Hantaran teratas")
show = st.session_state.get("show_translation_bm", True)
st.dataframe(
    posts_display_columns(sub.sort_values("engagement_total", ascending=False).head(15) if "engagement_total" in sub.columns else sub.head(15),
                          show_translation=show, extra=["platform", "sentiment", "district", "source_url"]),
    width="stretch", hide_index=True,
)
