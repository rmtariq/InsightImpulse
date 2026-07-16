"""Two charts only for executive report: sentiment + top 5 issues."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd

from utils.reporting.labels import UNCLASSIFIED, normalize_issue

NAVY = "#1e3a5f"
COLORS = {"Positif": "#22c55e", "Neutral": "#94a3b8", "Negatif": "#ef4444", "Belum Dilabel": "#cbd5e1"}


def _save(fig, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def chart_sentiment(sc: dict, path: Path, period: str) -> str | None:
    labels, sizes, colors = [], [], []
    mapping = [
        ("Positif", "pct_positive", "positive", COLORS["Positif"]),
        ("Neutral", "pct_neutral", "neutral", COLORS["Neutral"]),
        ("Negatif", "pct_negative", "negative", COLORS["Negatif"]),
    ]
    for lbl, pk, ck, col in mapping:
        if sc.get(ck, 0) > 0:
            labels.append(f"{lbl} ({sc[pk]}%)")
            sizes.append(sc[ck])
            colors.append(col)
    if sc.get("unknown", 0) > 0:
        labels.append(f"Belum Dilabel ({sc['pct_unknown']}%)")
        sizes.append(sc["unknown"])
        colors.append(COLORS["Belum Dilabel"])
    if not sizes:
        return None
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.pie(sizes, labels=labels, colors=colors, autopct="", startangle=90, wedgeprops={"width": 0.42})
    ax.set_title(f"Taburan Sentimen\n{period}", fontsize=11, fontweight="bold", color=NAVY)
    return _save(fig, path)


def chart_top_issues(df: pd.DataFrame, path: Path, period: str, n: int = 5) -> str | None:
    if df.empty or "issue_cluster" not in df.columns:
        return None
    work = df.copy()
    work["_ic"] = work["issue_cluster"].apply(normalize_issue)
    work = work[work["_ic"] != UNCLASSIFIED]
    top = work["_ic"].value_counts().head(n).sort_values()
    if top.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, max(3.5, n * 0.55)))
    ax.barh(top.index.astype(str), top.values, color=NAVY)
    ax.set_title(f"Lima Isu Utama\n{period}", fontsize=11, fontweight="bold", color=NAVY)
    ax.set_xlabel("Bilangan hantaran")
    fig.tight_layout()
    return _save(fig, path)


def generate_executive_charts(df: pd.DataFrame, out_dir: Path, sc: dict, period: str = "") -> Dict[str, str]:
    out: Dict[str, str] = {}
    p = chart_sentiment(sc, out_dir / "exec_sentiment.png", period)
    if p:
        out["sentiment"] = p
    p2 = chart_top_issues(df, out_dir / "exec_issues.png", period)
    if p2:
        out["issues"] = p2
    return out
