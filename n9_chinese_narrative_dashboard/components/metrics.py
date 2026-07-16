"""KPI metric cards."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def kpi_row(metrics: list[tuple[str, str, str | None]]):
    """Render a row of KPI cards: (label, value, delta)."""
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        col.metric(label, value, delta)


def compute_overview_kpis(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {k: 0 for k in [
            "total_posts", "total_engagement", "total_views", "avg_engagement_rate",
            "pct_positive", "pct_neutral", "pct_negative", "high_risk", "misinfo", "active_sources",
        ]}

    total_eng = int(df["engagement_total"].sum()) if "engagement_total" in df.columns else 0
    total_views = int(df["views"].sum()) if "views" in df.columns else 0
    avg_rate = round(df["engagement_rate"].mean(), 2) if "engagement_rate" in df.columns else 0.0

    sent = df["sentiment"].astype(str).str.lower() if "sentiment" in df.columns else pd.Series(dtype=str)
    n = max(len(df), 1)
    pct_pos = round((sent == "positive").sum() / n * 100, 1)
    pct_neu = round((sent == "neutral").sum() / n * 100, 1)
    pct_neg = round((sent == "negative").sum() / n * 100, 1)

    high_risk = 0
    if "risk_level" in df.columns:
        high_risk = int(df["risk_level"].astype(str).isin(["High", "Critical"]).sum())

    misinfo = int(df["misinformation_flag"].sum()) if "misinformation_flag" in df.columns else 0
    sources = df["account_name"].nunique() if "account_name" in df.columns else 0

    return {
        "total_posts": len(df),
        "total_engagement": total_eng,
        "total_views": total_views,
        "avg_engagement_rate": avg_rate,
        "pct_positive": pct_pos,
        "pct_neutral": pct_neu,
        "pct_negative": pct_neg,
        "high_risk": high_risk,
        "misinfo": misinfo,
        "active_sources": sources,
    }


def render_overview_kpis(df: pd.DataFrame):
    k = compute_overview_kpis(df)
    kpi_row([
        ("Jumlah Hantaran", f"{k['total_posts']:,}", None),
        ("Jumlah Engagement", f"{k['total_engagement']:,}", None),
        ("Jumlah Views", f"{k['total_views']:,}", None),
        ("Purata Engagement Rate", f"{k['avg_engagement_rate']}%", None),
    ])
    kpi_row([
        ("Sentimen Positif", f"{k['pct_positive']}%", None),
        ("Sentimen Neutral", f"{k['pct_neutral']}%", None),
        ("Sentimen Negatif", f"{k['pct_negative']}%", None),
        ("Naratif Risiko Tinggi", f"{k['high_risk']:,}", None),
    ])
    kpi_row([
        ("Maklumat Salah", f"{k['misinfo']:,}", None),
        ("Sumber Aktif", f"{k['active_sources']:,}", None),
    ])


def generate_executive_summary_bm(df: pd.DataFrame) -> str:
    """Auto-generate BM executive summary from filtered data."""
    if df is None or df.empty:
        return "Tiada data dalam tempoh yang dipilih."

    k = compute_overview_kpis(df)
    top_issues = (
        df["issue_cluster"].value_counts().head(3).index.tolist()
        if "issue_cluster" in df.columns else []
    )
    issues_str = ", ".join(top_issues) if top_issues else "tiada isu dominan"

    # Sentiment trend last 7 days vs prior
    trend_note = ""
    if "published_at" in df.columns and "sentiment" in df.columns:
        df_sorted = df.dropna(subset=["published_at"]).sort_values("published_at")
        if len(df_sorted) > 10:
            cutoff = df_sorted["published_at"].max() - pd.Timedelta(days=7)
            recent = df_sorted[df_sorted["published_at"] >= cutoff]
            prior = df_sorted[df_sorted["published_at"] < cutoff]
            if len(recent) > 0 and len(prior) > 0:
                r_neg = (recent["sentiment"].astype(str).str.lower() == "negative").mean() * 100
                p_neg = (prior["sentiment"].astype(str).str.lower() == "negative").mean() * 100
                diff = round(r_neg - p_neg, 1)
                if diff > 0:
                    trend_note = f" Sentimen negatif meningkat sebanyak {diff}% dalam tujuh hari terakhir."
                elif diff < 0:
                    trend_note = f" Sentimen negatif menurun sebanyak {abs(diff)}% dalam tujuh hari terakhir."

    return (
        f"Dalam tempoh yang dipilih, sebanyak **{k['total_posts']:,}** hantaran berkaitan "
        f"naratif berbahasa Cina telah dikesan dengan jumlah engagement **{k['total_engagement']:,}**. "
        f"Isu **{issues_str}** merupakan isu paling dominan. "
        f"Peratus sentimen: positif {k['pct_positive']}%, neutral {k['pct_neutral']}%, "
        f"negatif {k['pct_negative']}%. "
        f"Terdapat **{k['high_risk']}** naratif berisiko tinggi/kritikal dan "
        f"**{k['misinfo']}** hantaran ditanda maklumat salah.{trend_note}"
    )
