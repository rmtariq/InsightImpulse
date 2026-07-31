"""Configurable in-dashboard alerts."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.storage import config_path, load_csv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_alert_rules() -> pd.DataFrame:
    return load_csv(config_path("alert_rules.csv"))


def evaluate_alerts(posts: pd.DataFrame, complaints: pd.DataFrame) -> list[dict]:
    """Return alert messages for display inside dashboard only."""
    alerts: list[dict] = []
    if posts is None or posts.empty:
        return alerts

    try:
        from backend.nim_safety import enrich_posts_with_safety  # noqa: WPS433
        posts = enrich_posts_with_safety(posts)
    except Exception:
        pass

    rules = load_alert_rules()
    if rules.empty:
        rules = pd.DataFrame([
            {"rule_id": "R1", "rule_name": "Volume +50%", "threshold": 50, "enabled": True},
            {"rule_id": "R2", "rule_name": "Negatif >65%", "threshold": 65, "enabled": True},
        ])

    if "sentiment" in posts.columns:
        neg = (posts["sentiment"].astype(str).str.lower() == "negative").mean() * 100
        if neg > 65:
            alerts.append({"level": "warning", "msg": f"Sentimen negatif keseluruhan {neg:.1f}% melebihi ambang 65%."})

    if "growth_percentage" in posts.columns:
        hot = posts[posts["growth_percentage"] > 50]
        if not hot.empty:
            alerts.append({"level": "info", "msg": f"{len(hot)} kumpulan naratif dengan pertumbuhan >50%."})

    if "risk_level" in posts.columns:
        hr = posts[posts["risk_level"].isin(["High", "Critical"])]
        if not hr.empty and "issue_cluster" in hr.columns:
            ic = hr["issue_cluster"].mode().iloc[0]
            if str(ic).lower() in ("race and religion",):
                alerts.append({"level": "critical", "msg": f"Risiko perkauman/agama tinggi pada isu: {ic}."})

    if "misinformation_flag" in posts.columns:
        m = posts[posts["misinformation_flag"] == True]  # noqa: E712
        if not m.empty and "engagement_total" in m.columns:
            hi = m[m["engagement_total"] > 1000]
            if not hi.empty:
                alerts.append({"level": "critical", "msg": f"{len(hi)} siaran maklumat salah dengan engagement tinggi."})

    if "nim_safety_flagged" in posts.columns:
        flagged = posts[posts["nim_safety_flagged"].astype(str).str.lower().isin(["true", "1"])]
        if not flagged.empty:
            categories = "isu sensitif"
            if "nim_safety_categories" in flagged.columns and not flagged["nim_safety_categories"].dropna().empty:
                categories = str(flagged["nim_safety_categories"].dropna().iloc[0])
            alerts.append({
                "level": "critical",
                "msg": f"{len(flagged)} siaran ditanda Nemotron Safety ({categories}) — perlu semakan manusia.",
            })

    if complaints is not None and not complaints.empty:
        open_c = complaints[~complaints["complaint_status"].isin(["Selesai", "Di Luar Bidang Kuasa"])]
        if len(open_c) > 10:
            alerts.append({"level": "warning", "msg": f"{len(open_c)} aduan belum selesai — semak SLA."})

    return alerts
