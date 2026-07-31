"""Canonical section order & content — shared by PDF and DOCX writers."""
from __future__ import annotations

from typing import Any

from utils.report_formatting import priority_actions_from_insights

# Shared limits (None = all)
MAX_ACTIONS = 8
MAX_VOICE = 5
MAX_TOP_POSTS = 10
MAX_RISK = 8
MAX_MISINFO = 8

DASHBOARD_HINT = "Dashboard: cd n9_chinese_narrative_dashboard && .venv/bin/streamlit run app.py"

REPORT_FOOTER = "— InsightPulse · PRN Chinese Narrative Monitoring · PDF & DOCX struktur sama —"


def cover_meta(payload: dict[str, Any]) -> dict[str, str]:
    meta = payload.get("meta") or {}
    return {
        "state": payload["state"],
        "short": meta.get("short", ""),
        "focus": meta.get("focus", ""),
        "konteks": payload.get("konteks_negeri", ""),
        "generated_at": payload.get("generated_at", ""),
        "record_count": f"{payload.get('record_count', 0):,}",
        "data_period": payload.get("data_period", "—"),
        "dashboard": DASHBOARD_HINT,
    }


ETHICS_NOTES = [
    "Analisis naratif berbahasa Cina — bukan polling atau ramalan undi mengikut etnik.",
    "Tiada inferens etnik dari nama/foto; hanya kandungan teks awam.",
    "Label sentimen/risiko = pemerhatian analitik; semakan manusia digalakkan.",
]

MATRIX_INTRO = (
    "Setiap kad = satu tindakan keutamaan. Tier P1 (merah) wajib hari ini; "
    "P2 (oren) 24–48 jam; P3 (biru) susulan."
)

KPI_ROWS = [
    ("Jumlah hantaran", "total_posts"),
    ("Jumlah engagement", "total_engagement"),
    ("Sentimen positif (%)", "pct_positive"),
    ("Sentimen neutral (%)", "pct_neutral"),
    ("Sentimen negatif (%)", "pct_negative"),
    ("Naratif risiko tinggi/kritikal", "high_risk"),
    ("Ditanda maklumat salah", "misinfo"),
    ("Sumber/akaun aktif", "active_sources"),
]

COUNT_TABLES = [
    ("Taburan Sentimen", "sentiment"),
    ("Taburan Platform", "platform"),
    ("Isu Utama (Kluster)", "issues"),
    ("Taburan Bahasa", "languages"),
]


def ethics_notes(payload: dict[str, Any]) -> list[str]:
    state = payload["state"]
    return ETHICS_NOTES + [f"Rekod dalam laporan ini: {payload['record_count']:,} hantaran ({state} sahaja)."]


def snapshot_data(payload: dict[str, Any]) -> dict[str, Any]:
    ins = payload.get("insights") or {}
    k = payload["kpis"]
    return {
        "verdict": ins.get("verdict", "—"),
        "verdict_label": ins.get("verdict_label", ""),
        "verdict_action": ins.get("verdict_action", ""),
        "health_score": ins.get("health_score", "—"),
        "record_count": payload["record_count"],
        "generated_at": payload["generated_at"],
        "hot_issue": (ins.get("three_things") or {}).get("hot_issue", "—"),
        "must_do": (ins.get("three_things") or {}).get("must_do", "—"),
        "kpi_line": (
            f"Engagement: {k.get('total_engagement', 0):,} · "
            f"Positif {k.get('pct_positive')}% · Negatif {k.get('pct_negative')}% · "
            f"Risiko tinggi: {k.get('high_risk')} · Misinfo: {k.get('misinfo')}"
        ),
    }


def insights_lists(payload: dict[str, Any]) -> dict[str, Any]:
    ins = payload.get("insights") or {}
    actions = priority_actions_from_insights(ins)
    return {
        "checklist_24h": ins.get("checklist_24h") or [],
        "executive_takeaways": ins.get("executive_takeaways") or [],
        "issue_insights": ins.get("issue_insights") or [],
        "actions": actions[:MAX_ACTIONS],
        "implementation_steps": ins.get("implementation_steps") or [],
        "voice_quotes": (ins.get("voice_quotes") or [])[:MAX_VOICE],
        "state_comparison": ins.get("state_comparison") or [],
        "dont_do": ins.get("dont_do") or [],
        "checklist_72h": ins.get("checklist_72h") or [],
    }


def kpi_table_rows(payload: dict[str, Any]) -> list[list[str]]:
    k = payload["kpis"]
    rows = [["Petunjuk", "Nilai"]]
    for label, key in KPI_ROWS:
        val = k[key]
        rows.append([label, f"{val:,}" if isinstance(val, int) else str(val)])
    return rows
