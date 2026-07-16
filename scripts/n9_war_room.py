#!/usr/bin/env python3
"""PRN N9 War Room — playbook, crawl triggers, RAG briefing, agent queue (Fasa A–E)."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import PAS_BREAK, SHARED, reference, reports, resolve_existing  # noqa: E402

MASTER_DIR = PAS_BREAK / "master"
OUT_JSON = reports("N9") / "war_room/n9_war_room.json"
OUT_CSV = resolve_existing(
    reports("N9") / "war_room/n9_war_room_actions.csv",
    ROOT / "JITP_2026/Master_File/n9_war_room_actions.csv",
)
OUT_BRIEFING = reports("N9") / "war_room/n9_war_room_briefing.json"
OUT_WHATSAPP = reports("N9") / "war_room/n9_hari_ini_whatsapp.txt"
NEWS_ANALYZED_JSON = resolve_existing(
    reference("N9") / "prn_n9_news_analyzed_summary.json",
    ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_news_analyzed_summary.json",
)

NS_PATTERN = re.compile(
    r"negeri sembilan|n\.?\s*sembilan|prn.*sembilan|sembilan.*prn|dun sembilan|prn n9",
    re.I,
)

CATEGORY_META = {
    "defend": {"label": "Pertahan", "color": "defend", "resource": "Tinggi", "icon": "shield"},
    "winnable": {"label": "Boleh Menang", "color": "winnable", "resource": "Tinggi", "icon": "target"},
    "tough": {"label": "Sukar / Lawan Kuat", "color": "tough", "resource": "Sederhana", "icon": "alert-triangle"},
    "not_priority": {"label": "Bukan Fokus", "color": "not_priority", "resource": "Rendah", "icon": "minus-circle"},
}

ACTION_TYPES = {
    "digital": "Digital / Socmed",
    "lapangan": "Lapangan",
    "komunikasi": "Komunikasi / Mesej",
    "intel": "Intel / Crawl",
}


def _find_master() -> Optional[Path]:
    candidates = sorted(
        MASTER_DIR.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _swing_target(majority: int) -> int:
    return max(200, int(majority // 2) + 200)


def _priority_for(seat: dict) -> str:
    kp = seat.get("kategoriPas", "not_priority")
    if kp in ("defend", "winnable"):
        return "P1"
    if kp == "tough":
        return "P2"
    return "P3"


def _templates_for_category(kp: str, seat: dict) -> Dict[str, List[str]]:
    name = seat.get("name", "")
    code = seat.get("code", "")
    isu1 = seat.get("isuUtama1", "kos sara hidup")
    isu2 = seat.get("isuUtama2", "infrastruktur")
    cluster = seat.get("clusterKawasan", "")
    swing = _swing_target(int(seat.get("majority") or 0))
    fb = seat.get("facebookUrl") or "halaman calon/ADUN"
    tt = seat.get("tiktokHandle") or "@calon"

    if kp == "defend":
        return {
            "digital": [
                f"Post FB/TikTok harian dari {fb} — highlight projek selesai & kehadiran ADUN.",
                f"3 video TikTok/minggu isu tempatan: {isu1}.",
                "Balas komen negatif ≤4 jam; escalate ke war room jika viral >5k views.",
            ],
            "lapangan": [
                "House-to-house zon pengundi setia (FELDA/LBN) — 2 kali/minggu.",
                "Majlis pengundi setia + transport undi keluar (OKU/warga emas).",
                "Pastikan jentera polling agent confirmed — senarai 100% sebelum penamaan.",
            ],
            "komunikasi": [
                f"Mesej utama: kestabilan + penghargaan + {isu1} ditangani.",
                "Counter-narrative split PAS-Bersatu — tekankan kestabilan negeri.",
            ],
            "intel": [
                f"Crawl keyword: {seat.get('keywordPrimary', code)} — 2×/hari semasa kempen.",
                "Alert bila sentiment negatif >20% atau lawan mula ceramah <5km.",
            ],
        }
    if kp == "winnable":
        return {
            "digital": [
                f"Micro-content isu {isu1} & {isu2} — 4 post/minggu FB + TikTok {tt}.",
                "Testimoni pengundi swing (video 60s) — 2/minggu.",
                "Boost post kawasan majoriti ≤999 undi — budget terhad.",
            ],
            "lapangan": [
                f"Ceramah 2–3×/minggu — fokus swing voter (target +{swing} undi).",
                "Door-to-door 500 rumah/minggu di zon marginal.",
                "Booth pasar malam / pasar pagi — Sabtu & Ahad.",
            ],
            "komunikasi": [
                f"Frame: perubahan mampu milik — {isu1} vs status quo.",
                "Highlight majoriti {seat.get('majority', 0):,} — setiap undi kritikal.",
            ],
            "intel": [
                f"Pantau calon lawan ({seat.get('challenger', '—')}) — socmed & ceramah.",
                "Track risiko 3 penjuru — alert jika PN clash atau PH-BN straight fight.",
            ],
        }
    if kp == "tough":
        return {
            "digital": [
                "Minimum 1 post/minggu — jangan habiskan budget iklan.",
                f"Rebut isu {isu1} hanya bila lawan attack.",
            ],
            "lapangan": [
                "Ceramah selective — hanya jika isyarat positif (crowd >200).",
                f"Sentuhan akar umbi {cluster} — 1 program/2 minggu.",
            ],
            "komunikasi": [
                "Mesej defensif: perpaduan + elak provokasi.",
            ],
            "intel": [
                f"Monitor passive — crawl 1×/minggu {code} {name}.",
                "Naikkan ke Boleh Menang jika lawan lemah (clash PN / sentiment drop).",
            ],
        }
    return {
        "digital": ["Tiada kempen aktif — maintain presence minimum."],
        "lapangan": ["Tiada operasi lapangan kecuali permintaan calon tempatan."],
        "komunikasi": ["—"],
        "intel": [
            f"Crawl passive 1×/minggu — {code} {name}.",
            "Reclassify jika majoriti lawan drop atau isu tempatan panas.",
        ],
    }


def build_actions_for_seat(seat: dict) -> List[dict]:
    kp = seat.get("kategoriPas", "not_priority")
    code = seat["code"]
    prio = _priority_for(seat)
    owner = f"Jentera {code}"
    templates = _templates_for_category(kp, seat)
    actions: List[dict] = []
    idx = 0
    for atype, texts in templates.items():
        for text in texts:
            if text.strip() in ("—", "-", ""):
                continue
            idx += 1
            trigger = "manual"
            if atype == "intel" and "Alert" in text:
                trigger = "sentiment_neg_pct > 20"
            elif atype == "intel" and "Naikkan" in text:
                trigger = "opponent_weak_signal"
            elif kp in ("defend", "winnable") and atype == "digital":
                trigger = "weekly_schedule"
            actions.append({
                "id": f"{code}_{atype}_{idx}",
                "kod_dun": code,
                "kawasan": seat.get("name", ""),
                "kategori_pas": kp,
                "kategori_label": seat.get("kategoriPasLabel", CATEGORY_META.get(kp, {}).get("label", kp)),
                "action_type": atype,
                "action_type_label": ACTION_TYPES[atype],
                "priority": prio,
                "action_text": text,
                "owner": owner,
                "frequency": {
                    "digital": "3–7×/minggu" if kp in ("defend", "winnable") else "1×/minggu",
                    "lapangan": "2–3×/minggu" if kp in ("defend", "winnable") else "selective",
                    "komunikasi": "mingguan",
                    "intel": "2×/hari" if kp == "defend" else "1×/minggu",
                }.get(atype, "ad hoc"),
                "trigger_signal": trigger,
                "status": "pending",
                "due_date": None,
                "pas_win_prob": seat.get("pasWinProb"),
                "swing_target_undi": _swing_target(int(seat.get("majority") or 0)) if kp == "winnable" else None,
            })
    return actions


def _seat_mention_stats(seats: List[dict], df: Optional[pd.DataFrame]) -> Dict[str, dict]:
    stats: Dict[str, dict] = {s["code"]: {
        "mentions": 0, "negative": 0, "neutral": 0, "positive": 0,
        "neg_pct": 0.0, "alert_level": "ok", "top_snippet": "",
    } for s in seats}

    if df is None or df.empty or "Text" not in df.columns:
        return stats

    sent_col = "sentiment_label" if "sentiment_label" in df.columns else "Sentiment"
    for seat in seats:
        code = seat["code"]
        name = seat.get("name", "")
        kw = re.compile(
            rf"\b{re.escape(code)}\b|{re.escape(name)}|{re.escape(seat.get('keywordPrimary', ''))}",
            re.I,
        )
        sub = df[df["Text"].fillna("").astype(str).str.contains(kw, na=False)]
        if sub.empty:
            continue
        n = len(sub)
        neg = neu = pos = 0
        if sent_col in sub.columns:
            vc = sub[sent_col].fillna("").astype(str).str.lower()
            neg = int(vc.str.contains("neg").sum())
            neu = int(vc.str.contains("neut").sum())
            pos = int(vc.str.contains("pos").sum())
        neg_pct = round(neg / n * 100, 1) if n else 0.0
        alert = "ok"
        if neg_pct >= 25:
            alert = "critical"
        elif neg_pct >= 15:
            alert = "warning"
        elif n >= 10 and neg_pct >= 10:
            alert = "watch"
        snippet = ""
        if not sub.empty:
            snippet = re.sub(r"\s+", " ", str(sub.iloc[0]["Text"]))[:120]
        stats[code] = {
            "mentions": n,
            "negative": neg,
            "neutral": neu,
            "positive": pos,
            "neg_pct": neg_pct,
            "alert_level": alert,
            "top_snippet": snippet,
        }
    return stats


def _load_news_analyzed() -> dict:
    if not NEWS_ANALYZED_JSON.exists():
        return {}
    try:
        return json.loads(NEWS_ANALYZED_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_media_triggers(news: dict) -> List[dict]:
    """Triggers from Tier A media/komen — berasingan dari socmed master."""
    if not news:
        return []
    triggers: List[dict] = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    for alert in news.get("narrative_alerts") or []:
        if alert.get("count", 0) < 2:
            continue
        triggers.append({
            "id": f"trg_media_{alert.get('type', 'narrative')}",
            "kod_dun": None,
            "kawasan": "Media / N9",
            "kategori_pas": "intel",
            "type": f"media_{alert.get('type', 'narrative')}",
            "severity": alert.get("severity", "watch"),
            "message": alert.get("message", ""),
            "recommended_action": "Semak panel Media Tone dashboard; sediakan counter-narrative jika perlu.",
            "detected_at": ts,
            "auto_fired": True,
            "source_layer": "media_and_comments",
        })

    pv = news.get("public_voice") or {}
    if pv.get("total", 0) >= 3 and pv.get("neg_pct", 0) >= 40:
        triggers.append({
            "id": "trg_media_comments_neg",
            "kod_dun": None,
            "kawasan": "Komen pembaca",
            "kategori_pas": "intel",
            "type": "public_voice_negative",
            "severity": "warning",
            "message": f"Suara awam (komen) {pv['neg_pct']}% negatif ({pv['total']} komen Tier A)",
            "recommended_action": "Balas/pantau komen di China Press / FMT; escalate jika viral.",
            "detected_at": ts,
            "auto_fired": True,
            "source_layer": "media_and_comments",
        })

    mt = news.get("media_tone") or {}
    if mt.get("neg_pct", 0) >= 35 and mt.get("total", 0) >= 5:
        triggers.append({
            "id": "trg_media_tone_neg",
            "kod_dun": None,
            "kawasan": "Media NS",
            "kategori_pas": "intel",
            "type": "media_tone_negative",
            "severity": "watch",
            "message": f"Media tone {mt['neg_pct']}% negatif ({mt['total']} artikel direct Tier A)",
            "recommended_action": "Review headline negatif; koordinasi mesej komunikasi.",
            "detected_at": ts,
            "auto_fired": True,
            "source_layer": "media_and_comments",
        })

    return triggers[:6]


def build_triggers(seats: List[dict], signals: Dict[str, dict], news_analyzed: Optional[dict] = None) -> List[dict]:
    triggers: List[dict] = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    for seat in seats:
        code = seat["code"]
        sig = signals.get(code, {})
        kp = seat.get("kategoriPas", "not_priority")
        if kp not in ("defend", "winnable", "tough") and sig.get("alert_level") == "ok":
            continue

        if sig.get("alert_level") in ("critical", "warning"):
            triggers.append({
                "id": f"trg_{code}_sentiment",
                "kod_dun": code,
                "kawasan": seat.get("name", ""),
                "kategori_pas": kp,
                "type": "sentiment_drop",
                "severity": sig["alert_level"],
                "message": f"Sentimen negatif {sig['neg_pct']}% ({sig['mentions']} mention) — {code} {seat.get('name', '')}",
                "recommended_action": "Lancar counter-narrative digital + pantau komen 4 jam; escalate ke war room.",
                "detected_at": ts,
                "auto_fired": True,
            })

        if kp == "winnable" and int(seat.get("majority") or 0) <= 500:
            triggers.append({
                "id": f"trg_{code}_marginal",
                "kod_dun": code,
                "kawasan": seat.get("name", ""),
                "kategori_pas": kp,
                "type": "ultra_marginal",
                "severity": "watch",
                "message": f"Kerusi ultra-marginal — majoriti {seat.get('majority', 0):,}. Target swing +{_swing_target(int(seat.get('majority') or 0))} undi.",
                "recommended_action": "Intensifkan door-to-door + 2 ceramah/minggu.",
                "detected_at": ts,
                "auto_fired": True,
            })

        if seat.get("threeCornerRisk") == "Tinggi" and kp in ("defend", "winnable"):
            triggers.append({
                "id": f"trg_{code}_3corner",
                "kod_dun": code,
                "kawasan": seat.get("name", ""),
                "kategori_pas": kp,
                "type": "three_corner_risk",
                "severity": "warning",
                "message": f"Risiko 3 penjuru tinggi — {code}. Pantau overlap calon PAS/PN/BN.",
                "recommended_action": "Koordinasi war room — elak pecah undi; intel calon lawan.",
                "detected_at": ts,
                "auto_fired": True,
            })

    media_triggers = build_media_triggers(news_analyzed or {})
    triggers.extend(media_triggers)
    return triggers[:24]


def _rule_based_briefing(seats: List[dict], triggers: List[dict], signals: Dict[str, dict]) -> dict:
    kp_count = {}
    for s in seats:
        kp_count[s.get("kategoriPas", "not_priority")] = kp_count.get(s.get("kategoriPas", "not_priority"), 0) + 1

    critical = [t for t in triggers if t.get("severity") == "critical"]
    defend = [s for s in seats if s.get("kategoriPas") == "defend"]
    winnable = [s for s in seats if s.get("kategoriPas") == "winnable"]

    exec_summary = (
        f"War Room N9 — {len(defend)} kerusi Pertahan, {len(winnable)} Boleh Menang, "
        f"{len(triggers)} isyarat aktif. "
        f"{'⚠️ ' + str(len(critical)) + ' alert kritikal sentiment.' if critical else 'Tiada alert kritikal sentiment.'} "
        "Model ramalan = rule-based, bukan polling."
    )

    priorities = []
    for code in [s["code"] for s in defend + winnable]:
        s = next(x for x in seats if x["code"] == code)
        sig = signals.get(code, {})
        priorities.append(
            f"{code} {s['name']} ({s.get('kategoriPasLabel', '')}): "
            f"PAS {s.get('pasWinProb')}% · mention {sig.get('mentions', 0)} · "
            f"isu: {s.get('isuUtama1', '—')}"
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "rule_based",
        "model": "template",
        "executive_summary": exec_summary,
        "week_priorities": priorities[:8],
        "digital_actions": [
            "Post harian kerusi Pertahan (N05, N25, N31) — projek + kehadiran ADUN.",
            "Video TikTok isu kos hidup — target Boleh Menang (N03, N09, N18).",
            "Counter-narrative split PAS-Bersatu jika sentiment negatif >15%.",
        ],
        "lapangan_actions": [
            "Ceramah FELDA/LBN — N05, N03 minggu ini.",
            "Door-to-door 500 rumah — kerusi marginal N09/N18.",
            "Confirm polling agent — semua kerusi Pertahan.",
        ],
        "intel_actions": [
            "Refresh crawl master — filter keyword NS + kod DUN kritikal.",
            "Pantau calon lawan post-penamaan SPR.",
            "Track scenario S1 vs S4 (PAS-PN clash).",
        ],
        "risks": [t["message"] for t in triggers if t.get("severity") in ("critical", "warning")][:6],
        "disclaimer": "Bukan polling. Human-in-the-loop — semak sebelum terbit/post.",
    }


def generate_llm_briefing(seats: List[dict], triggers: List[dict], signals: Dict[str, dict]) -> dict:
    """Fasa D — RAG-style context + LLM draft (fallback rule-based)."""
    base = _rule_based_briefing(seats, triggers, signals)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return base

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = {
            "defend": [f"{s['code']} {s['name']}" for s in seats if s.get("kategoriPas") == "defend"],
            "winnable": [f"{s['code']} {s['name']}" for s in seats if s.get("kategoriPas") == "winnable"],
            "triggers": triggers[:10],
            "signals_top": {k: v for k, v in list(signals.items())[:12] if v.get("mentions", 0) > 0},
        }
        prompt = f"""Anda analis war room PRN Negeri Sembilan 2026 (PAS/PN lens).
