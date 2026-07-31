"""Premium CSS — colourful modern SaaS theme."""
from __future__ import annotations

import streamlit as st

from components.ui.design_tokens import GRADIENTS


def inject_premium_css(dark: bool = False):
    bg = "#0f172a" if dark else "#f1f5f9"
    card = "#1e293b" if dark else "#ffffff"
    text = "#f1f5f9" if dark else "#0f172a"
    muted = "#94a3b8" if dark else "#64748b"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif !important; }}
.stApp {{ background: {bg}; animation: fadeIn 0.4s ease; }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes slideUp {{ from {{ transform: translateY(12px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}

.block-container {{ padding-top: 1rem; max-width: 100%; }}
[data-testid="stSidebar"] {{ background: {card}; border-right: 1px solid #e2e8f0; }}

/* Header */
.premium-header {{
  background: {GRADIENTS["header"]};
  border-radius: 16px; padding: 22px 28px; margin-bottom: 16px;
  box-shadow: 0 10px 40px rgba(37,99,235,0.25);
  animation: slideUp 0.5s ease;
}}
.premium-header h1 {{ color: #fff !important; font-size: 1.55rem; font-weight: 800; margin: 0; letter-spacing: -0.02em; }}
.premium-header p {{ color: rgba(255,255,255,0.88) !important; margin: 6px 0 0; font-size: 0.85rem; }}
.premium-header .meta {{ color: rgba(255,255,255,0.75) !important; font-size: 0.75rem; }}

/* KPI cards */
.kpi-grid {{ display: grid; gap: 12px; }}
.kpi-card-v2 {{
  background: {card}; border-radius: 14px; padding: 16px 18px;
  border: 1px solid #e2e8f0; box-shadow: 0 4px 14px rgba(15,23,42,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
  animation: slideUp 0.45s ease;
}}
.kpi-card-v2:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(37,99,235,0.12); }}
.kpi-card-v2 .icon {{ font-size: 1.4rem; margin-bottom: 6px; }}
.kpi-card-v2 .label {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: {muted} !important; font-weight: 600; }}
.kpi-card-v2 .value {{ font-size: 1.75rem; font-weight: 800; color: {text} !important; line-height: 1.1; margin: 4px 0; }}
.kpi-card-v2 .sub {{ font-size: 0.72rem; color: {muted} !important; }}
.kpi-card-v2.gradient {{ background: linear-gradient(135deg, #eff6ff, #f5f3ff); border: none; }}

/* Executive summary */
.exec-card {{
  background: {GRADIENTS["exec"]};
  border-radius: 16px; padding: 20px 24px; margin-bottom: 16px;
  border: 1px solid #e0e7ff; box-shadow: 0 8px 24px rgba(124,58,237,0.08);
  animation: slideUp 0.55s ease;
}}
.exec-card h3 {{ color: {text} !important; font-size: 1rem; font-weight: 700; margin: 0 0 10px; }}
.exec-card p {{ color: #334155 !important; font-size: 0.9rem; line-height: 1.55; margin: 0 0 8px; }}
.exec-highlight {{ background: rgba(255,255,255,0.7); border-radius: 10px; padding: 10px 14px; margin: 6px 0;
  border-left: 4px solid #2563eb; font-size: 0.84rem; color: #1e293b !important; }}

/* Badges */
.badge {{ display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }}
.badge-success {{ background: #dcfce7; color: #166534 !important; }}
.badge-warning {{ background: #fef9c3; color: #854d0e !important; }}
.badge-orange {{ background: #ffedd5; color: #9a3412 !important; }}
.badge-critical {{ background: #fee2e2; color: #991b1b !important; }}
.badge-info {{ background: #dbeafe; color: #1e40af !important; }}
.badge-neutral {{ background: #f1f5f9; color: #475569 !important; }}
.badge-late {{ background: #7f1d1d; color: #fecaca !important; }}
.badge-chinese {{ background: #ffe4e6; color: #be123c !important; }}
.badge-indian {{ background: #f3e8ff; color: #7e22ce !important; }}
.badge-cross {{ background: #cffafe; color: #0e7490 !important; }}

/* Community strip */
.community-strip {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }}
.comm-chip {{ padding: 6px 14px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }}

/* Kanban */
.kanban-col {{ background: #f8fafc; border-radius: 12px; padding: 12px; min-height: 200px; border: 1px solid #e2e8f0; }}
.kanban-card {{ background: {card}; border-radius: 10px; padding: 12px; margin-bottom: 8px;
  border-left: 4px solid #2563eb; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.15s; }}
.kanban-card:hover {{ transform: translateY(-2px); }}
.kanban-card.p1 {{ border-left-color: #ef4444; }}
.kanban-card.p2 {{ border-left-color: #f59e0b; }}
.kanban-card.p3 {{ border-left-color: #2563eb; }}
.kanban-title {{ font-weight: 700; font-size: 0.85rem; color: {text} !important; }}
.kanban-meta {{ font-size: 0.72rem; color: {muted} !important; }}

/* Copy panel */
.copy-panel {{ background: {card}; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0;
  box-shadow: 0 8px 30px rgba(0,0,0,0.08); }}
.copy-block {{ background: #f8fafc; border-radius: 8px; padding: 12px; font-size: 0.85rem;
  border: 1px dashed #cbd5e1; margin: 8px 0; white-space: pre-wrap; }}

/* Nav hint */
.nav-pill {{ background: {card}; border-radius: 10px; padding: 10px 16px; margin-bottom: 12px;
  border: 1px solid #e2e8f0; font-size: 0.82rem; color: {muted} !important; }}

/* Empty state */
.empty-state {{ text-align: center; padding: 40px 20px; background: {card}; border-radius: 16px;
  border: 2px dashed #cbd5e1; }}
.empty-state .icon {{ font-size: 2.5rem; opacity: 0.5; }}

/* Progress */
.progress-bar {{ height: 6px; background: #e2e8f0; border-radius: 999px; overflow: hidden; margin-top: 6px; }}
.progress-fill {{ height: 100%; background: linear-gradient(90deg, #2563eb, #06b6d4); border-radius: 999px; }}

[data-testid="stMetric"] {{ background: {card}; border-radius: 12px; padding: 12px; border: 1px solid #e2e8f0; }}
</style>
        """,
        unsafe_allow_html=True,
    )


from components.ui.design_tokens import PLOTLY_CHART_CONFIG

def plotly_chart(fig, **kwargs):
    if fig is None:
        return
    from components.ui.design_tokens import PLOTLY_LAYOUT
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0")
    cfg = kwargs.get("config") or PLOTLY_CHART_CONFIG
    st.plotly_chart(fig, width=kwargs.get("width", "stretch"), config=cfg)
