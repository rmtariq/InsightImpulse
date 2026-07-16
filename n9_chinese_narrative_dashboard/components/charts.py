"""Plotly chart helpers."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def daily_volume(df: pd.DataFrame):
    if df.empty or "published_at" not in df.columns:
        return None
    daily = df.groupby(df["published_at"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    return px.line(daily, x="date", y="count", title="Isipadu Naratif Harian", markers=True)


def sentiment_pie(df: pd.DataFrame):
    if df.empty or "sentiment" not in df.columns:
        return None
    counts = df["sentiment"].value_counts().reset_index()
    counts.columns = ["sentiment", "count"]
    return px.pie(counts, names="sentiment", values="count", title="Taburan Sentimen")


def platform_bar(df: pd.DataFrame):
    if df.empty or "platform" not in df.columns:
        return None
    c = df["platform"].value_counts().reset_index()
    c.columns = ["platform", "count"]
    return px.bar(c, x="platform", y="count", title="Taburan Platform", color="count")


def top_issues(df: pd.DataFrame, n: int = 10):
    if df.empty or "issue_cluster" not in df.columns:
        return None
    c = df["issue_cluster"].value_counts().head(n).reset_index()
    c.columns = ["issue", "count"]
    return px.bar(c, x="count", y="issue", orientation="h", title=f"Top {n} Kluster Isu")


def top_locations(df: pd.DataFrame, n: int = 5):
    col = "constituency" if "constituency" in df.columns else "district"
    if df.empty or col not in df.columns:
        return None
    c = df[col].value_counts().head(n).reset_index()
    c.columns = ["location", "count"]
    return px.bar(c, x="location", y="count", title=f"Top {n} Lokasi")


def top_accounts(df: pd.DataFrame, n: int = 10):
    if df.empty or "account_name" not in df.columns:
        return None
    g = df.groupby("account_name")["engagement_total"].sum().nlargest(n).reset_index()
    g.columns = ["account", "engagement"]
    return px.bar(g, x="engagement", y="account", orientation="h", title=f"Top {n} Akaun (Engagement)")


def language_bar(df: pd.DataFrame):
    if df.empty or "language_detected" not in df.columns:
        return None
    c = df["language_detected"].value_counts().reset_index()
    c.columns = ["language", "count"]
    return px.bar(c, x="language", y="count", title="Taburan Bahasa")


def risk_distribution(df: pd.DataFrame):
    if df.empty or "risk_level" not in df.columns:
        return None
    c = df["risk_level"].value_counts().reset_index()
    c.columns = ["risk", "count"]
    order = ["Low", "Medium", "High", "Critical"]
    c["risk"] = pd.Categorical(c["risk"], categories=order, ordered=True)
    c = c.sort_values("risk")
    return px.bar(c, x="risk", y="count", title="Taburan Tahap Risiko", color="risk")


def issue_sentiment_heatmap(df: pd.DataFrame):
    if df.empty or "issue_cluster" not in df.columns or "sentiment" not in df.columns:
        return None
    pivot = pd.crosstab(df["issue_cluster"], df["sentiment"])
    return px.imshow(pivot, title="Isu vs Sentimen (Heatmap)", aspect="auto", color_continuous_scale="RdYlGn_r")


def issue_platform_heatmap(df: pd.DataFrame):
    if df.empty or "issue_cluster" not in df.columns or "platform" not in df.columns:
        return None
    pivot = pd.crosstab(df["issue_cluster"], df["platform"])
    return px.imshow(pivot, title="Isu vs Platform (Heatmap)", aspect="auto")


def issue_trend(df: pd.DataFrame, issue: str | None = None):
    if df.empty or "published_at" not in df.columns:
        return None
    sub = df if not issue else df[df["issue_cluster"] == issue]
    daily = sub.groupby(sub["published_at"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    title = f"Trend Isu: {issue}" if issue else "Trend Isu (Semua)"
    return px.line(daily, x="date", y="count", title=title, markers=True)


def party_mentions(df: pd.DataFrame):
    if df.empty or "party_mentioned" not in df.columns:
        return None
    sub = df[df["party_mentioned"].astype(str).str.len() > 0]
    c = sub["party_mentioned"].value_counts().reset_index()
    c.columns = ["party", "count"]
    return px.bar(c, x="party", y="count", title="Sebutan Parti")


def party_sentiment(df: pd.DataFrame):
    if df.empty or "party_mentioned" not in df.columns or "sentiment" not in df.columns:
        return None
    sub = df[df["party_mentioned"].astype(str).str.len() > 0]
    pivot = pd.crosstab(sub["party_mentioned"], sub["sentiment"])
    return px.bar(pivot.reset_index(), x="party_mentioned", y=pivot.columns.tolist(), title="Sentimen mengikut Parti", barmode="stack")


def geo_bar(df: pd.DataFrame, col: str = "district"):
    if df.empty or col not in df.columns:
        return None
    c = df[col].value_counts().head(15).reset_index()
    c.columns = [col, "count"]
    return px.bar(c, x=col, y="count", title=f"Hantaran mengikut {col}")


def party_radar(df: pd.DataFrame, party: str):
    """Radar chart metrics for one party."""
    if df.empty or "party_mentioned" not in df.columns:
        return None
    sub = df[df["party_mentioned"] == party]
    if sub.empty:
        return None
    total = len(df)
    sov = len(sub) / max(total, 1) * 100
    pos = (sub["sentiment"].astype(str).str.lower() == "positive").mean() * 100 if "sentiment" in sub.columns else 0
    eng = sub["engagement_total"].sum() / max(df["engagement_total"].sum(), 1) * 100
    issues = sub["issue_cluster"].nunique() if "issue_cluster" in sub.columns else 0
    viral = int((sub["engagement_total"] > sub["engagement_total"].quantile(0.9)).sum()) if "engagement_total" in sub.columns else 0
    risk = (sub["risk_level"].astype(str).isin(["High", "Critical"]).mean() * 100) if "risk_level" in sub.columns else 0

    categories = ["Share of Voice", "Positif %", "Engagement %", "Bil. Isu", "Viral", "Risiko %"]
    values = [sov, pos, eng, min(issues * 5, 100), min(viral * 10, 100), risk]

    fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill="toself", name=party))
    fig.update_layout(title=f"Perbandingan Naratif — {party}", polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    return fig


def risk_trend(df: pd.DataFrame):
    if df.empty or "published_at" not in df.columns or "risk_level" not in df.columns:
        return None
    sub = df[df["risk_level"].astype(str).isin(["High", "Critical"])]
    daily = sub.groupby(sub["published_at"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    return px.line(daily, x="date", y="count", title="Trend Risiko Tinggi/Kritikal", markers=True)
