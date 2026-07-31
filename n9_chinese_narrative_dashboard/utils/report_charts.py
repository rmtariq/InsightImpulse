"""Matplotlib chart PNGs for PDF/DOCX reports."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

PALETTE = {
    "positive": "#22c55e",
    "neutral": "#94a3b8",
    "negative": "#ef4444",
    "primary": "#1e3a5f",
    "accent": "#0ea5e9",
    "warn": "#f59e0b",
    "danger": "#dc2626",
}


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_sentiment_donut(df: pd.DataFrame, path: Path) -> Path | None:
    if df.empty or "sentiment" not in df.columns:
        return None
    counts = df["sentiment"].astype(str).str.lower().value_counts()
    labels, sizes, colors = [], [], []
    for key, color in [("positive", PALETTE["positive"]), ("neutral", PALETTE["neutral"]), ("negative", PALETTE["negative"])]:
        if key in counts.index:
            labels.append(key.capitalize())
            sizes.append(counts[key])
            colors.append(color)
    if not sizes:
        return None
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90, wedgeprops={"width": 0.45})
    ax.set_title("Taburan Sentimen", fontsize=12, fontweight="bold", color=PALETTE["primary"])
    return _save(fig, path)


def chart_daily_volume(df: pd.DataFrame, path: Path) -> Path | None:
    if df.empty or "published_at" not in df.columns:
        return None
    s = df.dropna(subset=["published_at"]).copy()
    if s.empty:
        return None
    daily = s.groupby(s["published_at"].dt.date).size()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.fill_between(range(len(daily)), daily.values, alpha=0.25, color=PALETTE["accent"])
    ax.plot(daily.values, color=PALETTE["primary"], linewidth=2, marker="o", markersize=4)
    ax.set_xticks(range(len(daily)))
    ax.set_xticklabels([str(d)[5:] for d in daily.index], rotation=45, ha="right", fontsize=7)
    ax.set_title("Isipadu Naratif Harian", fontsize=12, fontweight="bold", color=PALETTE["primary"])
    ax.set_ylabel("Bilangan post")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, path)


def chart_top_issues(df: pd.DataFrame, path: Path, n: int = 8) -> Path | None:
    if df.empty or "issue_cluster" not in df.columns:
        return None
    top = df["issue_cluster"].value_counts().head(n).sort_values()
    fig, ax = plt.subplots(figsize=(7, max(3, n * 0.35)))
    colors = [PALETTE["danger"] if i >= len(top) - 2 else PALETTE["primary"] for i in range(len(top))]
    ax.barh(top.index.astype(str), top.values, color=colors)
    ax.set_title(f"Top {n} Kluster Isu", fontsize=12, fontweight="bold", color=PALETTE["primary"])
    ax.set_xlabel("Bilangan post")
    fig.tight_layout()
    return _save(fig, path)


def chart_platforms(df: pd.DataFrame, path: Path) -> Path | None:
    if df.empty or "platform" not in df.columns:
        return None
    c = df["platform"].value_counts().head(8)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(range(len(c)), c.values, color=PALETTE["accent"])
    ax.set_xticks(range(len(c)))
    ax.set_xticklabels(c.index.astype(str), rotation=35, ha="right", fontsize=8)
    ax.set_title("Taburan Platform", fontsize=12, fontweight="bold", color=PALETTE["primary"])
    ax.set_ylabel("Bilangan")
    fig.tight_layout()
    return _save(fig, path)


def chart_district_heatmap(df: pd.DataFrame, path: Path) -> Path | None:
    col = "district" if "district" in df.columns else "constituency"
    if df.empty or col not in df.columns or "issue_cluster" not in df.columns:
        return None
    top_issues = df["issue_cluster"].value_counts().head(6).index
    top_loc = df[col].value_counts().head(8).index
    sub = df[df["issue_cluster"].isin(top_issues) & df[col].isin(top_loc)]
    if sub.empty:
        return None
    pivot = pd.crosstab(sub[col], sub["issue_cluster"])
    fig, ax = plt.subplots(figsize=(8, max(3.5, len(pivot) * 0.35)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns.astype(str), rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index.astype(str), fontsize=8)
    ax.set_title(f"Heatmap Isu × {col.title()}", fontsize=12, fontweight="bold", color=PALETTE["primary"])
    plt.colorbar(im, ax=ax, fraction=0.03)
    fig.tight_layout()
    return _save(fig, path)


def chart_health_gauge(score: float, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(4, 3), subplot_kw={"projection": "polar"})
    theta = np.linspace(0, np.pi, 100)
    ax.plot(theta, [1] * 100, color="#e5e7eb", linewidth=18, solid_capstyle="round")
    pct = max(0, min(100, score)) / 100
    fill_theta = np.linspace(0, np.pi * pct, 50)
    color = PALETTE["positive"] if score >= 70 else PALETTE["warn"] if score >= 45 else PALETTE["danger"]
    ax.plot(fill_theta, [1] * len(fill_theta), color=color, linewidth=18, solid_capstyle="round")
    ax.set_ylim(0, 1.2)
    ax.axis("off")
    ax.text(0, 0, f"{score:.0f}", ha="center", va="center", fontsize=28, fontweight="bold", color=PALETTE["primary"])
    ax.text(0, -0.35, "Narrative Health", ha="center", va="center", fontsize=9, color="#64748b")
    fig.tight_layout()
    return _save(fig, path)


def generate_all_charts(df: pd.DataFrame, out_dir: Path, health_score: float) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}
    mapping = {
        "sentiment": chart_sentiment_donut(df, out_dir / "sentiment.png"),
        "volume": chart_daily_volume(df, out_dir / "volume.png"),
        "issues": chart_top_issues(df, out_dir / "issues.png"),
        "platforms": chart_platforms(df, out_dir / "platforms.png"),
        "heatmap": chart_district_heatmap(df, out_dir / "heatmap.png"),
        "health": chart_health_gauge(health_score, out_dir / "health.png"),
    }
    for k, p in mapping.items():
        if p:
            paths[k] = str(p)
    return paths
