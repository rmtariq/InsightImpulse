"""Interactive issue map — scatter + heat layer."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.ui.design_tokens import DISTRICT_COORDS, PLOTLY_LAYOUT


def _risk_color(neg_pct: float, high_risk: int) -> str:
    if high_risk > 0 or neg_pct >= 45:
        return "#ef4444"
    if neg_pct >= 30:
        return "#f97316"
    if neg_pct >= 20:
        return "#f59e0b"
    return "#22c55e"


def build_map_df(df: pd.DataFrame) -> pd.DataFrame:
    col = "district" if "district" in df.columns else "constituency"
    if df.empty or col not in df.columns:
        return pd.DataFrame()
    rows = []
    for loc, grp in df.groupby(col):
        loc = str(loc).strip()
        if not loc or loc.lower() == "nan":
            continue
        coords = DISTRICT_COORDS.get(loc)
        if not coords:
            continue
        neg = (grp["sentiment"].astype(str).str.lower() == "negative").mean() * 100 if "sentiment" in grp.columns else 0
        hr = int(grp["risk_level"].astype(str).isin(["High", "Critical"]).sum()) if "risk_level" in grp.columns else 0
        top_issue = grp["issue_cluster"].mode().iloc[0] if "issue_cluster" in grp.columns and len(grp) else "—"
        comm = grp["community"].mode().iloc[0] if "community" in grp.columns and len(grp) else "general"
        rows.append({
            "location": loc, "lat": coords[0], "lon": coords[1],
            "count": len(grp), "neg_pct": round(neg, 1), "high_risk": hr,
            "top_issue": str(top_issue), "community": comm,
            "color": _risk_color(neg, hr),
        })
    return pd.DataFrame(rows)


def issue_map(df: pd.DataFrame, title: str = "Peta Hotspot Isu"):
    mdf = build_map_df(df)
    if mdf.empty:
        return None
    fig = px.scatter_mapbox(
        mdf, lat="lat", lon="lon", size="count", color="neg_pct",
        hover_name="location",
        hover_data={"top_issue": True, "count": True, "high_risk": True, "neg_pct": True, "lat": False, "lon": False},
        color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
        size_max=35, zoom=7.5, height=480,
        title=title,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        **PLOTLY_LAYOUT,
    )
    return fig


def action_map(df: pd.DataFrame, actions_df: pd.DataFrame, title: str = "Peta Tindakan"):
    """Map markers for locations with open actions."""
    if actions_df is None or actions_df.empty:
        return issue_map(df, title)
    mdf = build_map_df(df)
    if mdf.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=mdf["lat"], lon=mdf["lon"], mode="markers",
        marker=dict(size=mdf["count"].clip(8, 40), color=mdf["color"], opacity=0.85),
        text=mdf.apply(lambda r: f"{r['location']}<br>{r['top_issue']}<br>{r['count']} hantaran", axis=1),
        hoverinfo="text",
    ))
    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=mdf["lat"].mean(), lon=mdf["lon"].mean()), zoom=7.5),
        title=title, **PLOTLY_LAYOUT, height=480,
    )
    return fig
