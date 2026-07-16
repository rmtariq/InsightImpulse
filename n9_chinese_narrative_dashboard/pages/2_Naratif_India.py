"""Naratif India — community-focused view."""
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

from components.negeri_selector import get_selected_negeri

init_dashboard("Naratif India", "Naratif India")
render_page_shell("Naratif India")

df, filtered, _ = load_dashboard_data()
sub = filter_community(filtered, "indian") if filtered is not None else None
selected = get_selected_negeri()

st.markdown(
    f'<div style="background:{GRADIENTS["indian"]};border-radius:12px;padding:14px 18px;margin-bottom:14px;border:1px solid #e9d5ff;">'
    f'<span class="badge badge-indian">🇮🇳 Naratif India</span> '
    f'<span style="color:#6b21a8;font-size:0.85rem;">Suara komuniti India — Tamil, media India, isu tempatan</span></div>',
    unsafe_allow_html=True,
)

if sub is None or sub.empty:
    all_ind = filter_community(df, "indian") if df is not None else None
    counts = {}
    if all_ind is not None and not all_ind.empty and "state" in all_ind.columns:
        counts = all_ind["state"].value_counts().to_dict()
    hint = ""
    if counts:
        parts = [f"{s}: {counts[s]:,}" for s in ("Negeri Sembilan", "Johor", "Melaka") if counts.get(s)]
        hint = f" Rekod India mengikut negeri — {' · '.join(parts)}. Pilih negeri lain di sidebar atau laraskan tarikh."
    empty_state(
        "🇮🇳", f"Tiada Naratif India untuk {selected}",
        f"Tiada hantaran komuniti India dalam penapis semasa ({selected}).{hint}",
    )
    # Show cross-community as fallback hint
    if filtered is not None and "community" in filtered.columns:
        cross = filter_community(filtered, "cross")
        if not cross.empty:
            st.info(f"💡 {len(cross)} rekod merentas komuniti (BM/EN) tersedia — mungkin relevan untuk konteks India.")
    st.stop()

k = compute_overview_kpis(sub)
render_kpi_row([
    ("📨", "Hantaran India", f"{k['total_posts']:,}", "Dalam tempoh", True),
    ("💬", "Interaksi", f"{k['total_engagement']:,}", "Engagement", False),
    ("😟", "Negatif", f"{k['pct_negative']}%", "Sentimen", False),
    ("⚠️", "Risiko", f"{k['high_risk']:,}", "Tinggi/kritikal", False),
])

c1, c2 = st.columns(2)
with c1:
    plotly_chart(sentiment_donut(sub, "Sentimen naratif India"))
    plotly_chart(issues_bar(sub, title="Isu panas komuniti India"))
with c2:
    plotly_chart(trend_line(sub, "Trend naratif India"))
    plotly_chart(platform_bar(sub, "Platform naratif India"))

st.markdown("#### 📋 Hantaran teratas")
show = st.session_state.get("show_translation_bm", True)
st.dataframe(
    posts_display_columns(sub.sort_values("engagement_total", ascending=False).head(15) if "engagement_total" in sub.columns else sub.head(15),
                          show_translation=show, extra=["platform", "sentiment", "district", "source_url"]),
    width="stretch", hide_index=True,
)
