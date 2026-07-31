"""Data & Laporan — raw data + report generation."""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from components.negeri_selector import get_selected_negeri
from components.page_setup import render_data_quality
from utils.translator import posts_display_columns
from components.ui.cards import empty_state
from utils.state_report_generator import DEFAULT_OUT, generate_state_reports

init_dashboard("Data & Laporan", "Data & Laporan")
render_page_shell("Data & Laporan")

df, filtered, seed = load_dashboard_data()
if df is None:
    st.stop()

render_data_quality(df)

tab1, tab2 = st.tabs(["📋 Senarai Hantaran", "📄 Jana Laporan"])

with tab1:
    if filtered is None or filtered.empty:
        empty_state("📋", "Tiada Data", "Laraskan penapis.")
    else:
        q = st.text_input("🔍 Carian")
        sub = filtered.copy()
        if q:
            mask = sub["post_text"].astype(str).str.contains(q, case=False, na=False)
            if "translated_text_bm" in sub.columns:
                mask = mask | sub["translated_text_bm"].astype(str).str.contains(q, case=False, na=False)
            sub = sub[mask]
        sort = st.selectbox("Susun", ["engagement_total", "published_at"], index=0)
        if sort in sub.columns:
            sub = sub.sort_values(sort, ascending=False)
        show = st.session_state.get("show_translation_bm", True)
        st.dataframe(posts_display_columns(sub.head(100), show_translation=show), width="stretch", hide_index=True)
        st.caption(f"{len(sub):,} rekod · muat turun CSV dari sidebar")

with tab2:
    negeri = get_selected_negeri()
    st.markdown(
        f"""
<div class="exec-card">
  <h3>📄 Laporan Tersedia</h3>
  <p><b>Eksekutif</b> — 4 ms KPI + isu + tindakan<br>
  <b>Kit Respons</b> — copy BM/中文 + platform + naratif balas<br>
  📁 <code>{DEFAULT_OUT}</code></p>
</div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Jana Eksekutif + Kit Respons", type="primary", width="stretch"):
            with st.spinner("Menjana…"):
                paths = generate_state_reports(df, states=[negeri], executive=True, response_kit=True, appendix=False)
                p = paths.get(negeri, {})
                st.success("Selesai!")
                if p.get("executive_pdf"):
                    st.code(p["executive_pdf"])
                if p.get("response_kit_pdf"):
                    st.code(p["response_kit_pdf"])
    with c2:
        if st.button("Jana 3 negeri", width="stretch"):
            with st.spinner("Menjana…"):
                generate_state_reports(df, executive=True, response_kit=True, appendix=False)
            st.success("Semua negeri dijana.")

    if seed is not None and not seed.empty:
        with st.expander("Seed crawler"):
            st.dataframe(seed.head(30), width="stretch")
