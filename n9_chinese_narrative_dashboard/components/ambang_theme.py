"""Dark AMBANG-style theme — applied globally."""
from __future__ import annotations

import streamlit as st

PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cbd5e1", size=12),
    margin=dict(l=8, r=8, t=44, b=8),
    colorway=["#fb923c", "#38bdf8", "#f87171", "#4ade80", "#a78bfa", "#facc15"],
)

PLOTLY_CHART_CONFIG = {"displayModeBar": False, "responsive": True}


def inject_ambang_css():
    st.markdown(
        """
<style>
.stApp { background: linear-gradient(165deg, #070d18 0%, #0f172a 45%, #0b1220 100%); }
.block-container { padding-top: 0.8rem; max-width: 100%; }
h1,h2,h3,h4,h5,h6,p,label,span,li { color: #e2e8f0 !important; }
[data-testid="stSidebar"] { background: #070d18; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] .stMarkdown h3 { color: #f8fafc !important; font-size: 0.95rem; }

.ambang-header {
  background: linear-gradient(90deg, #111827 0%, #0f172a 100%);
  border: 1px solid #1f2937; border-radius: 12px;
  padding: 16px 22px; margin-bottom: 14px;
}
.ambang-title { font-size: 1.45rem; font-weight: 800; letter-spacing: 0.05em; color: #f8fafc !important; margin: 0; }
.ambang-sub { font-size: 0.76rem; color: #94a3b8 !important; margin: 4px 0 0; text-transform: uppercase; letter-spacing: 0.07em; }
.ambang-clock { font-size: 1.05rem; font-weight: 700; color: #fb923c !important; text-align: right; margin: 0; }
.ambang-date { font-size: 0.72rem; color: #64748b !important; text-align: right; margin: 0; }

.kpi-card {
  background: #111827; border: 1px solid #1f2937; border-left: 4px solid #fb923c;
  border-radius: 8px; padding: 11px 14px; margin-bottom: 7px;
}
.kpi-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8 !important; margin: 0; }
.kpi-value { font-size: 1.55rem; font-weight: 800; color: #fb923c !important; margin: 2px 0; line-height: 1.1; }
.kpi-value.teal { color: #2dd4bf !important; }
.kpi-value.red { color: #f87171 !important; }
.kpi-meta { font-size: 0.62rem; color: #64748b !important; margin: 0; }

.panel {
  background: #111827; border: 1px solid #1f2937; border-radius: 10px;
  padding: 12px 14px; margin-bottom: 10px;
}
.panel-title {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  color: #94a3b8 !important; margin: 0 0 8px; border-bottom: 1px solid #1f2937; padding-bottom: 6px;
}
.fact-item { font-size: 0.81rem; color: #cbd5e1 !important; margin: 0 0 8px; line-height: 1.45; }
.fact-src { color: #64748b !important; font-size: 0.66rem; }

.status-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; margin-right: 6px; }
.status-hijau { background: #14532d; color: #86efac !important; }
.status-kuning { background: #713f12; color: #fde047 !important; }
.status-jingga { background: #7c2d12; color: #fdba74 !important; }
.status-merah { background: #7f1d1d; color: #fca5a5 !important; }

.nav-hint {
  background: #0f172a; border: 1px dashed #334155; border-radius: 8px;
  padding: 10px 14px; margin-bottom: 12px; font-size: 0.82rem; color: #94a3b8 !important;
}
.step-num {
  display: inline-block; background: #fb923c; color: #0f172a !important;
  font-weight: 800; width: 22px; height: 22px; border-radius: 50%;
  text-align: center; line-height: 22px; font-size: 0.75rem; margin-right: 6px;
}

[data-testid="stMetric"] {
  background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 8px 12px;
}
[data-testid="stMetricValue"] { color: #fb923c !important; }
[data-testid="stDataFrame"] { border: 1px solid #1f2937; border-radius: 8px; }
.stExpander { background: #111827; border: 1px solid #1f2937; border-radius: 8px; }

section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: #ea580c !important; border-color: #ea580c !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_dark(fig):
    if fig is None:
        return None
    fig.update_layout(**PLOTLY_DARK)
    fig.update_xaxes(gridcolor="#1e293b", zerolinecolor="#1f2937")
    fig.update_yaxes(gridcolor="#1e293b", zerolinecolor="#1f2937")
    return fig


def plotly_chart(fig, **kwargs):
    """Wrapper — always dark theme."""
    if fig is not None:
        apply_plotly_dark(fig)
    cfg = kwargs.get("config") or PLOTLY_CHART_CONFIG
    st.plotly_chart(fig, width=kwargs.get("width", "stretch"), config=cfg)
