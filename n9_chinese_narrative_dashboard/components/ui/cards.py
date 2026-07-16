"""Reusable UI components — cards, badges, header."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from components.metrics import compute_overview_kpis, generate_executive_summary_bm
from components.ui.design_tokens import GRADIENTS, STATUS_BADGE


def status_from_kpis(k: dict) -> tuple[str, str]:
    if k.get("high_risk", 0) >= 5 or k.get("misinfo", 0) >= 3 or k.get("pct_negative", 0) >= 45:
        return "MERAH", "Keutamaan tinggi — tindakan segera diperlukan"
    if k.get("pct_negative", 0) >= 35 or k.get("high_risk", 0) >= 2:
        return "JINGGA", "Perlu tindakan dalam 24–48 jam"
    if k.get("pct_negative", 0) >= 25:
        return "KUNING", "Pantau rapat — trend meningkat"
    return "HIJAU", "Stabil — teruskan pemantauan"


def badge_html(code: str) -> str:
    label, css = STATUS_BADGE.get(code, (code, "badge-neutral"))
    return f'<span class="badge {css}">{label}</span>'


def render_premium_header(state: str, data_updated: str = ""):
    now = datetime.now()
    updated = data_updated or now.strftime("%d %b %Y, %H:%M")
    st.markdown(
        f"""
<div class="premium-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>Dashboard Pemantauan Naratif Komuniti Cina &amp; India</h1>
      <p>Pemantauan isu, sentimen, lokasi dan rancangan tindakan · <b>{state}</b></p>
    </div>
    <div style="text-align:right;">
      <div class="meta">🕐 {now:%H:%M:%S} · {now:%A, %d %b %Y}</div>
      <div class="meta">📅 Data dikemas kini: {updated}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(items: list[tuple[str, str, str, str, bool]]):
    """(icon, label, value, sub, gradient)"""
    cols = st.columns(len(items))
    for col, (icon, label, value, sub, grad) in zip(cols, items):
        gclass = " gradient" if grad else ""
        with col:
            st.markdown(
                f"""
<div class="kpi-card-v2{gclass}">
  <div class="icon">{icon}</div>
  <div class="label">{label}</div>
  <div class="value">{value}</div>
  <div class="sub">{sub}</div>
</div>
                """,
                unsafe_allow_html=True,
            )


def render_executive_summary(df, k: dict | None = None, actions: list[str] | None = None):
    k = k or compute_overview_kpis(df)
    code, note = status_from_kpis(k)
    summary = generate_executive_summary_bm(df)
    highlights = actions or [
        f"Isu utama: semak halaman Isu & Tindakan",
        f"{k.get('high_risk', 0)} risiko tinggi — sahkan bukti",
        "Jana Kit Respons untuk copy siap pos",
    ]
    hl_html = "".join(f'<div class="exec-highlight">→ {h}</div>' for h in highlights[:3])
    st.markdown(
        f"""
<div class="exec-card">
  <h3>💡 Ringkasan Eksekutif {badge_html(code)}</h3>
  <p>{summary}</p>
  <p style="font-size:0.82rem;color:#64748b !important;margin-top:8px;">{note}</p>
  {hl_html}
</div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 Lihat Pusat Tindakan", width="stretch", type="primary"):
            st.switch_page("pages/4_Pusat_Tindakan.py")
    with c2:
        if st.button("📄 Jana Laporan", width="stretch"):
            st.session_state["trigger_report"] = True


def render_community_chips(counts: dict[str, int]):
    chips = {
        "chinese": ("badge-chinese", "🇨🇳 Naratif Cina", GRADIENTS["chinese"]),
        "indian": ("badge-indian", "🇮🇳 Naratif India", GRADIENTS["indian"]),
        "cross": ("badge-cross", "🔗 Merentas Komuniti", GRADIENTS["cross"]),
        "general": ("badge-neutral", "📊 Umum", "linear-gradient(135deg,#f1f5f9,#e2e8f0)"),
    }
    html = '<div class="community-strip">'
    for key, (css, label, _) in chips.items():
        n = counts.get(key, 0)
        html += f'<span class="comm-chip {css}">{label}: {n:,}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def empty_state(icon: str, title: str, msg: str):
    st.markdown(
        f"""
<div class="empty-state">
  <div class="icon">{icon}</div>
  <h4 style="color:#334155 !important;margin:12px 0 6px;">{title}</h4>
  <p style="color:#64748b !important;font-size:0.88rem;">{msg}</p>
</div>
        """,
        unsafe_allow_html=True,
    )
