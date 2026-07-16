"""AMBANG-style single-screen executive dashboard."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ambang_theme import apply_plotly_dark, inject_ambang_css, plotly_chart
from components.metrics import compute_overview_kpis
from utils.reporting.labels import normalize_issue, UNCLASSIFIED


def _status_badge(k: dict) -> tuple[str, str, str]:
    p1 = k.get("high_risk", 0) >= 5 or k.get("misinfo", 0) >= 3
    neg = k.get("pct_negative", 0)
    if p1 or neg >= 45:
        return "MERAH", "status-merah", "Keutamaan tinggi — tindakan segera"
    if neg >= 35 or k.get("high_risk", 0) >= 2:
        return "JINGGA", "status-jingga", "Perlu tindakan dalam 24–48 jam"
    if neg >= 25:
        return "KUNING", "status-kuning", "Pantau rapat"
    return "HIJAU", "status-hijau", "Stabil — teruskan pemantauan"


def _kpi_card(label: str, value: str, meta: str = "", css_class: str = "") -> str:
    vc = f"kpi-value {css_class}".strip()
    return f"""
<div class="kpi-card">
  <p class="kpi-label">{label}</p>
  <p class="{vc}">{value}</p>
  <p class="kpi-meta">{meta}</p>
</div>"""


def _sourced_facts(df: pd.DataFrame, k: dict, state: str) -> list[tuple[str, str]]:
    facts: list[tuple[str, str]] = []
    if df.empty:
        return [("Tiada data dalam tempoh dipilih.", "—")]

    if "issue_cluster" in df.columns:
        top = df["issue_cluster"].apply(normalize_issue).value_counts()
        top = top[top.index != UNCLASSIFIED]
        if len(top):
            iss, cnt = top.index[0], int(top.iloc[0])
            neg = 0.0
            sub = df[df["issue_cluster"].apply(normalize_issue) == iss]
            if "sentiment" in sub.columns:
                neg = (sub["sentiment"].astype(str).str.lower() == "negative").mean() * 100
            facts.append((
                f"Isu paling banyak dibincang: **{iss}** ({cnt} hantaran, {neg:.0f}% negatif).",
                "InsightPulse · crawl",
            ))

    uncl = 0.0
    if "issue_cluster" in df.columns:
        uncl = (df["issue_cluster"].apply(normalize_issue) == UNCLASSIFIED).mean() * 100
    if uncl > 15:
        facts.append((
            f"{uncl:.0f}% rekod belum diklasifikasikan — tafsir isu perlu berhati-hati.",
            "Kualiti data",
        ))

    if k.get("misinfo", 0) > 0:
        facts.append((
            f"{k['misinfo']} hantaran ditanda maklumat salah disyaki — wajib fact check sebelum respons.",
            "Risk engine",
        ))

    if "platform" in df.columns:
        plat = df["platform"].value_counts().index[0]
        facts.append((
            f"Saluran dominan: **{plat}** — fokus edar respons di platform ini.",
            state,
        ))

    if k.get("pct_negative", 0) >= 35:
        facts.append((
            f"Sentimen negatif {k['pct_negative']}% — dominasi naratif dengan bukti & tindakan, bukan debat.",
            "Sentimen",
        ))

    return facts[:5]


def _district_chart(df: pd.DataFrame, state: str):
    col = "district" if "district" in df.columns else "constituency"
    if df.empty or col not in df.columns:
        return None
    g = df.groupby(col).agg(
        count=(col, "count"),
        neg=("sentiment", lambda s: (s.astype(str).str.lower() == "negative").mean() * 100 if len(s) else 0),
    ).reset_index()
    g = g[g[col].astype(str).str.len() > 0]
    g = g.sort_values("count", ascending=False).head(12)
    if g.empty:
        return None
    fig = px.bar(
        g, x="count", y=col, orientation="h",
        color="neg", color_continuous_scale=["#1e3a5f", "#38bdf8", "#fb923c", "#ef4444"],
        title=f"Naratif Cina — Ikut Daerah ({state})",
        labels={"count": "Hantaran", col: "Daerah", "neg": "% Negatif"},
    )
    fig.update_layout(coloraxis_colorbar=dict(title="% Neg", len=0.5))
    return apply_plotly_dark(fig)


def _issue_chart(df: pd.DataFrame):
    if df.empty or "issue_cluster" not in df.columns:
        return None
    s = df["issue_cluster"].apply(normalize_issue)
    s = s[s != UNCLASSIFIED]
    c = s.value_counts().head(10).reset_index()
    c.columns = ["issue", "count"]
    if c.empty:
        return None
    fig = px.bar(
        c, x="count", y="issue", orientation="h",
        title="Isu Utama (tanpa Belum Diklasifikasikan)",
        color="count", color_continuous_scale=["#334155", "#fb923c"],
    )
    return apply_plotly_dark(fig)


def _platform_donut(df: pd.DataFrame):
    if df.empty or "platform" not in df.columns:
        return None
    c = df["platform"].value_counts().head(6).reset_index()
    c.columns = ["platform", "count"]
    fig = px.pie(c, names="platform", values="count", hole=0.55, title="Komposisi Platform")
    return apply_plotly_dark(fig)


def _sentiment_donut(df: pd.DataFrame):
    if df.empty or "sentiment" not in df.columns:
        return None
    s = df["sentiment"].astype(str).str.lower()
    s = s[s.isin(["positive", "neutral", "negative"])]
    if s.empty:
        return None
    c = s.value_counts().reset_index()
    c.columns = ["sentiment", "count"]
    colors = {"positive": "#4ade80", "neutral": "#94a3b8", "negative": "#f87171"}
    fig = go.Figure(data=[go.Pie(
        labels=c["sentiment"], values=c["count"], hole=0.55,
        marker=dict(colors=[colors.get(x, "#64748b") for x in c["sentiment"]]),
    )])
    fig.update_layout(title="Komposisi Sentimen")
    return apply_plotly_dark(fig)


def render_ambang_header(state: str, k: dict):
    now = datetime.now()
    code, css, note = _status_badge(k)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            f"""
