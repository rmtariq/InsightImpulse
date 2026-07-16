"""Themed Plotly charts."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.ui.design_tokens import CHART_COLORS, PLOTLY_LAYOUT
from utils.reporting.labels import normalize_issue, UNCLASSIFIED


def _layout(fig, title: str):
    if fig is None:
        return None
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=title, x=0, font=dict(size=14, color="#0f172a")),
    )
    fig.update_xaxes(gridcolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#e2e8f0")
    return fig


def sentiment_donut(df: pd.DataFrame, title: str = "Sentimen — gambaran keseluruhan"):
    if df.empty or "sentiment" not in df.columns:
        return None
    s = df["sentiment"].astype(str).str.lower()
    s = s[s.isin(["positive", "neutral", "negative"])]
    if s.empty:
        return None
    c = s.value_counts().reset_index()
    c.columns = ["sentiment", "count"]
    colors = {"positive": "#22c55e", "neutral": "#94a3b8", "negative": "#ef4444"}
    fig = go.Figure(data=[go.Pie(
        labels=c["sentiment"], values=c["count"], hole=0.55,
        marker=dict(colors=[colors.get(x, "#64748b") for x in c["sentiment"]]),
        textinfo="label+percent",
    )])
    return _layout(fig, title)


def issues_bar(df: pd.DataFrame, n: int = 8, title: str = "Isu utama yang paling dibincang"):
    if df.empty or "issue_cluster" not in df.columns:
        return None
    s = df["issue_cluster"].apply(normalize_issue)
    s = s[s != UNCLASSIFIED]
    c = s.value_counts().head(n).reset_index()
    c.columns = ["issue", "count"]
    if c.empty:
        return None
    fig = px.bar(c, x="count", y="issue", orientation="h", color="count",
                 color_continuous_scale=["#dbeafe", "#2563eb"])
    fig.update_layout(coloraxis_showscale=False)
    return _layout(fig, title)


def trend_line(df: pd.DataFrame, title: str = "Trend isipadu naratif harian"):
    if df.empty or "published_at" not in df.columns:
        return None
    daily = df.groupby(df["published_at"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    fig = px.area(daily, x="date", y="count", color_discrete_sequence=[CHART_COLORS[0]])
    return _layout(fig, title)


def platform_bar(df: pd.DataFrame, title: str = "Di mana naratif berlaku (platform)"):
    if df.empty or "platform" not in df.columns:
        return None
    c = df["platform"].value_counts().head(8).reset_index()
    c.columns = ["platform", "count"]
    fig = px.bar(c, x="count", y="platform", orientation="h", color="platform", color_discrete_sequence=CHART_COLORS)
    return _layout(fig, title)


def district_bar(df: pd.DataFrame, title: str = "Hotspot daerah — bilangan hantaran"):
    col = "district" if "district" in df.columns else "constituency"
    if df.empty or col not in df.columns:
        return None
    g = df.groupby(col).agg(
        count=(col, "count"),
        neg=("sentiment", lambda s: (s.astype(str).str.lower() == "negative").mean() * 100 if len(s) else 0),
    ).reset_index().sort_values("count", ascending=False).head(12)
    fig = px.bar(g, x="count", y=col, orientation="h", color="neg",
                 color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
                 labels={"neg": "% Negatif"})
    return _layout(fig, title)
