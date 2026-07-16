#!/usr/bin/env python3
"""Sync Job 1 (Pengundi Malaysia Poll) + Job 2 (Monarki K1–K5) into PRN N9 War Room dashboard."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
ACTIONS_JSON = PROTO / "n9_actions_v2.json"
SOCIAL_JSON = PROTO / "n9_social_summary.json"
BUNDLE_JSON = PROTO / "n9_production_bundle.json"
ML_JSON = PROTO / "n9_ml_predictions.json"
JOB_EX_JSON = PROTO / "n9_job_exercises.json"
JOB_METRICS_JSON = PROTO / "n9_job_crawl_metrics.json"
POLL_CSV = ROOT / "data/analyzed/Sentiment_Emotion_FACEBOOK_20260705_000328.csv"
POLL_URL = "https://www.facebook.com/story.php?story_fbid=1579205333771288&id=100050455091322"
MYT = timezone(timedelta(hours=8))

KEYWORDS = [
    {"id": "K1", "label": "Monarki luas", "report_dir": ROOT / "reports/20260705_002927_tuanku muhriz OR yang di-pertuan besar OR undang y"},
    {"id": "K2", "label": "Mukhriz vs Undang", "report_dir": ROOT / "reports/20260705_004507_Mukhriz undang negeri sembilan"},
    {"id": "K3", "label": "Undang 4 vs MB", "report_dir": ROOT / "reports/20260705_005735_undang empat menteri besar aminuddin"},
    {"id": "K4", "label": "Adat + DAP", "report_dir": ROOT / "reports/20260705_010838_adat perpatih DAP negeri sembilan"},
    {"id": "K5", "label": "Batch C09", "report_dir": ROOT / "reports/20260705_015017_adat perpatih OR undang OR tuanku muhriz negeri se"},
]

UNDANG_DUN = ["N03", "N05", "N06", "N18", "N19", "N25", "N26", "N27", "N34", "N35"]

BLOC_LABELS = {
    "pas_solo": "#1 PAS Solo",
    "umno_solo": "#2 UMNO Solo",
    "mn": "#3 MN ★",
    "pn": "#4 PN",
    "ph": "#5 PH",
    "bersama": "#6 Bersama",
    "pn_plus": "#7 PN+",
    "hung": "Risiko tiada majoriti",
}


def _parse_summary(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def pct(label: str) -> float:
        m = re.search(rf"\*\*{label}:\*\* ([\d.]+)%", text)
        return float(m.group(1)) if m else 0.0

    total_m = re.search(r"\*\*Total Data Points:\*\* ([\d,]+)", text)
    eng_m = re.search(r"Total engagement: ([\d,]+)", text)
    platforms = {}
    for m in re.finditer(r"- \*\*(\w+)\*\*: ([\d,]+) posts", text):
        platforms[m.group(1).lower()] = int(m.group(2).replace(",", ""))
    posts_total = sum(platforms.values()) or (int(total_m.group(1).replace(",", "")) if total_m else 0)
    return {
        "total": int(total_m.group(1).replace(",", "")) if total_m else posts_total,
        "posts": posts_total,
        "comments": max(0, (int(total_m.group(1).replace(",", "")) if total_m else 0) - posts_total),
        "positive": pct("Positive"),
        "neutral": pct("Neutral"),
        "negative": pct("Negative"),
        "engagement": int(eng_m.group(1).replace(",", "")) if eng_m else 0,
        "platforms": platforms,
    }


def _classify_vote(t: str) -> str:
    t = (t or "").strip().lower()
    if re.search(r"\(b\)|^b[\.\)\s,/]|^b$|tidak\s*sokong|tak\s*sokong|x\s*sokong|tak\s*setuju", t):
        return "B"
    if re.search(r"\(a\)|^a[\.\)\s,/]|^a$|a\s*sokong|sokong.*(umno|pas)|lawan.*(dap|ph|harapan)", t):
        return "A"
    if re.search(r"sokong.*(umno|pas)|lawan.*(dap|ph)|tolak.*(dap|ph)|bersatu.*melayu", t):
        return "A_soft"
    return "other"


def load_poll_stats() -> dict:
    with POLL_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    comments = [r for r in rows if str(r.get("Type", "")).lower() == "comment"]
    post = next((r for r in rows if str(r.get("Type", "")).lower() == "post"), {})
    votes = Counter(_classify_vote(r.get("Text", "")) for r in comments)
    a = votes["A"] + votes["A_soft"]
    b = votes["B"]
    decided = a + b or 1
    sent = Counter(r.get("sentiment_label") or "?" for r in comments)
    try:
        likes = int(float(post.get("likes") or 0))
        shares = int(float(post.get("shares") or 0))
        post_comments = int(float(post.get("comments_count") or 0))
        post_eng = int(float(post.get("total_engagement") or 0))
    except (TypeError, ValueError):
        likes = shares = post_comments = post_eng = 0
    if post_eng <= 0:
        post_eng = likes + post_comments + shares
    return {
        "posts": 1,
        "comments": len(comments),
        "comments_crawled": len(comments),
        "likes": likes,
        "shares": shares,
        "comments_on_post": post_comments,
        "engagement": post_eng,
        "a_count": a,
        "b_count": b,
        "a_pct": round(a / decided * 100, 1),
        "b_pct": round(b / decided * 100, 1),
        "decided": decided,
        "post_engagement": post_eng,
        "sentiment": {
            "positive": sent.get("positive", 0),
            "neutral": sent.get("neutral", 0),
            "negative": sent.get("negative", 0),
        },
        "url": POLL_URL,
    }


def load_kw_stats() -> list[dict]:
    out = []
    for kw in KEYWORDS:
        s = _parse_summary(kw["report_dir"] / "EXECUTIVE_SUMMARY.md")
        s.update(kw)
        out.append(s)
    return out


def build_job_bloc7_effects(poll: dict, kw_stats: list[dict]) -> dict:
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    # Nudges in percentage points on P(majoriti) bar — qualitative from crawl signals
    nudges = {
        "mn": 3,
        "ph": -2,
        "pas_solo": 1,
        "umno_solo": -1,
        "pn": 1,
        "pn_plus": 1,
        "bersama": 0,
        "hung": 1 if k3["negative"] >= 50 else 0,
    }
    effects = []
    for bloc_id, delta in nudges.items():
        if delta == 0 and bloc_id == "bersama":
            continue
        sign = f"+{delta}" if delta > 0 else str(delta)
        label = BLOC_LABELS.get(bloc_id, bloc_id)
        if bloc_id == "mn":
            reason = f"Job 1 poll ~{poll['a_pct']}% sokong MN lawan PH"
        elif bloc_id == "ph":
            reason = f"Job 1 poll tolak PH + Job 2 K3 {k3['negative']:.0f}% neg MB/adat"
        elif bloc_id == "pas_solo":
            reason = "Job 1 mobilize Pro-PAS · Job 2 krisis adat segmen Melayu-Islam"
        elif bloc_id == "umno_solo":
            reason = "Job 2 istana — UMNO dalam kerajaan negeri N9"
        elif bloc_id in ("pn", "pn_plus"):
            reason = "Job 1 signal gabungan anti-PH"
        elif bloc_id == "hung":
            reason = f"Job 2 polarisasi K3 {k3['negative']:.0f}% — risiko tiada majoriti"
        else:
            reason = "Neutral"
        effects.append({"bloc_id": bloc_id, "label": label, "nudge_pp": delta, "sign": sign, "reason": reason})

    return {
        "source": "Job 1 Poll + Job 2 Monarki K1–K5",
        "updated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M"),
        "nudges_pp": nudges,
        "effects": effects,
        "crawlAdjustments": [
            f"Job 1 Poll: MN lawan PH ~{poll['a_pct']}% ({poll['decided']} komen A/B) → #3 MN (+3pp)",
            f"Job 1 Poll: Tolak PH ~{poll['b_pct']}% → #5 PH (-2pp)",
            f"Job 2 K5: {k5['total']:,} rekod · {k5['engagement']:,} engagement · neg {k5['negative']:.0f}%",
            f"Job 2 K3 puncak: Undang 4 vs MB {k3['negative']:.0f}% neg → elak politisasi istana",
            "MN (#3): Istana/adat handled well → laluan MN Melayu rural (+5pp legacy + +3pp poll)",
            "PH (#5): Frame adat+DAP K4 + MB zone → (-2pp poll + -5pp istana legacy)",
            "PAS Solo (#1): Anti-PH poll + adat segmen (+1pp + +4pp legacy)",
            "Risiko hung: K3 polarisasi → (+1pp jika mishandle adat)",
        ],
        "mn_expected_seats_baseline": 22.9,
        "note": "Nudges = penyesuaian P(majoriti) bar · bukan kerusi automatik · overlap K1–K5",
    }


def build_ml_job_impact(poll: dict, kw_stats: list[dict]) -> dict:
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    total_records = sum(s["total"] for s in kw_stats)
    total_engagement = sum(s["engagement"] for s in kw_stats)
    return {
        "updated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M"),
        "summary": (
            f"Job 1: {poll['posts']} post · {poll['comments']} komen · {poll['engagement']:,} eng · "
            f"{poll['a_pct']}% sokong MN | Job 2: {len(kw_stats)} KW · {total_records:,} rekod · "
            f"{total_engagement:,} eng"
        ),
        "job1_poll": {
            "posts": poll["posts"],
            "comments": poll["comments"],
            "likes": poll["likes"],
            "shares": poll["shares"],
            "engagement": poll["engagement"],
            "sokong_mn_pct": poll["a_pct"],
            "tolak_pct": poll["b_pct"],
            "decided_ab": poll["decided"],
            "sentiment": poll["sentiment"],
        },
        "job2_monarki": {
            "keywords": len(kw_stats),
            "total_records_overlap": total_records,
            "total_engagement_overlap": total_engagement,
            "k5_records": k5["total"],
            "k5_engagement": k5["engagement"],
            "peak_neg_kw": k3["id"],
            "peak_neg_pct": k3["negative"],
            "per_keyword": [
                {
                    "id": s["id"],
                    "label": s["label"],
                    "posts": s.get("posts", s["total"]),
                    "records": s["total"],
                    "engagement": s["engagement"],
                    "neg_pct": s["negative"],
                    "pos_pct": s["positive"],
                    "platforms": s.get("platforms", {}),
                }
                for s in kw_stats
            ],
        },
        "ml_flags": {
            "socmed_neg_boost": "Undang-zone DUN — monitor, bukan auto-flip",
            "feature_impact": "scenario_pas_pn · pct_melayu · socmed_neg_pct · socmed_engagement",
            "cv_accuracy_rf": "~94%",
            "mn_bloc_expected": "~22.9 kerusi (majoriti 19)",
        },
        "seat_risk": [
            {"code": "N05", "risk": "critical", "action": "JANGAN campur adat · pertahan MN murni (+843 tipis)"},
            {"code": "N19", "risk": "high", "action": "Monitor spike · soft touch zon Undang"},
            {"code": "N03", "risk": "medium", "action": "Neutral istana · jangan provokasi"},
            {"code": "N14", "risk": "medium", "action": "JANGAN serang via adat · fokus flip muafakat"},
        ],
        "prescriptive_additions": [
            {
                "rank": 0,
                "urgency": "immediate",
                "domain": "job2_monarki",
                "title": f"Monitor adat N19/N05 — K3 {k3['negative']:.0f}% neg",
                "detail": f"Job 2 crawl {k5['total']:,} rekod · elak politisasi istana · ML pasWinProb N05 70% N19 38%",
                "entity": "N19",
                "score": 0.95,
                "ml_support": "job_crawl+pasWinProb",
            },
            {
                "rank": 0,
                "urgency": "immediate",
                "domain": "job1_poll",
                "title": f"Echo poll MN {poll['a_pct']}% — {poll['engagement']:,} engagement",
                "detail": f"{poll['comments']} komen · {poll['decided']} A/B jelas · pisah dari debat istana",
                "entity": "N9",
                "score": 0.92,
                "ml_support": "poll_signal",
            },
        ],
    }


def build_job_metrics(poll: dict, kw_stats: list[dict], bloc7: dict, ml_impact: dict) -> dict:
    now = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    return {
        "meta": {"generated": now, "state": "N9", "jobs": 2},
        "totals": {
            "posts_job1": poll["posts"],
            "comments_job1": poll["comments"],
            "engagement_job1": poll["engagement"],
            "records_job2_overlap": sum(s["total"] for s in kw_stats),
            "engagement_job2_overlap": sum(s["engagement"] for s in kw_stats),
            "records_job2_k5": k5["total"],
            "engagement_job2_k5": k5["engagement"],
        },
        "job1": {
            "id": "JOB-N9-01",
            "title": "Pengundi Malaysia Poll",
            "platform": "Facebook",
            "url": POLL_URL,
            "posts": poll["posts"],
            "comments": poll["comments"],
            "likes": poll["likes"],
            "shares": poll["shares"],
            "engagement": poll["engagement"],
            "sokong_mn_pct": poll["a_pct"],
            "tolak_pct": poll["b_pct"],
            "decided_ab": poll["decided"],
            "sentiment": poll["sentiment"],
        },
        "job2": {
            "id": "JOB-N9-02",
            "title": "Monarki & Adat K1–K5",
            "keywords": [
                {
                    "id": s["id"],
                    "label": s["label"],
                    "posts": s.get("posts", s["total"]),
                    "records": s["total"],
                    "engagement": s["engagement"],
                    "neg_pct": s["negative"],
                    "pos_pct": s["positive"],
                    "neu_pct": s["neutral"],
                    "platforms": s.get("platforms", {}),
                }
                for s in kw_stats
            ],
        },
        "bloc7_effects": bloc7,
        "ml_impact": ml_impact,
    }


def build_job_exercises(poll: dict, kw_stats: list[dict]) -> list[dict]:
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    now = datetime.now(MYT).strftime("%Y-%m-%d %H:%M")
    return [
        {
            "id": "JOB-N9-01",
            "title": "Pengundi Malaysia Poll — MN vs PH",
            "status": "siap",
            "completed_at": "2026-07-05",
            "type": "cula_digital_poll",
            "platform": "Facebook",
            "url": POLL_URL,
            "posts": poll["posts"],
            "comments": poll["comments"],
            "likes": poll["likes"],
            "shares": poll["shares"],
            "engagement": poll["engagement"],
            "stats": {
                "posts": poll["posts"],
                "sokong_mn_pct": poll["a_pct"],
                "tolak_pct": poll["b_pct"],
                "comments": poll["comments"],
                "likes": poll["likes"],
                "shares": poll["shares"],
                "engagement": poll["engagement"],
                "decided_ab": poll["decided"],
            },
            "bloc7_nudge": {"mn": 3, "ph": -2},
            "insight": f"1 post · {poll['comments']} komen · {poll['engagement']:,} eng · ~{poll['a_pct']}% sokong MN",
            "pptx": "Pengundi_Malaysia_Poll_N9_Insight_Tindakan.pptx",
            "report_dir": "reports/20260705_000328_httpswwwfacebookcomstoryphpstory_fbid1579205333771",
            "synced_at": now,
        },
        {
            "id": "JOB-N9-02",
            "title": "Monarki & Adat N9 — Keyword K1–K5",
            "status": "siap",
            "completed_at": "2026-07-05",
            "type": "keyword_crawl",
            "platform": "FB + X + News",
            "posts_total_overlap": sum(s.get("posts", s["total"]) for s in kw_stats),
            "records_total_overlap": sum(s["total"] for s in kw_stats),
            "engagement_total_overlap": sum(s["engagement"] for s in kw_stats),
            "keywords": [
                {
                    "id": s["id"],
                    "label": s["label"],
                    "posts": s.get("posts", s["total"]),
                    "records": s["total"],
                    "neg_pct": s["negative"],
                    "engagement": s["engagement"],
                    "platforms": s.get("platforms", {}),
                }
                for s in kw_stats
            ],
            "stats": {
                "keywords": len(kw_stats),
                "records_k5": k5["total"],
                "posts_k5": k5.get("posts", k5["total"]),
                "neg_pct_peak": max(s["negative"] for s in kw_stats),
                "neg_peak_kw": k3["id"],
                "engagement_k5": k5["engagement"],
                "engagement_overlap": sum(s["engagement"] for s in kw_stats),
                "undang_dun": UNDANG_DUN,
            },
            "bloc7_nudge": {"mn": 5, "ph": -5, "pas_solo": 4, "hung": 1},
            "insight": f"K5 {k5['engagement']:,} eng · overlap K1–K5 {sum(s['engagement'] for s in kw_stats):,} eng",
            "pptx": "MN_N9_Strategic_Brief_Monarki_Poll_Insight_Tindakan.pptx",
            "report_dir": "reports/20260705_015017_adat perpatih OR undang OR tuanku muhriz negeri se",
            "synced_at": now,
        },
    ]


def build_pulse_digital(poll: dict, kw_stats: list[dict]) -> list[dict]:
    rows = [
        {
            "id": "PULSE-N9-PM-POLL",
            "dun": "N9",
            "seat": "Negeri Sembilan",
            "platform": "Facebook",
            "stimulus": "Post Pengundi Malaysia — poll MN vs PH (A/B komen)",
            "status": "crawl_done",
            "sentiment_summary": f"~{poll['a_pct']}% sokong MN · {poll['b_pct']}% tolak",
            "emotion_summary": "Galvanize · debat · Pro-PAS",
            "issue_cluster": "Gabungan MN vs PH",
            "posts": poll["posts"],
            "comments": poll["comments"],
            "likes": poll["likes"],
            "shares": poll["shares"],
            "engagement": poll["engagement"],
            "confidence": 0.85,
            "recommended_action": "Echo poll di group kempen · pisahkan dari debat istana · jangan over-claim SPR.",
            "job_id": "JOB-N9-01",
            "url": POLL_URL,
        },
    ]
    for s in kw_stats:
        rows.append(
            {
                "id": f"PULSE-N9-{s['id']}",
                "dun": "N9",
                "seat": "Zon Undang",
                "platform": "Multi",
                "stimulus": s["label"],
                "status": "crawl_done",
                "sentiment_summary": f"{s['negative']:.1f}% neg · {s['positive']:.1f}% pos",
                "emotion_summary": "Polarizing" if s["negative"] >= 50 else "Mixed",
                "issue_cluster": "Monarki & Adat",
                "posts": s.get("posts", s["total"]),
                "records": s["total"],
                "engagement": s["engagement"],
                "confidence": 0.78,
                "recommended_action": "Monitor" if s["negative"] < 50 else "Alert P1 — elak politisasi istana",
                "job_id": "JOB-N9-02",
                "platforms": s.get("platforms", {}),
            }
        )
    return rows


def build_job_actions(poll: dict, kw_stats: list[dict]) -> list[dict]:
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    return [
        {
            "id": "ACT-N9-J1-001",
            "title": f"Echo poll Pengundi Malaysia ({poll['a_pct']}% · {poll['engagement']:,} eng)",
            "category": "digital",
            "priority": "p1",
            "status": "baru",
            "owner": "Comms PAS N9",
            "due": "48 jam",
            "dun": "N9",
            "seat": "Negeri Sembilan",
            "locality": "Semua platform",
            "reason": f"1 post · {poll['comments']} komen · {poll['a_pct']}% sokong MN — #3 MN +3pp scenario.",
            "evidence": [
                f"{poll['decided']} komen A/B jelas",
                f"{poll['likes']:,} likes · {poll['shares']} shares",
                f"Engagement {poll['engagement']:,}",
            ],
            "recommended_steps": [
                "Edar 3 mesej ringkas BM (poll + footnote bukan SPR).",
                "Pisahkan naratif poll dari debat istana/adat.",
                "Pantau komen tolak (B) dan balas dengan sopan.",
            ],
            "impact_metric": "Mesej diedar ke 20 ketua kerusi MN",
            "job_id": "JOB-N9-01",
        },
        {
            "id": "ACT-N9-J2-001",
            "title": "Brief ketua 20 kerusi MN: garis «poll MN + hormat adat»",
            "category": "rapid_response",
            "priority": "p1",
            "status": "baru",
            "owner": "Comms HQ",
            "due": "Hari ini",
            "dun": "N9",
            "seat": "Negeri Sembilan",
            "locality": "WhatsApp HQ",
            "reason": f"K3 {k3['negative']:.0f}% neg · K5 {k5['total']:,} rekod · ML flag N05/N19.",
            "evidence": ["5 keyword crawl siap K1–K5", "10 DUN zon Undang micro-target", "7-bloc MN +5pp istana legacy"],
            "recommended_steps": [
                "Hantar 1-pager doc WhatsApp (DO/DON'T adat).",
                "JANGAN serang MB guna «penderhaka Undang».",
                "Monitor K2/K3 daily — spike >60% neg → alert.",
            ],
            "impact_metric": "Brief diedar ke 20 ketua kerusi MN",
            "job_id": "JOB-N9-02",
        },
        {
            "id": "ACT-N9-J2-002",
            "title": "Monitor monarki/adat — 10 DUN zon Undang",
            "category": "digital",
            "priority": "p1",
            "status": "baru",
            "owner": "Digital War Room",
            "due": "2× sehari",
            "dun": "N19",
            "seat": "Johol",
            "locality": "Jelebu · Johol · Rembau · Tampin",
            "reason": "Micro-target soft comms sahaja — bukan 32 DUN.",
            "evidence": [f"K5 {k5['engagement']:,} engagement", "N19 pasWinProb 38%", "N05 pertahan tipis +843"],
            "recommended_steps": [
                "Check pulse PULSE-N9-K2/K3/K5 setiap pagi & petang.",
                "Soft touch N19, N03, N05 — elak provokasi.",
                "Log spike ke Action Center.",
            ],
            "impact_metric": "2 laporan monitor/hari untuk 10 DUN Undang",
            "job_id": "JOB-N9-02",
        },
        {
            "id": "ACT-N9-J2-003",
            "title": "Siap 1-pager edukasi adat N9 (bukan serangan parti)",
            "category": "rapid_response",
            "priority": "p2",
            "status": "baru",
            "owner": "Comms + legal adat",
            "due": "48 jam",
            "dun": "N9",
            "seat": "Negeri Sembilan",
            "locality": "HQ",
            "reason": "Counter frame K4 (adat+DAP) dengan edukasi, bukan debat kasar.",
            "evidence": ["K4 48% neg · 2,838 rekod", "PH #5 -2pp poll + -5pp istana"],
            "recommended_steps": ["Draft fakta Undang 4, DKU, peranan YDPB.", "Review legal/adat.", "Edar ke ketua DUN zon Undang."],
            "impact_metric": "1-pager siap + diedar",
            "job_id": "JOB-N9-02",
        },
    ]


def merge_actions(existing: list[dict], new_job: list[dict]) -> list[dict]:
    job_ids = {a["id"] for a in new_job}
    kept = [a for a in existing if a.get("id") not in job_ids and not str(a.get("id", "")).startswith("ACT-N9-J")]
    return kept + new_job


def merge_pulse(existing: list[dict], new_pulse: list[dict]) -> list[dict]:
    job_pulse_ids = {p["id"] for p in new_pulse}
    kept = [
        p
        for p in existing
        if p.get("id") not in job_pulse_ids
        and not str(p.get("id", "")).startswith("PULSE-N9-K")
        and p.get("id") != "PULSE-N9-PM-POLL"
    ]
    return new_pulse + kept


def merge_bloc7_nudges(existing: dict | None, job_nudges: dict) -> dict:
    base = dict(existing or {})
    for k, v in job_nudges.items():
        base[k] = base.get(k, 0) + v
    return base


def update_daily_briefing(poll: dict, kw_stats: list[dict]) -> dict:
    k3 = next(s for s in kw_stats if s["id"] == "K3")
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    total_eng_j2 = sum(s["engagement"] for s in kw_stats)
    return {
        "headline": f"Job 1+2 sync: {poll['comments']} komen · {poll['engagement']:,} eng poll · K5 {k5['total']:,} rekod · 7-bloc + ML updated.",
        "what_changed": [
            f"Job 1: 1 post · {poll['comments']} komen · {poll['likes']:,} likes · {poll['engagement']:,} eng · {poll['a_pct']}% sokong MN.",
            f"Job 2: K1–K5 · {total_eng_j2:,} eng (overlap) · K5 {k5['total']:,} rekod · K3 neg {k3['negative']:.0f}%.",
            "7-bloc scenario nudges dikemaskini (#3 MN +3pp poll · #5 PH -2pp).",
            "ML Analytics: seat risk N05/N19 + prescriptive job actions.",
        ],
        "next_24h": [
            "Brief 20 ketua kerusi MN — garis poll + hormat adat.",
            f"Echo poll PM ({poll['a_pct']}%) · {poll['engagement']:,} engagement.",
            "Monitor K2/K3/K5 — alert jika neg >60%.",
        ],
        "risk": "Politikkan istana (K3 54% neg) atau over-claim poll tanpa cula lapangan.",
    }


def update_istana_signal(kw_stats: list[dict]) -> dict:
    k5 = next(s for s in kw_stats if s["id"] == "K5")
    pos = int(round(k5["total"] * k5["positive"] / 100))
    neg = int(round(k5["total"] * k5["negative"] / 100))
    neu = max(0, k5["total"] - pos - neg)
    return {
        "posts": k5.get("posts", k5["total"]),
        "records": k5["total"],
        "engagement": float(k5["engagement"]),
        "pos": pos,
        "neg": neg,
        "neu": neu,
        "blamePosts": neg,
        "neg_pct": k5["negative"],
        "source": "Job 2 K1–K5 crawl (K5 batch primary · overlap noted)",
        "updated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M"),
    }


def patch_json(path: Path, mutator):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutator(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_dashboard() -> dict:
    poll = load_poll_stats()
    kw_stats = load_kw_stats()
    bloc7 = build_job_bloc7_effects(poll, kw_stats)
    ml_impact = build_ml_job_impact(poll, kw_stats)
    metrics = build_job_metrics(poll, kw_stats, bloc7, ml_impact)
    exercises = build_job_exercises(poll, kw_stats)
    pulse = build_pulse_digital(poll, kw_stats)
    job_actions = build_job_actions(poll, kw_stats)
    istana = update_istana_signal(kw_stats)
    k5_batch = next(s for s in kw_stats if s["id"] == "K5")
    now = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")

    JOB_METRICS_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JOB_EX_JSON.write_text(
        json.dumps({"meta": {"generated": now, "state": "N9"}, "exercises": exercises}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    def patch_actions(data):
        data.setdefault("meta", {})["generated"] = now
        data["meta"]["job_sync"] = now
        data["jobExercises"] = exercises
        data["jobCrawlMetrics"] = metrics
        data["actions"] = merge_actions(data.get("actions") or [], job_actions)
        data["pulseDigital"] = merge_pulse(data.get("pulseDigital") or [], pulse)
        data["dailyBriefing"] = update_daily_briefing(poll, kw_stats)

    patch_json(ACTIONS_JSON, patch_actions)

    def patch_social(data):
        data.setdefault("meta", {})["jobSync"] = now
        signals = data.setdefault("signals", {})
        signals["n9IstanaAdat"] = istana
        signals["jobCrawlMetrics"] = metrics
        data["jobCrawlMetrics"] = metrics

        hybrid = data.setdefault("demographics", {}).setdefault("hybrid", {})
        hybrid["bloc7Nudges"] = merge_bloc7_nudges(hybrid.get("bloc7Nudges"), bloc7["nudges_pp"])
        hybrid["jobBloc7Effects"] = bloc7
        hybrid["jobCrawlTotals"] = metrics["totals"]

        cf = data.setdefault("coalitionFormation", {})
        cs = cf.setdefault("crawlSignals", {})
        cs["job1Poll"] = metrics["job1"]
        cs["job2Monarki"] = {
            "keywords": len(kw_stats),
            "records_k5": k5_batch["total"],
            "posts_k5": k5_batch.get("posts", k5_batch["total"]),
            "engagement_k5": k5_batch["engagement"],
            "records_overlap": sum(s["total"] for s in kw_stats),
            "engagement_overlap": sum(s["engagement"] for s in kw_stats),
            "per_keyword": metrics["job2"]["keywords"],
        }
        cs["n9IstanaAdat"] = istana

        adj = data.get("crawlAdjustments") or []
        job_adj = [a for a in bloc7["crawlAdjustments"] if a not in adj]
        data["crawlAdjustments"] = job_adj + adj
        dq = data.setdefault("dataQuality", {})
        dq["istanaAdatPosts"] = istana["posts"]
        dq["istanaAdatRecords"] = istana["records"]
        dq["istanaAdatEngagement"] = int(istana["engagement"])
        dq["istanaAdatBlamePosts"] = istana["blamePosts"]
        dq["istanaAdatSource"] = istana["source"]
        dq["job1PollComments"] = poll["comments"]
        dq["job1PollEngagement"] = poll["engagement"]
        dq["job1PollLikes"] = poll["likes"]
        dq["job2RecordsK5"] = k5_batch["total"]
        dq["job2EngagementK5"] = k5_batch["engagement"]
        dq["job2EngagementOverlap"] = sum(s["engagement"] for s in kw_stats)
        dq["istanaAdatEngagementK5"] = k5_batch["engagement"]

    patch_json(SOCIAL_JSON, patch_social)

    if BUNDLE_JSON.exists():

        def patch_bundle(data):
            ss = data.get("socialSummary") or {}
            if isinstance(ss, dict):
                sig = ss.setdefault("signals", {})
                sig["n9IstanaAdat"] = istana
                sig["jobCrawlMetrics"] = metrics
                hybrid = ss.setdefault("demographics", {}).setdefault("hybrid", {})
                hybrid["bloc7Nudges"] = merge_bloc7_nudges(hybrid.get("bloc7Nudges"), bloc7["nudges_pp"])
                hybrid["jobBloc7Effects"] = bloc7
                hybrid["jobCrawlTotals"] = metrics["totals"]
                dq = ss.setdefault("dataQuality", {})
                dq["istanaAdatPosts"] = istana["posts"]
                dq["istanaAdatEngagement"] = int(istana["engagement"])
                dq["job1PollComments"] = poll["comments"]
                dq["job1PollEngagement"] = poll["engagement"]
            data["jobExercises"] = exercises
            data["jobCrawlMetrics"] = metrics
            data.setdefault("meta", {})["jobSync"] = now

        patch_json(BUNDLE_JSON, patch_bundle)

    if ML_JSON.exists():

        def patch_ml(data):
            data["job_crawl_impact"] = ml_impact
            data["generated_at"] = now
            additions = ml_impact.get("prescriptive_additions") or []
            existing = data.get("prescriptive_actions") or []
            # Prepend job actions, dedupe by title
            titles = {a.get("title") for a in additions}
            kept = [a for a in existing if a.get("title") not in titles]
            data["prescriptive_actions"] = additions + kept

        patch_json(ML_JSON, patch_ml)

    return {
        "poll": poll,
        "kw_count": len(kw_stats),
        "exercises": len(exercises),
        "pulse": len(pulse),
        "actions": len(job_actions),
        "bloc7_nudges": bloc7["nudges_pp"],
    }


def main() -> None:
    result = sync_dashboard()
    print("✅ Dashboard synced — Job 1 + Job 2 (full metrics + 7-bloc + ML)")
    print(
        f"   Job1: {result['poll']['comments']} komen · {result['poll']['engagement']:,} eng · "
        f"{result['poll']['a_pct']}% MN"
    )
    print(f"   Job2: {result['kw_count']} KW · {result['pulse']} pulse · bloc7 {result['bloc7_nudges']}")
    print(f"   {JOB_METRICS_JSON}")
    print(f"   {ACTIONS_JSON}")
    print(f"   {ML_JSON}")


if __name__ == "__main__":
    main()