Context JSON:
{json.dumps(context, ensure_ascii=False)[:6000]}

Hasilkan JSON sahaja dengan keys:
executive_summary (2 ayat BM),
week_priorities (array 5 bullet),
digital_actions (array 3),
lapangan_actions (array 3),
intel_actions (array 3),
risks (array 3).
Bukan polling. Cadangan operasi sahaja. BM formal."""

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1200,
        )
        text = resp.choices[0].message.content or ""
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            parsed = json.loads(m.group())
            base.update(parsed)
            base["source"] = "llm_rag"
            base["model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    except Exception as exc:
        base["llm_error"] = str(exc)[:200]

    return base


def build_agent_queue(
    actions: List[dict], triggers: List[dict], briefing: dict
) -> List[dict]:
    """Fasa E — cadangan agent menunggu kelulusan manusia."""
    queue: List[dict] = []
    ts = datetime.now().isoformat(timespec="seconds")

    for trg in triggers:
        if trg.get("severity") not in ("critical", "warning", "watch"):
            continue
        queue.append({
            "id": f"agent_{trg['id']}",
            "type": "trigger_response",
            "kod_dun": trg["kod_dun"],
            "title": f"[{trg['severity'].upper()}] {trg['kawasan']}",
            "proposal": trg.get("recommended_action", ""),
            "context": trg.get("message", ""),
            "status": "pending_approval",
            "created_at": ts,
            "source": "crawl_trigger",
        })

    for act in actions:
        if act.get("priority") != "P1" or act.get("action_type") != "digital":
            continue
        if act.get("kategori_pas") not in ("defend", "winnable"):
            continue
        queue.append({
            "id": f"agent_{act['id']}",
            "type": "scheduled_post",
            "kod_dun": act["kod_dun"],
            "title": f"Draf socmed — {act['kod_dun']} ({act['action_type_label']})",
            "proposal": act["action_text"],
            "context": f"Priority {act['priority']} · {act.get('frequency', '')}",
            "status": "pending_approval",
            "created_at": ts,
            "source": "playbook",
        })

    if briefing.get("digital_actions"):
        queue.append({
            "id": "agent_briefing_digital",
            "type": "weekly_brief",
            "kod_dun": "ALL",
            "title": "Briefing mingguan — Digital",
            "proposal": "; ".join(briefing["digital_actions"][:3]),
            "context": briefing.get("executive_summary", "")[:300],
            "status": "pending_approval",
            "created_at": ts,
            "source": "llm_briefing" if briefing.get("source") == "llm_rag" else "rule_briefing",
        })

    seen = set()
    deduped = []
    for item in queue:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        deduped.append(item)
    return deduped[:20]


# ── War Room Lite: 6 kerusi + checklist 10 modul ──

CRITICAL_SEATS = ["N05", "N25", "N31", "N03", "N09", "N18"]

MODULE_CHECKLIST = [
    {"id": "M1", "label": "Data pengundi & isu tempatan", "icon": "database"},
    {"id": "M2", "label": "Sentimen socmed (AI)", "icon": "message-square"},
    {"id": "M3", "label": "Segmentasi kerusi", "icon": "users"},
    {"id": "M4", "label": "Draf kandungan kempen", "icon": "file-text"},
    {"id": "M5", "label": "Jadual post (semi-auto)", "icon": "calendar"},
    {"id": "M6", "label": "Pantau isu & counter-narrative", "icon": "radar"},
    {"id": "M7", "label": "Tugasan jentera / sukarelawan", "icon": "user-check"},
    {"id": "M8", "label": "Integrasi data (CSV/Sheet)", "icon": "link"},
    {"id": "M9", "label": "Laporan prestasi mingguan", "icon": "bar-chart"},
    {"id": "M10", "label": "Ramalan kerusi (rule-based)", "icon": "trending-up"},
]


def _jentera_daily_hint(seat: dict) -> Optional[str]:
    """Tindakan lapangan dari data DPI/cula/SKT (Jun 2026)."""
    bkc = seat.get("bkcCula")
    cula = seat.get("culaPct")
    skt = seat.get("skt51")
    total = seat.get("culaPasTotal")
    if bkc is not None and bkc < -1500:
        return (
            f"JENTERA: sahkan cula & daftar undi — BKC {bkc:,} (SKT {skt:,}). "
            f"Fokus Bulan/Condong Bulan hari ini."
        )
    if bkc is not None and bkc < -500:
        return f"JENTERA: kejar {abs(bkc):,} undi lagi ke SKT 51% — cula {total or '—'} pengundi ({cula or '—'}%)."
    if cula and cula >= 18 and seat.get("kategoriPas") == "winnable":
        return f"Cula {cula}% kuat — convert ke turnout: 100 rumah + senarai transport undi."
    return None


def _pick_daily_action(seat: dict, actions: List[dict], signals: dict) -> Optional[dict]:
    if not actions:
        return None
    code = seat["code"]
    sig = signals.get(code, {})
    kp = seat.get("kategoriPas", "not_priority")

    if sig.get("alert_level") in ("critical", "warning"):
        for a in actions:
            if "counter" in a["action_text"].lower() or a["action_type"] == "komunikasi":
                return a

    rotate = {
        "defend": ["digital", "lapangan", "digital", "lapangan", "komunikasi", "intel", "digital"],
        "winnable": ["lapangan", "digital", "lapangan", "digital", "lapangan", "intel", "komunikasi"],
    }
    pick_type = rotate.get(kp, ["intel"])[datetime.now().weekday()]
    for a in actions:
        if a["action_type"] == pick_type:
            chosen = dict(a)
            jentera = _jentera_daily_hint(seat)
            if jentera and datetime.now().weekday() in (0, 2, 4):
                chosen["action_text"] = jentera
                chosen["action_type"] = "lapangan"
                chosen["source"] = "dpi_jentera"
            return chosen
    chosen = dict(actions[0])
    jentera = _jentera_daily_hint(seat)
    if jentera:
        chosen["action_text"] = jentera
        chosen["source"] = "dpi_jentera"
    return chosen


def build_hari_ini(seats: List[dict], by_seat: Dict[str, List[dict]], signals: dict, triggers: List[dict]) -> dict:
    seat_map = {s["code"]: s for s in seats}
    items = []
    for code in CRITICAL_SEATS:
        seat = seat_map.get(code)
        if not seat:
            continue
        acts = by_seat.get(code, [])
        daily = _pick_daily_action(seat, acts, signals)
        if not daily:
            continue
        sig = signals.get(code, {})
        jentera_hint = _jentera_daily_hint(seat)
        items.append({
            "id": f"today_{code}",
            "kod_dun": code,
            "kawasan": seat.get("name", ""),
            "kategori_pas": seat.get("kategoriPas", ""),
            "kategori_label": seat.get("kategoriPasLabel", ""),
            "action_text": daily["action_text"],
            "action_type": daily["action_type"],
            "action_source": daily.get("source", "playbook"),
            "pas_win_prob": seat.get("pasWinProb"),
            "mentions": sig.get("mentions", 0),
            "neg_pct": sig.get("neg_pct", 0),
            "alert_level": sig.get("alert_level", "ok"),
            "registered_voters_dpi": seat.get("registeredVotersDpi"),
            "pct_melayu": seat.get("pctMelayu"),
            "cula_pct": seat.get("culaPct"),
            "cula_pas_total": seat.get("culaPasTotal"),
            "skt51": seat.get("skt51"),
            "bkc_cula": seat.get("bkcCula"),
            "jentera_status": seat.get("jenteraStatus"),
            "jentera_hint": jentera_hint,
            "mn_calon": seat.get("mnCalon"),
        })

    # Jentera alerts — kerusi kritikal dengan BKC terburuk
    jentera_alerts = []
    for code in CRITICAL_SEATS:
        seat = seat_map.get(code, {})
        bkc = seat.get("bkcCula")
        if bkc is not None and bkc < -800:
            jentera_alerts.append({
                "kod_dun": code,
                "message": (
                    f"BKC cula {bkc:,} · cula {seat.get('culaPct', '—')}% · "
                    f"{seat.get('jenteraStatus', 'perlu tindakan')}"
                ),
                "severity": "warning" if bkc > -2000 else "critical",
            })
    jentera_alerts.sort(key=lambda x: seat_map.get(x["kod_dun"], {}).get("bkcCula", 0))

    alerts = []
    for t in triggers:
        if t.get("kod_dun") in CRITICAL_SEATS or t.get("severity") in ("critical", "warning"):
            alerts.append({
                "kod_dun": t.get("kod_dun"),
                "message": t.get("message", ""),
                "severity": t.get("severity", "watch"),
            })
    alerts = alerts[:3]
    if jentera_alerts and len(alerts) < 3:
        for ja in jentera_alerts:
            if len(alerts) >= 3:
                break
            if not any(a.get("kod_dun") == ja["kod_dun"] for a in alerts):
                alerts.append(ja)

    media_alerts = []
    news = _load_news_analyzed()
    for na in (news.get("narrative_alerts") or [])[:2]:
        media_alerts.append({
            "kod_dun": None,
            "message": na.get("message", "")[:100],
            "severity": na.get("severity", "watch"),
            "source": "media_tier_a",
        })
    pv = news.get("public_voice") or {}
    if pv.get("neg_pct", 0) >= 40 and pv.get("total", 0) >= 2:
        media_alerts.append({
            "kod_dun": None,
            "message": f"Komen pembaca {pv['neg_pct']}% negatif ({pv['total']} komen)",
            "severity": "warning",
            "source": "public_voice",
        })

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "items": items,
        "alerts": alerts,
        "media_alerts": media_alerts,
        "jentera_alerts": jentera_alerts[:6],
        "dpi_as_of": "Disember 2025 (SPR DPI)",
        "done_count_hint": 0,
    }


def build_module_status(summary: dict, master_path: Optional[Path], triggers: List[dict]) -> List[dict]:
    has_master = bool(master_path and master_path.exists())
    has_news = NEWS_ANALYZED_JSON.exists()
    dpi_json = resolve_existing(
        reference("N9") / "n9_dpi_updates.json",
        ROOT / "data/projects/political/pas_break_2026/reference/n9_dpi_updates.json",
    )
    has_dpi = dpi_json.exists()
    out = []
    statuses = {
        "M1": ("ready" if has_dpi else "partial", "DPI Dec 2025 + demografi 36 DUN · SPR"),
        "M2": ("ready" if (has_master or has_news) else "partial", "Socmed master + Media Tier A berita"),
        "M3": ("ready", "Pertahan / Menang / Sukar + cula/SKT/BKC"),
        "M4": ("partial", "Draf teks — War Room / LLM optional"),
        "M5": ("partial", "Semi-auto — draf + reminder (bukan post auto)"),
        "M6": ("ready" if triggers else "partial", f"{len(triggers)} isyarat (socmed + media Tier A)"),
        "M7": ("ready", "6 tindakan Hari Ini + WhatsApp + jentera DPI"),
        "M8": ("ready" if has_dpi else "partial", "Excel N9/Updates_* → n9_dpi_updates.json"),
        "M9": ("planned", "Laporan mingguan — fasa seterusnya"),
        "M10": ("partial", "pasWinProb + BKC cula — bukan polling"),
    }
    for mod in MODULE_CHECKLIST:
        st, note = statuses.get(mod["id"], ("planned", ""))
        out.append({**mod, "status": st, "note": note})
    return out


def build_whatsapp_digest(hari_ini: dict) -> str:
    header = f"PRN N9 — Tindakan {hari_ini.get('date', '')}"
    dates_path = resolve_existing(
        SHARED / "spr/spr_prn_dates_2026.json",
        ROOT / "data/projects/political/pas_break_2026/reference/spr_prn_dates_2026.json",
    )
    if dates_path.exists():
        try:
            d = json.loads(dates_path.read_text(encoding="utf-8"))
            ns = d.get("negeri_sembilan", {})
            header += f"\n📅 SPR: penamaan {ns.get('penamaan_display', '—')} · mengundi {ns.get('mengundi_display', '—')}"
        except json.JSONDecodeError:
            pass
    lines = [header, ""]
    defend = [i for i in hari_ini.get("items", []) if i.get("kategori_pas") == "defend"]
    win = [i for i in hari_ini.get("items", []) if i.get("kategori_pas") == "winnable"]
    if defend:
        lines.append("PERTAHAN")
        for i in defend:
            dpi = ""
            if i.get("bkc_cula") is not None:
                dpi = f" [BKC {i['bkc_cula']:,}]"
            lines.append(f"• {i['kod_dun']}: {i['action_text'][:85]}{dpi}")
        lines.append("")
    if win:
        lines.append("BOLEH MENANG")
        for i in win:
            dpi = ""
            if i.get("cula_pct") is not None:
                dpi = f" [cula {i['cula_pct']}%"
                if i.get("bkc_cula") is not None:
                    dpi += f" BKC {i['bkc_cula']:,}"
                dpi += "]"
            lines.append(f"• {i['kod_dun']}: {i['action_text'][:85]}{dpi}")
        lines.append("")
    for a in hari_ini.get("alerts", []):
        lines.append(f"⚠️ {a.get('kod_dun', '')}: {a.get('message', '')[:80]}")
    for ma in hari_ini.get("media_alerts", []):
        lines.append(f"📰 Media: {ma.get('message', '')[:80]}")
    lines.append("")
    lines.append("Reply DONE bila siap.")
    return "\n".join(lines)


def build_war_room_payload(seats: List[dict], master_path: Optional[Path] = None) -> dict:
    master_path = master_path or _find_master()
    df = None
    if master_path and master_path.exists():
        try:
            df = pd.read_csv(master_path, low_memory=False)
            text = df["Text"].fillna("").astype(str)
            df = df[text.str.contains(NS_PATTERN, case=False, na=False)].copy()
        except Exception:
            df = None

    signals = _seat_mention_stats(seats, df)
    news_analyzed = _load_news_analyzed()
    all_actions: List[dict] = []
    by_seat: Dict[str, List[dict]] = {}
    for seat in seats:
        acts = build_actions_for_seat(seat)
        by_seat[seat["code"]] = acts
        all_actions.extend(acts)

    triggers = build_triggers(seats, signals, news_analyzed)
    briefing = generate_llm_briefing(seats, triggers, signals)
    agent_queue = build_agent_queue(all_actions, triggers, briefing)
    hari_ini = build_hari_ini(seats, by_seat, signals, triggers)
    whatsapp = build_whatsapp_digest(hari_ini)

    summary = {
        "total_actions": len(all_actions),
        "by_category": {},
        "by_type": {},
        "triggers_active": len(triggers),
        "agent_pending": len([a for a in agent_queue if a["status"] == "pending_approval"]),
        "critical_alerts": len([t for t in triggers if t.get("severity") == "critical"]),
        "hari_ini_count": len(hari_ini.get("items", [])),
    }
    for seat in seats:
        kp = seat.get("kategoriPas", "not_priority")
        summary["by_category"][kp] = summary["by_category"].get(kp, 0) + 1
    for act in all_actions:
        summary["by_type"][act["action_type"]] = summary["by_type"].get(act["action_type"], 0) + 1

    module_checklist = build_module_status(summary, master_path, triggers)

    payload = {
        "meta": {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "master_source": str(master_path.relative_to(ROOT)) if master_path else None,
            "mode": "lite",
            "phases": ["hari_ini", "module_checklist", "whatsapp"],
        },
        "hari_ini": hari_ini,
        "module_checklist": module_checklist,
        "whatsapp_digest": whatsapp,
        "category_meta": CATEGORY_META,
        "action_types": ACTION_TYPES,
        "summary": summary,
        "signals": signals,
        "media_analyzed": news_analyzed,
        "triggers": triggers,
        "actions": all_actions,
        "actions_by_seat": by_seat,
        "briefing": briefing,
        "agent_queue": agent_queue,
    }
    return payload


def save_war_room(payload: dict) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_BRIEFING.write_text(json.dumps(payload["briefing"], ensure_ascii=False, indent=2), encoding="utf-8")

    rows = []
    for act in payload["actions"]:
        rows.append({
            "id": act["id"],
            "kod_dun": act["kod_dun"],
            "kawasan": act["kawasan"],
            "kategori_pas": act["kategori_pas"],
            "action_type": act["action_type"],
            "priority": act["priority"],
            "action_text": act["action_text"],
            "owner": act["owner"],
            "frequency": act["frequency"],
            "trigger_signal": act["trigger_signal"],
            "status": act["status"],
        })
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8")

    wa_path = OUT_WHATSAPP
    wa_path.write_text(payload.get("whatsapp_digest", ""), encoding="utf-8")


def main() -> None:
    from n9_seat_analytics import load_enriched_seats

    seats = load_enriched_seats()
    payload = build_war_room_payload(seats)
    save_war_room(payload)
    print(f"✅ War Room JSON: {OUT_JSON}")
    print(f"✅ Actions CSV:   {OUT_CSV}")
    print(f"✅ Briefing:      {OUT_BRIEFING}")
    print(
        f"   Actions: {payload['summary']['total_actions']} · "
        f"Triggers: {payload['summary']['triggers_active']} · "
        f"Agent queue: {payload['summary']['agent_pending']}"
    )


if __name__ == "__main__":
    main()
