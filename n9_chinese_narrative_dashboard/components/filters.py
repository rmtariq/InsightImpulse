"""Global sidebar filters — simplified for revamp."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

from components.negeri_selector import filter_by_negeri, get_selected_negeri


def _opts(series: pd.Series) -> list:
    if series is None or series.empty:
        return []
    vals = series.dropna().astype(str).unique().tolist()
    return sorted([v for v in vals if v and v.lower() not in ("nan", "none", "")])


def init_session_state():
    defaults = {"filters_reset": False, "filter_date_start": None, "filter_date_end": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = filter_by_negeri(df)
    f = st.session_state.get("active_filters", {})

    if f.get("date_start") and "published_at" in out.columns:
        ts = pd.to_datetime(out["published_at"], errors="coerce")
        start = pd.Timestamp(f["date_start"])
        out = out[ts.isna() | (ts >= start)]
    if f.get("date_end") and "published_at" in out.columns:
        ts = pd.to_datetime(out["published_at"], errors="coerce")
        end = pd.Timestamp(f["date_end"]) + pd.Timedelta(days=1)
        out = out[ts.isna() | (ts <= end)]

    mapping = {
        "platforms": "platform", "issues": "issue_cluster", "sentiments": "sentiment",
        "districts": "district", "risks": "risk_level",
        "languages": "language_detected", "duns": "dun_code",
        "parties": "party_mentioned",
    }
    for key, col in mapping.items():
        sel = f.get(key, [])
        if sel and col in out.columns:
            out = out[out[col].astype(str).isin(sel)]

    if f.get("misinformation_only") and "misinformation_flag" in out.columns:
        out = out[out["misinformation_flag"] == True]  # noqa: E712
    return out


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    init_session_state()
    negeri = get_selected_negeri()

    if df is None or df.empty:
        st.sidebar.warning("Tiada data.")
        return df

    df_negeri = filter_by_negeri(df)

    st.sidebar.markdown("### 🔍 Penapis Ringkas")

    min_d = df_negeri["published_at"].min() if "published_at" in df_negeri.columns and not df_negeri.empty else None
    max_d = df_negeri["published_at"].max() if "published_at" in df_negeri.columns and not df_negeri.empty else None
    if pd.notna(min_d) and pd.notna(max_d):
        d_val = st.sidebar.date_input("Tarikh", value=(min_d.date(), max_d.date()),
                                       min_value=min_d.date(), max_value=max_d.date())
        if isinstance(d_val, tuple) and len(d_val) == 2:
            date_start, date_end = d_val
        else:
            date_start, date_end = d_val, d_val
    else:
        date_start, date_end = None, None

    platforms = st.sidebar.multiselect("Platform", _opts(df_negeri.get("platform", pd.Series(dtype=str))))
    issues = st.sidebar.multiselect("Isu", _opts(df_negeri.get("issue_cluster", pd.Series(dtype=str))))
    sentiments = st.sidebar.multiselect("Sentimen", _opts(df_negeri.get("sentiment", pd.Series(dtype=str))))
    districts = st.sidebar.multiselect("Daerah", _opts(df_negeri.get("district", pd.Series(dtype=str))))

    languages: list = []
    duns: list = []
    risks: list = []
    parties: list = []
    misinformation_only = False
    show_translation_bm = True
    auto_translate_bm = True

    with st.sidebar.expander("Penapis Lanjutan"):
        languages = st.multiselect("Bahasa", _opts(df_negeri.get("language_detected", pd.Series(dtype=str))))
        duns = st.multiselect("DUN", _opts(df_negeri.get("dun_code", pd.Series(dtype=str))))
        risks = st.multiselect("Risiko", _opts(df_negeri.get("risk_level", pd.Series(dtype=str))))
        parties = st.multiselect("Parti", _opts(df_negeri.get("party_mentioned", pd.Series(dtype=str))))
        misinformation_only = st.checkbox("Hanya maklumat salah")
        show_translation_bm = st.checkbox("Papar terjemahan BM", value=True)
        auto_translate_bm = st.checkbox("Auto-terjemah → BM", value=True)
        if st.button("Reset penapis", width="stretch"):
            st.session_state["active_filters"] = {}
            st.rerun()

    st.session_state["active_filters"] = {
        "date_start": date_start, "date_end": date_end,
        "platforms": platforms, "issues": issues, "sentiments": sentiments,
        "districts": districts, "languages": languages, "duns": duns,
        "risks": risks, "parties": parties, "misinformation_only": misinformation_only,
    }
    st.session_state["show_translation_bm"] = show_translation_bm
    st.session_state["auto_translate_bm"] = auto_translate_bm

    filtered = apply_filters(df)
    from utils.translator import enrich_translations
    filtered = enrich_translations(filtered, auto_translate=auto_translate_bm, max_auto=200)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{len(filtered):,}** rekod · {negeri}")

    slug = negeri.lower().replace(" ", "_")
    st.sidebar.download_button(
        "⬇️ CSV", data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"prn_{slug}.csv", mime="text/csv", width="stretch",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 Laporan")
    if st.sidebar.button("Jana Eksekutif + Kit Respons", width="stretch", type="primary"):
        try:
            from utils.state_report_generator import generate_state_reports
            paths = generate_state_reports(df, states=[negeri], executive=True, response_kit=True, appendix=False)
            p = paths.get(negeri, {})
            st.sidebar.success("Siap!")
            if p.get("executive_pdf"):
                st.sidebar.caption(f"📊 {p['executive_pdf'].split('/')[-1]}")
            if p.get("response_kit_pdf"):
                st.sidebar.caption(f"💬 {p['response_kit_pdf'].split('/')[-1]}")
        except Exception as exc:
            st.sidebar.error(str(exc)[:120])

    if st.sidebar.button("🔄 Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    with st.sidebar.expander("🔧 Penyelenggaraan"):
        if st.button("Bina semula dataset", width="stretch"):
            from utils.build_dataset import build_dataset
            build_dataset()
            st.cache_data.clear()
            st.rerun()

    return filtered
