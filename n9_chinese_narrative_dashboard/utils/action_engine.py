"""Rule-based action recommendations and priority scoring."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RISK_WEIGHT = {"Low": 0.25, "Medium": 0.50, "High": 0.75, "Critical": 1.0}

ACTION_TYPES = [
    "Semakan fakta", "Penjelasan dasar", "Respons perkhidmatan", "Lawatan kawasan",
    "Dialog komuniti terbuka", "Sidang media", "Kandungan penerangan", "Infografik fakta",
    "Video penerangan", "Soalan lazim", "Penyelesaian aduan", "Pemantauan lanjut",
    "Tiada tindakan segera",
]

ACTION_STATUS = [
    "Baharu", "Dalam Semakan", "Fakta Sedang Disahkan", "Tindakan Dirancang",
    "Sedang Dilaksanakan", "Selesai", "Ditangguhkan", "Tidak Memerlukan Tindakan",
]

TEAMS = [
    "Social Listening", "Data Analysis", "Fact Checking", "Policy",
    "Communications", "Local Operations", "Community Engagement",
    "Legal Review", "Management Approval",
]

RULES: list[dict] = [
    {
        "match": lambda ic, **k: ic == "Water Supply",
        "type": "Respons perkhidmatan",
        "text": "Semak aduan dengan agensi berkaitan, kenal pasti lokasi terjejas, dapatkan tempoh pemulihan dan keluarkan kemas kini perkhidmatan yang boleh disahkan.",
        "team": "Local Operations",
        "reason": "Isu bekalan air dengan sentimen negatif tinggi.",
    },
    {
        "match": lambda ic, **k: ic == "Road and Traffic",
        "type": "Penyelesaian aduan",
        "text": "Kenal pasti lokasi jalan atau trafik yang disebut, semak bidang kuasa agensi dan sediakan status tindakan serta garis masa pembaikan.",
        "team": "Local Operations",
        "reason": "Isu jalan/trafik memerlukan tindakan perkhidmatan tempatan.",
    },
    {
        "match": lambda ic, **k: ic == "Cost of Living",
        "type": "Penjelasan dasar",
        "text": "Sediakan penerangan dasar, bantuan yang tersedia, saluran permohonan dan data kos sara hidup yang disahkan.",
        "team": "Policy",
        "reason": "Isu kos sara hidup — fokus maklumat dasar dan bantuan disahkan.",
    },
    {
        "match": lambda ic, **k: ic == "Chinese Education",
        "type": "Dialog komuniti terbuka",
        "text": "Sediakan penerangan dasar pendidikan yang tepat, rekod peruntukan yang boleh disahkan dan sesi dialog terbuka bersama pihak sekolah serta komuniti.",
        "team": "Policy",
        "reason": "Isu pendidikan Cina — penjelasan dasar dan dialog terbuka.",
    },
    {
        "match": lambda ic, **k: ic == "SME and Business",
        "type": "Kandungan penerangan",
        "text": "Sediakan maklumat lesen, geran, bantuan digitalisasi, kos pematuhan dan saluran penyelesaian masalah peniaga.",
        "team": "Policy",
        "reason": "Isu PKS/peniaga — maklumat perkhidmatan dan bantuan.",
    },
    {
        "match": lambda ic, **k: ic in ("PAS Factor", "DAP Performance", "MCA Relevance", "PH-BN Relationship", "Gerakan and PN"),
        "type": "Penjelasan dasar",
        "text": "Kenal pasti kebimbangan sebenar di sebalik naratif, semak fakta dan sediakan penjelasan dasar serta kedudukan rasmi tanpa menyerang kaum, agama atau individu.",
        "team": "Communications",
        "reason": "Naratif politik — penjelasan dasar berasaskan fakta, bukan serangan perkauman.",
    },
    {
        "match": lambda ic, **k: k.get("misinformation"),
        "type": "Semakan fakta",
        "text": "Jangan respons serta-merta. Sahkan dakwaan melalui sekurang-kurangnya dua sumber yang boleh dipercayai dan rekodkan bukti sebelum menyediakan pembetulan.",
        "team": "Fact Checking",
        "reason": "Bendera maklumat salah — wajib pengesahan bukti.",
    },
    {
        "match": lambda ic, **k: k.get("risk") == "Critical",
        "type": "Semakan fakta",
        "text": "Risiko kritikal — wajib semakan undang-undang/komunikasi, lampiran bukti dan kelulusan pengurus sebelum sebarang tindakan.",
        "team": "Legal Review",
        "reason": "Tahap risiko Critical — semakan manusia wajib.",
    },
]


def recommend(issue_cluster: str, neg_pct: float, misinformation: bool, risk_level: str) -> tuple[str, str, str]:
    """Return (action_type, recommended_action, reason)."""
    for rule in RULES:
        try:
            if rule["match"](issue_cluster, misinformation=misinformation, risk=risk_level, neg=neg_pct):
                return rule["type"], rule["text"], rule["reason"]
        except Exception:
            continue
    if neg_pct >= 60:
        return (
            "Pemantauan lanjut",
            "Pantau naratif berkembang; sediakan penjelasan berdasarkan isu perkhidmatan awam jika disahkan.",
            "Sentimen negatif tinggi — pemantauan dan penjelasan isu awam.",
        )
    return (
        "Tiada tindakan segera",
        "Teruskan pemantauan; tiada tindakan operasi segera diperlukan setelah semakan awal.",
        "Isu tidak memenuhi ambang tindakan segera.",
    )


def priority_score(volume: float, engagement: float, neg_pct: float, growth: float, risk: str) -> float:
    rw = RISK_WEIGHT.get(str(risk), 0.25)
    # Normalisation handled externally; here assume 0-1 inputs
    return round(
        0.25 * volume + 0.20 * engagement + 0.20 * neg_pct + 0.20 * growth + 0.15 * rw,
        3,
    )


def _growth_pct(grp: pd.DataFrame) -> float:
    if "published_at" not in grp.columns or grp["published_at"].isna().all():
        return 0.0
    grp = grp.dropna(subset=["published_at"]).sort_values("published_at")
    if len(grp) < 4:
        return 0.0
    mid = grp["published_at"].iloc[len(grp) // 2]
    early = len(grp[grp["published_at"] < mid])
    late = len(grp[grp["published_at"] >= mid])
    return round((late - early) / max(early, 1) * 100, 1)


def build_action_candidates(posts: pd.DataFrame) -> pd.DataFrame:
    """Generate prioritised action rows from filtered posts."""
    if posts is None or posts.empty:
        return pd.DataFrame()

    try:
        from backend.nim_safety import enrich_posts_with_safety  # noqa: WPS433
        posts = enrich_posts_with_safety(posts)
    except Exception:
        pass

    rows = []
    group_cols = ["issue_cluster", "dun_code", "constituency", "platform"]
    for keys, grp in posts.groupby([c for c in group_cols if c in posts.columns], dropna=False):
        if isinstance(keys, tuple):
            ic, dun, loc, plat = (list(keys) + ["", "", ""])[:4]
        else:
            ic, dun, loc, plat = keys, "", "", ""
        if not str(ic).strip() or str(ic).lower() == "nan":
            continue
        vol = len(grp)
        eng = float(grp["engagement_total"].sum()) if "engagement_total" in grp.columns else 0
        neg_pct = (
            (grp["sentiment"].astype(str).str.lower() == "negative").mean() * 100
            if "sentiment" in grp.columns else 0
        )
        growth = _growth_pct(grp)
        sent_mode = grp["sentiment"].mode() if "sentiment" in grp.columns else pd.Series(dtype=str)
        risk_mode = grp["risk_level"].mode() if "risk_level" in grp.columns and len(grp) else pd.Series(dtype=str)
        risk = str(risk_mode.iloc[0]) if len(risk_mode) else "Low"
        if "nim_safety_flagged" in grp.columns and grp["nim_safety_flagged"].astype(str).str.lower().isin(["true", "1"]).any():
            risk = "Critical"
        misinfo = bool(grp["misinformation_flag"].any()) if "misinformation_flag" in grp.columns else False
        safety_categories = ""
        if "nim_safety_categories" in grp.columns:
            safety_categories = ",".join(sorted({str(v) for v in grp["nim_safety_categories"].dropna() if str(v).strip()}))
        atype, action, reason = recommend(str(ic), neg_pct, misinfo, risk)
        if safety_categories:
            reason = f"{reason} Nemotron Safety: {safety_categories}."
        sample = grp.nlargest(1, "engagement_total").iloc[0] if "engagement_total" in grp.columns and len(grp) else grp.iloc[0]
        narrative = str(sample.get("post_text", ""))[:120]
        aid = f"ACT-{str(ic)[:8].replace(' ', '')}-{str(dun or loc)[:6]}-{str(plat)[:4]}".upper().replace(",", "")
        rows.append({
            "action_id": aid,
            "issue_cluster": ic,
            "detected_narrative": narrative,
            "narrative_summary": narrative[:80] + ("…" if len(narrative) > 80 else ""),
            "location": loc or sample.get("constituency", ""),
            "dun": dun or sample.get("dun_code", ""),
            "platform": plat or sample.get("platform", ""),
            "volume": vol,
            "sentiment": sent_mode.iloc[0] if len(sent_mode) else "neutral",
            "negative_percentage": round(neg_pct, 1),
            "total_engagement": int(eng),
            "growth_percentage": growth,
            "risk_level": risk,
            "evidence_status": "Perlu bukti" if misinfo or str(risk) in ("High", "Critical") else "Sebahagian",
            "recommended_action_type": atype,
            "recommended_action": action,
            "recommendation_reason": reason,
            "responsible_team": "Fact Checking" if misinfo else "Communications",
            "due_date": (datetime.now() + timedelta(days=3 if str(risk) in ("High", "Critical") else 7)).strftime("%Y-%m-%d"),
            "action_status": "Baharu",
            "verification_required": str(risk) in ("High", "Critical") or misinfo,
            "notes": "",
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    for col, mx in [("volume", "volume"), ("total_engagement", "total_engagement"), ("negative_percentage", "negative_percentage"), ("growth_percentage", "growth_percentage")]:
        m = out[mx].max() or 1
        out[f"n_{mx}"] = out[mx] / m
    out["priority_score"] = out.apply(
        lambda r: priority_score(r["n_volume"], r["n_total_engagement"], r["n_negative_percentage"] / 1.0, max(r["n_growth_percentage"], 0), r["risk_level"]),
        axis=1,
    )
    return out.sort_values("priority_score", ascending=False).drop(columns=[c for c in out.columns if c.startswith("n_")], errors="ignore")