<div class="ambang-header">
  <p class="ambang-title">NARATIF CINA PRN</p>
  <p class="ambang-sub">Pemantauan naratif berbahasa Cina · {state}</p>
  <span class="status-badge {css}">{code}</span>
  <span style="font-size:0.78rem;color:#94a3b8;">{note}</span>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
<div class="ambang-header">
  <p class="ambang-clock">{now:%H:%M:%S}</p>
  <p class="ambang-date">{now:%A, %d %B %Y}</p>
</div>
            """,
            unsafe_allow_html=True,
        )


def render_ambang_dashboard(df: pd.DataFrame, state: str):
    """Single-screen layout inspired by AMBANG NEGARA."""
    inject_ambang_css()

    if df.empty:
        st.warning("Tiada rekod untuk negeri ini. Laraskan penapis atau muatkan crawl terkini.")
        return

    k = compute_overview_kpis(df)
    render_ambang_header(state, k)

    left, center, right = st.columns([1.05, 1.6, 1.05])

    with left:
        st.markdown(
            _kpi_card("Jumlah Hantaran", f"{k['total_posts']:,}", "Rekod naratif Cina", "teal")
            + _kpi_card("Jumlah Interaksi", f"{k['total_engagement']:,}", "Engagement direkod")
            + _kpi_card("Sentimen Negatif", f"{k['pct_negative']}%", f"Positif {k['pct_positive']}% · Neutral {k['pct_neutral']}%", "red")
            + _kpi_card("Risiko Tinggi / Kritikal", f"{k['high_risk']:,}", "Perlu semakan")
            + _kpi_card("Maklumat Salah Disyaki", f"{k['misinfo']:,}", "Fact check wajib")
            + _kpi_card("Sumber Aktif", f"{k['active_sources']:,}", "Akaun unik"),
            unsafe_allow_html=True,
        )

    with center:
        fig_d = _district_chart(df, state)
        if fig_d:
            plotly_chart(fig_d)
        else:
            st.markdown('<div class="panel"><p class="panel-title">Peta Daerah</p><p class="fact-item">Tiada data lokasi.</p></div>', unsafe_allow_html=True)
        st.caption("Warna bar = % sentimen negatif · Klik sidebar Analisis Kawasan untuk perincian DUN")

    with right:
        facts = _sourced_facts(df, k, state)
        html = '<div class="panel"><p class="panel-title">Fakta Bersumber</p>'
        for text, src in facts:
            html += f'<p class="fact-item">• {text}<br><span class="fact-src">{src}</span></p>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

        c_a, c_b = st.columns(2)
        with c_a:
            fig_s = _sentiment_donut(df)
            if fig_s:
                plotly_chart(fig_s)
        with c_b:
            fig_p = _platform_donut(df)
            if fig_p:
                plotly_chart(fig_p)

    # ── Row 2: Bottom charts ──
    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        fig_i = _issue_chart(df)
        if fig_i:
            plotly_chart(fig_i)
    with b2:
        if "platform" in df.columns:
            c = df["platform"].value_counts().head(8).reset_index()
            c.columns = ["platform", "count"]
            fig_pb = px.bar(
                c, x="count", y="platform", orientation="h",
                title="Naratif Mengikut Platform",
                color="count", color_continuous_scale=["#1e293b", "#38bdf8"],
            )
            st.plotly_chart(apply_plotly_dark(fig_pb), width="stretch", config={"displayModeBar": False, "responsive": True})

    # Quick nav
    st.markdown(
        """
<div class="panel" style="margin-top:8px;">
  <p class="panel-title">Tindakan Pantas</p>
  <p class="fact-item">
  📄 Jana laporan (sidebar) · 🎯 Tindakan Strategik · 💬 Pusat Tindak Balas · 📍 Analisis Kawasan
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
