"""Analitik + insight + cadangan tindakan untuk laporan PDF/DOCX."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils.action_engine import build_action_candidates, recommend

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "config/narrative_playbook.csv"

STATE_PLAYBOOK_HINTS: dict[str, list[str]] = {
    "Negeri Sembilan": [
        "Pantau naratif berkaitan kestabilan MB dan timing PRN — elak spekulasi tanpa bukti rasmi.",
        "Seremban/Nilai/PD: isu perkhidmatan bandar (air, jalan, kos hidup) lebih berpengaruh daripada naratif parti semata-mata.",
        "Media Cina NS = suara berwajaran tinggi — pastikan penjelasan dasar tersedia dalam BM dan Cina sebelum sidang media.",
    ],
    "Johor": [
        "JB/Skudai/Stulang: fokus respons perkhidmatan bandar dan penjelasan dasar PH/BN tanpa serangan peribadi.",
        "Naratif MB Johor = konteks, bukan suara komuniti Cina langsung — jangan campur dalam mesej komuniti.",
        "Platform FB/X dominan di bandar — masa respons 24–48 jam kritikal sebelum naratif meluas.",
    ],
    "Melaka": [
        "Bandar heritage kompak — isu trafik, pelancongan, perkhidmatan tempatan mudah menjadi viral.",
        "Kerajaan PH negeri: tekankan rekod perkhidmatan disahkan, bukan janji tanpa bukti.",
        "Volume lebih kecil vs N9/Johor — satu post negatif berengagement tinggi boleh dominan; prioritikan semakan fakta awal.",
    ],
}

VERDICT_META = {
    "HIJAU": {"label": "STABIL", "action": "Pemantauan rutin — tiada tindakan segera melainkan isu baharu muncul.", "color": "#22c55e"},
    "KUNING": {"label": "WASPADA", "action": "Laksanakan P1–P3 dalam 24–48 jam; koordinasi Communications + Operations.", "color": "#f59e0b"},
    "MERAH": {"label": "PRIORITI TINGGI", "action": "War room hari ini — semakan Legal/Management sebelum sebarang kenyataan awam.", "color": "#dc2626"},
}


def _load_playbook() -> pd.DataFrame:
    if PLAYBOOK.exists():
        return pd.read_csv(PLAYBOOK)
    return pd.DataFrame()


def compute_health_score(k: dict[str, Any]) -> float:
    score = 100.0
    score -= float(k.get("neg_pct", 0)) * 0.45
    score -= float(k.get("high_risk", 0)) * 4
    score -= float(k.get("misinfo", 0)) * 8
    if k.get("neg_trend_up"):
        score -= 8
    return round(max(0, min(100, score)), 0)


def compute_verdict(health: float, k: dict[str, Any]) -> str:
    if health >= 70 and k.get("high_risk", 0) == 0 and k.get("misinfo", 0) == 0:
        return "HIJAU"
    if health >= 45 or (k.get("high_risk", 0) <= 2 and k.get("misinfo", 0) <= 1):
        return "KUNING"
    return "MERAH"


def _sentiment_trend(sub: pd.DataFrame) -> tuple[str, bool]:
    if sub.empty or "published_at" not in sub.columns or "sentiment" not in sub.columns:
        return "Trend sentimen: data tidak mencukupi.", False
    s = sub.dropna(subset=["published_at"]).sort_values("published_at")
    if len(s) < 8:
        return "Trend sentimen: data masih sedikit — teruskan pemantauan harian.", False
    mid = s["published_at"].iloc[len(s) // 2]
    early = s[s["published_at"] < mid]
    late = s[s["published_at"] >= mid]
    if early.empty or late.empty:
        return "Trend sentimen: stabil antara tempoh awal dan akhir.", False
    e_neg = (early["sentiment"].astype(str).str.lower() == "negative").mean() * 100
    l_neg = (late["sentiment"].astype(str).str.lower() == "negative").mean() * 100
    diff = round(l_neg - e_neg, 1)
    if diff > 5:
        return f"Trend: sentimen negatif MENINGKAT +{diff}% (tempoh akhir vs awal).", True
    if diff < -5:
        return f"Trend: sentimen negatif MENURUN {abs(diff)}%.", False
    return "Trend sentimen: relatif stabil.", False


def _dominant_channel(sub: pd.DataFrame) -> str:
    if sub.empty or "platform" not in sub.columns:
        return ""
    top = sub["platform"].value_counts().head(2)
    parts = [f"{k} ({v})" for k, v in top.items()]
    return "Saluran dominan: " + ", ".join(parts)


def _top_issue_name(sub: pd.DataFrame) -> str:
    if sub.empty or "issue_cluster" not in sub.columns:
        return "—"
    vc = sub["issue_cluster"].value_counts()
    return str(vc.index[0]) if len(vc) else "—"


def _voice_quotes(sub: pd.DataFrame, n: int = 5) -> list[dict[str, str]]:
    if sub.empty:
        return []
    sort_col = "engagement_total" if "engagement_total" in sub.columns else None
    top = sub.sort_values(sort_col, ascending=False).head(n) if sort_col else sub.head(n)
    rows = []
    for _, r in top.iterrows():
        text = str(r.get("post_text", ""))[:280]
        trans = str(r.get("translated_text_bm", "") or "")
        if trans.lower() in ("nan", "", "—"):
            trans = "(Terjemahan BM — rujuk dashboard atau jalankan auto-translate)"
        rows.append({
            "platform": str(r.get("platform", "")),
            "sentiment": str(r.get("sentiment", "")),
            "issue": str(r.get("issue_cluster", "")),
            "location": str(r.get("constituency") or r.get("district") or "—"),
            "original": text,
            "translation_bm": trans[:280],
            "url": str(r.get("source_url", "") or "")[:120],
            "engagement": str(int(r.get("engagement_total", 0) or 0)),
        })
    return rows


def _issue_insights(sub: pd.DataFrame) -> list[str]:
    if sub.empty or "issue_cluster" not in sub.columns:
        return ["Tiada kluster isu untuk dianalisis."]
    insights = []
    for ic, grp in sub.groupby("issue_cluster"):
        if not str(ic).strip() or str(ic).lower() == "nan":
            continue
        neg = (grp["sentiment"].astype(str).str.lower() == "negative").mean() * 100 if "sentiment" in grp.columns else 0
        mis = bool(grp["misinformation_flag"].any()) if "misinformation_flag" in grp.columns else False
        rm = grp["risk_level"].mode() if "risk_level" in grp.columns and len(grp) else pd.Series(dtype=str)
        risk = str(rm.iloc[0]) if len(rm) else "Low"
        _, action, reason = recommend(str(ic), neg, mis, risk)
        insights.append(
            f"{ic} ({len(grp)} post, {neg:.0f}% negatif): {reason} → {action[:160]}"
        )
        if len(insights) >= 5:
            break
    return insights or ["Tiada isu dominan melepasi ambang analitik."]


def build_state_comparison(full_df: pd.DataFrame, current_state: str) -> list[list[str]]:
    rows = [["Negeri", "Post", "% Negatif", "Risiko Tinggi", "Misinfo", "Isu #1"]]
    if full_df is None or full_df.empty or "state" not in full_df.columns:
        return rows
    for st in ["Negeri Sembilan", "Johor", "Melaka"]:
        sub = full_df[full_df["state"].astype(str) == st]
        if sub.empty:
            continue
        sent = sub["sentiment"].astype(str).str.lower()
        neg = round((sent == "negative").mean() * 100, 1)
        hi = int(sub["risk_level"].astype(str).isin(["High", "Critical"]).sum()) if "risk_level" in sub.columns else 0
        mi = int(sub["misinformation_flag"].sum()) if "misinformation_flag" in sub.columns else 0
        top = _top_issue_name(sub)
        marker = " ◀" if st == current_state else ""
        rows.append([st + marker, str(len(sub)), f"{neg}%", str(hi), str(mi), top])
    return rows


def build_report_insights(
    sub: pd.DataFrame,
    state: str,
    full_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    k: dict[str, Any] = {}
    if not sub.empty:
        sent = sub["sentiment"].astype(str).str.lower() if "sentiment" in sub.columns else pd.Series(dtype=str)
        n = max(len(sub), 1)
        k = {
            "neg_pct": round((sent == "negative").sum() / n * 100, 1),
            "pos_pct": round((sent == "positive").sum() / n * 100, 1),
            "neu_pct": round((sent == "neutral").sum() / n * 100, 1),
            "high_risk": int(sub["risk_level"].astype(str).isin(["High", "Critical"]).sum()) if "risk_level" in sub.columns else 0,
            "misinfo": int(sub["misinformation_flag"].sum()) if "misinformation_flag" in sub.columns else 0,
            "total_engagement": int(sub["engagement_total"].sum()) if "engagement_total" in sub.columns else 0,
        }

    trend_text, neg_trend_up = _sentiment_trend(sub)
    k["neg_trend_up"] = neg_trend_up
    health = compute_health_score(k)
    verdict = compute_verdict(health, k)
    vmeta = VERDICT_META[verdict]

    actions_df = build_action_candidates(sub)
    priority_rows: list[dict[str, str]] = []
    if not actions_df.empty:
        for _, r in actions_df.head(8).iterrows():
            priority_rows.append({
                "rank": str(len(priority_rows) + 1),
                "issue": str(r.get("issue_cluster", "")),
                "location": str(r.get("location") or r.get("dun") or "—"),
                "platform": str(r.get("platform", "")),
                "score": f"{float(r.get('priority_score', 0)):.2f}",
                "action_type": str(r.get("recommended_action_type", "")),
                "action": str(r.get("recommended_action", "")),
                "team": str(r.get("responsible_team", "")),
                "due": str(r.get("due_date", "")),
                "evidence": str(r.get("evidence_status", "")),
                "reason": str(r.get("recommendation_reason", "")),
                "priority_tier": "P1" if len(priority_rows) < 2 else "P2" if len(priority_rows) < 5 else "P3",
            })

    top_issue = _top_issue_name(sub)
    p1 = priority_rows[0] if priority_rows else None

    three_things = {
        "hot_issue": f"{top_issue} — isu paling kerap dalam {len(sub)} post negeri ini.",
        "must_do": (
            f"{p1['action_type']}: {p1['action'][:200]} (Pasukan: {p1['team']}, sebelum {p1['due']})"
            if p1 else "Teruskan crawl harian dan rebuild dashboard + laporan."
        ),
    }

    checklist_24h: list[str] = []
    for i, row in enumerate(priority_rows[:5], 1):
        checklist_24h.append(
            f"[ ] {row['priority_tier']} — {row['issue']} ({row['location']}): "
            f"{row['action_type']} → {row['action'][:100]}… "
            f"| {row['team']} | {row['due']}"
        )
    if not checklist_24h:
        checklist_24h = [
            "[ ] Crawl news batch pagi + rebuild dataset",
            "[ ] Semak dashboard — tukar tab negeri dan sahkan isu top 3",
            "[ ] Jana semula laporan selepas crawl petang",
        ]

    dont_do = [
        "Jangan ramal undi atau sokongan mengikut etnik — bukan polling.",
        "JANGAN balas maklumat salah tanpa semakan fakta (min. 2 sumber bebas).",
        "JANGAN serang kaum, agama, atau individu.",
        f"JANGAN campur naratif negeri lain — respons untuk {state} sahaja.",
        "JANGAN keluarkan media statement tanpa Legal/Management jika risiko High/Critical.",
    ]

    playbook = _load_playbook()
    if not actions_df.empty and not playbook.empty:
        for ic in actions_df.head(5)["issue_cluster"].unique():
            match = playbook[playbook["issue_cluster"].astype(str) == str(ic)]
            if not match.empty:
                p = str(match.iloc[0].get("prohibited_approach", ""))
                if p:
                    dont_do.append(f"{ic}: {p}")

    executive_takeaways = [
        f"Status: {verdict} ({vmeta['label']}) — Narrative Health {health}/100.",
        vmeta["action"],
        f"Sentimen: {k.get('pos_pct', 0)}% positif · {k.get('neu_pct', 0)}% neutral · {k.get('neg_pct', 0)}% negatif.",
        trend_text,
    ]
    if k.get("misinfo", 0) > 0:
        executive_takeaways.append(f"{k['misinfo']} hantaran ditanda maklumat salah — Fact Checking wajib.")
    executive_takeaways.extend(STATE_PLAYBOOK_HINTS.get(state, [])[:2])
    if ch := _dominant_channel(sub):
        executive_takeaways.append(ch + " — fokus respons di saluran ini.")

    voice = _voice_quotes(sub, 5)

    implementation_steps = [
        ("1. Terima & assign (0–4 jam)", f"Assign {p1['team'] if p1 else 'Communications'} — isu: {top_issue}"),
        ("2. Sahkan fakta (4–12 jam)", "Kumpul bukti min. 2 sumber; archive URL/screenshot ke evidence register."),
        ("3. Sediakan respons (12–18 jam)", "Rancang mesej dengan Communications — kelulusan Legal/Management wajib."),
        ("4. Terbit & monitor (18–24 jam)", f"Terbit di {p1['platform'] if p1 else 'saluran dominan'}; pantau volume 24j selepas."),
        ("5. Susulan (48–72 jam)", "Semak KPI: adakah sentimen negatif isu ini turun? Jika tidak, escalate ke Management."),
    ]

    return {
        "verdict": verdict,
        "verdict_label": vmeta["label"],
        "verdict_action": vmeta["action"],
        "verdict_color": vmeta["color"],
        "health_score": health,
        "executive_takeaways": executive_takeaways,
        "three_things": three_things,
        "issue_insights": _issue_insights(sub),
        "priority_actions": priority_rows,
        "checklist_24h": checklist_24h,
        "checklist_72h": [
            "[ ] Banding sentimen isu P1 vs hari crawl lepas",
            "[ ] Kemas kini Excel keyword jika isu tempatan baharu",
            "[ ] Jana semula laporan PDF/DOCX + edar EXCO",
            "[ ] Archive semua bukti tindakan ke dashboard evidence",
        ],
        "dont_do": dont_do,
        "voice_quotes": voice,
        "implementation_steps": implementation_steps,
        "state_comparison": build_state_comparison(full_df, state) if full_df is not None else [],
        "action_table_header": [
            "P", "Tier", "Isu", "Lokasi", "Platform", "Skor", "Tindakan", "Pasukan", "Tarikh", "Bukti",
        ],
        "action_table": [
            [
                r["rank"], r["priority_tier"], r["issue"], r["location"], r["platform"], r["score"],
                r["action"][:90], r["team"], r["due"], r["evidence"],
            ]
            for r in priority_rows
        ],
    }
