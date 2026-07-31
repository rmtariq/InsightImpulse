#!/usr/bin/env python3
"""Shared per-DUN socmed + headline snippet builders for War Room states."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dun_headline_quality import score_headline
from dun_seat_keywords import (
    JOHOR_SEAT_KEYWORDS,
    N9_SEAT_KEYWORDS,
    keywords_for_state,
    norm_code,
    row_matches_seat,
)

__all__ = [
    "JOHOR_PATTERN",
    "JOHOR_SEAT_KEYWORDS",
    "N9_SEAT_KEYWORDS",
    "NS_PATTERN",
    "build_socmed_for_state",
    "find_johor_master",
    "find_pas_break_master",
    "keywords_for_state",
    "load_geo_seats",
    "load_state_rows",
    "norm_code",
    "row_matches_seat",
]

ROOT = Path(__file__).resolve().parents[1]
MYT = timezone(timedelta(hours=8))
HEADLINE_MAX_AGE_DAYS = 90

NS_PATTERN = re.compile(
    r"negeri\s*sembilan|n\.?\s*sembilan|prn.*sembilan|sembilan.*prn|dun\s*sembilan|prn\s*n9|\bn9\b",
    re.I,
)
JOHOR_PATTERN = re.compile(
    r"\bjohor\b|prn\s*johor|dun\s*johor|johor\s*darul|jdt\b|johor\s*bahru|"
    r"segamat|muar|batu\s*pahat|kluang|kota\s*tinggi|kulai|pontian|mersing|tangkak|"
    r"kempas|iskandar|pasir\s*gudang|senai|skudai|tampoi|permas|ulu\s*tiram|masai|"
    r"onen\s*hafiz|bangsa\s*johor|bn\s*johor|#bnjohor",
    re.I,
)


def parse_date(raw: str) -> Optional[datetime]:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    if s.isdigit():
        try:
            return datetime.fromtimestamp(int(s), tz=timezone.utc)
        except (ValueError, OSError):
            return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError:
        return None


def count_dun_codes(text: str) -> int:
    pat = re.compile(r"\bN\.?\s*0?[1-9][0-9]?\b", re.I)
    return len(set(m.group(0).upper().replace(".", "").replace(" ", "") for m in pat.finditer(text)))


def is_state_rollup(text: str, threshold: int = 4) -> bool:
    return count_dun_codes(text) >= threshold


def excerpt_around_seat(text: str, code: str, keywords: List[str], max_len: int = 160) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    t_lower = text.lower()
    pos = -1
    seat_name = next((kw for kw in keywords if len(kw) > 3), "")
    if seat_name:
        m = re.search(rf"\b{re.escape(seat_name)}\b", t_lower)
        if m:
            pos = m.start()
    if pos < 0:
        dotted = f"n.{code[1:].lower()}" if code.lower().startswith("n") else code.lower()
        for pat in (code.lower(), dotted):
            m = re.search(rf"\b{re.escape(pat)}\b", t_lower)
            if m:
                pos = m.start()
                break
    if pos >= 0:
        start = max(0, pos - 50)
        chunk = text[start : start + max_len].strip()
        if start > 0:
            chunk = "…" + chunk
        if start + max_len < len(text):
            chunk = chunk.rstrip() + "…"
        return chunk
    return text[:max_len]


def is_recent_row(row: dict, window_end: datetime, max_age_days: int = HEADLINE_MAX_AGE_DAYS) -> bool:
    dt = row.get("date")
    if not dt or not window_end:
        return False
    return (window_end - dt).days <= max_age_days


def pick_top_snippet(
    matched: List[dict],
    code: str,
    keywords: List[str],
    window_end: datetime,
    seat_meta: dict | None = None,
    state_key: str = "N9",
    max_age_days: int = HEADLINE_MAX_AGE_DAYS,
) -> tuple[str, str | None]:
    seat = {
        "code": code,
        "name": (seat_meta or {}).get("name"),
        "incumbent": (seat_meta or {}).get("incumbent"),
        "stateKey": state_key,
    }
    best_score = -1
    best_text = ""
    best_date: datetime | None = None

    for row in matched:
        if not is_recent_row(row, window_end, max_age_days):
            continue
        text = re.sub(r"\s+", " ", row["text"]).strip()
        if not text or is_state_rollup(text):
            continue
        if re.search(r"#top10|berita popular", text, re.I):
            continue
        verdict, _ = score_headline(text, seat)
        if verdict != "relevant":
            continue
        t = text.lower()
        score = 0
        for kw in keywords:
            if len(kw) > 3 and re.search(rf"\b{re.escape(kw)}\b", t):
                score += 6 + min(len(kw), 12)
        dotted = f"n.{code[1:].lower()}" if code.lower().startswith("n") else code.lower()
        if re.search(rf"\b{re.escape(code.lower())}\b", t) or re.search(rf"\b{re.escape(dotted)}\b", t):
            score += 10
        score += min(row.get("engagement", 0) // 1000, 5)
        if score > best_score:
            best_score = score
            best_text = text
            best_date = row.get("date")

    if best_text:
        iso = best_date.isoformat() if best_date else None
        return excerpt_around_seat(best_text, code, keywords), iso
    return "", None


def sentiment_bucket(label: str) -> str:
    s = (label or "").lower()
    if "neg" in s:
        return "negative"
    if "pos" in s:
        return "positive"
    return "neutral"


def emotion_bucket(label: str) -> str:
    """Normalize emotion_primary ke set ringkas untuk paparan."""
    e = (label or "").strip().lower()
    if e in ("anger", "marah"):
        return "anger"
    if e in ("fear", "takut"):
        return "fear"
    if e in ("sadness", "sad", "sedih"):
        return "sadness"
    if e in ("happy", "joy", "gembira"):
        return "happy"
    if e in ("love", "kasih"):
        return "love"
    if e in ("surprise", "terkejut"):
        return "surprise"
    return "neutral"


def demographic_bucket(label: str) -> str:
    """Normalize crawl demographic → 4 buckets for aggregation."""
    d = (label or "").strip().lower()
    if d in ("malay/bumiputera", "malay", "melayu"):
        return "malay"
    if d in ("chinese", "cina"):
        return "chinese"
    if d in ("indian", "tamil"):
        return "indian"
    if d in ("mixed/urban", "mixed", "urban", "english"):
        return "urban"
    return "unknown"


def compute_demo_insight(dpi_malay: float | None, soc_mix: dict, mentions: int) -> str | None:
    """Compare SPR DPI Malay % vs socmed language-proxy skew."""
    if not mentions or not soc_mix:
        return None
    soc_malay = soc_mix.get("malay", 0)
    if dpi_malay is None:
        if soc_malay >= 55:
            return "Naratif socmed condong Melayu — tiada DPI per-band for compare"
        if soc_mix.get("urban", 0) >= 40:
            return "Naratif socmed condong bandar/campuran"
        return None
    delta = soc_malay - dpi_malay
    if abs(delta) <= 8:
        return "Profil naratif socmed selari dengan demografi pengundi (DPI)"
    if delta > 8:
        return f"Naratif socmed lebih Melayu (+{delta:.0f}pp vs DPI) — suara rural/ground kuat"
    urban = soc_mix.get("urban", 0)
    if urban >= 30:
        return f"Naratif socmed lebih bandar (+{abs(delta):.0f}pp vs profil Melayu DPI) — digital/urban skew"
    return f"Naratif socmed kurang Melayu (−{abs(delta):.0f}pp vs DPI) — campuran/unknown dominan"


# Leksikon isu — diperkaya dari CSV keyword terperinci per-DUN (ekonomi, lokal/khidmat,
# institusi, serangan/tadbir urus, prestasi wakil). Tag isu panas per-DUN dari teks socmed.
ISSUE_LEXICON: Dict[str, List[str]] = {
    # — Ekonomi & kos hidup —
    "Kos sara hidup": ["kos hidup", "sara hidup", "harga barang", "barang naik", "barang mahal",
                        "harga naik", "mahal gila", "subsidi", "minyak naik", "harga minyak",
                        "diesel", "b40", "kemiskinan", "inflasi", "cukai", "gst", "sst"],
    "Sewa & rumah": ["sewa rumah", "sewa naik", "harga rumah", "rumah mampu milik", "sewa kedai",
                     "rumah mahal"],
    "Pekerjaan & ekonomi": ["peluang kerja", "kerja kilang", "gaji", "gaji rendah", "gaji tak naik",
                            "susah cari kerja", "pengangguran", "niaga susah", "kos niaga",
                            "pelaburan", "kilang", "industri", "ekonomi", "peniaga"],
    "Pertanian & Felda": ["harga sawit", "sawit turun", "subsidi felda", "peneroka", "pekebun kecil",
                          "getah", "ladang", "bantuan felda", "pengurusan felda"],
    # — Lokal / perkhidmatan —
    "Jalan & pengangkutan": ["jalan rosak", "lubang jalan", "jalan sesak", "kesesakan", "tol",
                             "parking", "parkir", "trafik", "jam", "jambatan", "pengangkutan awam"],
    "Banjir & air": ["banjir", "banjir kilat", "air paip", "bekalan air", "longkang", "pembetungan",
                     "tanah runtuh"],
    "Kebersihan & alam": ["sampah", "kebersihan", "pencemaran", "sampah pantai", "longkang tersumbat",
                          "bau busuk"],
    "Utiliti & internet": ["internet", "liputan internet", "internet lemah", "internet slow",
                           "elektrik", "lampu jalan", "jaringan"],
    # — Institusi & komuniti —
    "Pendidikan": ["sekolah", "sjkc", "sjkt", "sekolah cina", "sekolah tamil", "vernakular",
                   "universiti", "kolej", "pelajar", "yuran", "graduan", "pendidikan"],
    "Kesihatan": ["klinik", "hospital", "kesihatan", "ubat", "doktor", "klinik desa"],
    "Agama & institusi": ["masjid", "surau", "agama", "islam", "maruah", "kalimah", "halal",
                          "azan", "ulama", "syariah", "istana"],
    "Perpaduan kaum": ["perpaduan", "tamil", "tokong", "kuil", "gereja", "kaum", "dap", "mca", "mic"],
    "Pelancongan": ["pelancongan", "homestay", "resort", "hotel", "pantai", "pelancong"],
    # — Serangan / tadbir urus —
    "Rasuah & tadbir urus": ["rasuah", "sprm", "salah guna", "salah urus", "integriti", "skandal",
                             "pembaziran", "projek terbengkalai", "projek tertangguh", "projek lambat",
                             "pilih kasih", "kroni", "double standard", "lesen pilih kasih"],
    "Prestasi wakil": ["janji tinggal janji", "janji tak ditepati", "tak turun padang",
                       "tak turun kawasan", "perkhidmatan lambat", "pbt lemah", "pbt lambat",
                       "tak buat apa", "janji lupa"],
}
_ISSUE_PATTERNS = {
    label: re.compile("|".join(rf"\b{re.escape(k)}\b" for k in kws), re.I)
    for label, kws in ISSUE_LEXICON.items()
}


def detect_issues(text: str) -> List[str]:
    t = text or ""
    return [label for label, pat in _ISSUE_PATTERNS.items() if pat.search(t)]


def confidence_level(mentions: int) -> str:
    """Keyakinan socmed per-DUN ikut volum mention (elak over-claim kerusi tipis)."""
    if mentions >= 30:
        return "Tinggi"
    if mentions >= 8:
        return "Sederhana"
    if mentions >= 1:
        return "Rendah"
    return "Tiada"


def load_state_rows(master_paths: List[Path], state_pattern: re.Pattern) -> tuple[List[dict], List[str]]:
    rows: List[dict] = []
    sources: list[str] = []
    seen: set[str] = set()
    for master_path in master_paths:
        if not master_path.exists():
            continue
        sources.append(str(master_path.relative_to(ROOT)))
        with master_path.open(encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("Text") or ""
                url = row.get("URL") or ""
                if not state_pattern.search(f"{text} {url}"):
                    continue
                key = re.sub(r"\s+", " ", text.strip())[:240]
                if key in seen:
                    continue
                seen.add(key)
                sent_col = row.get("sentiment_label") or row.get("Sentiment") or ""
                try:
                    eng = int(float(row.get("total_engagement") or row.get("likes") or 0))
                except (TypeError, ValueError):
                    eng = 0
                rows.append({
                    "text": text,
                    "date": parse_date(row.get("Date") or ""),
                    "platform": (row.get("Platform") or "unknown").lower(),
                    "sentiment": sentiment_bucket(sent_col),
                    "sentiment_labeled": bool((sent_col or "").strip()),
                    "emotion": emotion_bucket(row.get("emotion_primary") or ""),
                    "demographic": demographic_bucket(row.get("demographic") or ""),
                    "narrative_split": bool(str(row.get("narrative_split", "")).lower() in ("true", "1", "yes")),
                    "engagement": eng,
                })
    return rows, sources


def build_socmed_for_state(
    state_key: str,
    seat_keywords: Dict[str, List[str]],
    state_rows: List[dict],
    master_sources: List[str],
    seat_meta: Dict[str, dict] | None = None,
) -> dict:
    st = state_key.upper()
    meta_by_code = seat_meta or {}
    max_dt: Optional[datetime] = None
    for row in state_rows:
        dt = row.get("date")
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt

    window_end = max_dt or datetime.now(timezone.utc)
    window_start_24h = window_end - timedelta(hours=24)
    window_start_7d = window_end - timedelta(days=7)

    by_dun: Dict[str, dict] = {}
    for code, keywords in seat_keywords.items():
        matched = [
            r for r in state_rows
            if row_matches_seat(r["text"], code, keywords, st)
        ]
        if not matched:
            by_dun[code] = {
                "mentions_total": 0,
                "mentions_24h": 0,
                "mentions_7d": 0,
                "neg_pct": 0.0,
                "pos_pct": 0.0,
                "neu_pct": 0.0,
                "lean": {"sokong": 0.0, "atas_pagar": 0.0, "menentang": 0.0},
                "lean_label": "Tiada data",
                "emotion": {},
                "emotion_top": None,
                "demo_mix": {},
                "demo_top": None,
                "demo_insight": None,
                "narrative_split_pct": 0.0,
                "top_issues": [],
                "confidence": "Tiada",
                "engagement_total": 0,
                "engagement_24h": 0,
                "platforms": {},
                "alert_level": "ok",
                "top_snippet": "",
                "top_snippet_date": None,
            }
            continue

        def in_window(r, start):
            return r["date"] is not None and start <= r["date"] <= window_end

        m24 = [r for r in matched if in_window(r, window_start_24h)]
        m7 = [r for r in matched if in_window(r, window_start_7d)]
        neg = sum(1 for r in matched if r["sentiment"] == "negative")
        pos = sum(1 for r in matched if r["sentiment"] == "positive")
        total = len(matched)
        neu = total - neg - pos
        neg_pct = round(neg / total * 100, 1) if total else 0.0
        pos_pct = round(pos / total * 100, 1) if total else 0.0
        neu_pct = round(neu / total * 100, 1) if total else 0.0
        plats = Counter(r["platform"] for r in matched)

        # Lean sokongan (sentiment-led): positif=sokong, negatif=menentang,
        # neutral/tak berlabel=atas pagar. (Master socmed tiada lajur stance.)
        lean = {"sokong": pos_pct, "atas_pagar": neu_pct, "menentang": neg_pct}
        lean_label = max(lean, key=lean.get)
        lean_label = {
            "sokong": "Cenderung Sokong", "atas_pagar": "Majoriti Atas Pagar",
            "menentang": "Cenderung Menentang",
        }[lean_label]

        # Agihan emosi (anger/fear/sadness/happy/love/surprise/neutral)
        emo_counter = Counter(r["emotion"] for r in matched)
        emo_mix = {
            k: round(v / total * 100, 1)
            for k, v in emo_counter.most_common()
            if k != "neutral"
        }
        emo_top = emo_counter.most_common(1)[0][0] if emo_counter else None
        if emo_top == "neutral":
            non_neu = [(k, v) for k, v in emo_counter.most_common() if k != "neutral"]
            emo_top = non_neu[0][0] if non_neu else "neutral"

        # Isu panas per-DUN dari teks
        issue_counter: Counter = Counter()
        for r in matched:
            for iss in detect_issues(r["text"]):
                issue_counter[iss] += 1
        top_issues = [
            {"issue": iss, "mentions": cnt} for iss, cnt in issue_counter.most_common(3)
        ]

        labeled = sum(1 for r in matched if r.get("sentiment_labeled"))

        # Demographic mix (language-proxy from crawl)
        demo_counter = Counter(r["demographic"] for r in matched if r.get("demographic"))
        demo_mix = {
            k: round(v / total * 100, 1)
            for k, v in demo_counter.items()
        }
        demo_top = demo_counter.most_common(1)[0][0] if demo_counter else None

        split_n = sum(1 for r in matched if r.get("narrative_split"))
        split_pct = round(split_n / total * 100, 1) if total else 0.0

        dpi_malay = (meta_by_code.get(code) or {}).get("pctMelayu")
        if dpi_malay in (None, ""):
            demo_obj = (meta_by_code.get(code) or {}).get("demo") or {}
            dpi_malay = demo_obj.get("malay")
        demo_insight = compute_demo_insight(
            float(dpi_malay) if dpi_malay not in (None, "") else None,
            demo_mix,
            total,
        )

        alert = "ok"
        ref = m24 if m24 else m7 if m7 else matched
        ref_neg = sum(1 for r in ref if r["sentiment"] == "negative")
        ref_n = len(ref)
        ref_neg_pct = (ref_neg / ref_n * 100) if ref_n else 0
        if ref_neg_pct >= 25:
            alert = "critical"
        elif ref_neg_pct >= 15:
            alert = "warning"
        elif ref_n >= 5 and ref_neg_pct >= 10:
            alert = "watch"

        snippet, snippet_date = pick_top_snippet(
            matched, code, keywords, window_end,
            seat_meta=meta_by_code.get(code), state_key=st,
        )

        by_dun[code] = {
            "mentions_total": total,
            "mentions_24h": len(m24),
            "mentions_7d": len(m7),
            "neg_pct": neg_pct,
            "pos_pct": pos_pct,
            "neu_pct": neu_pct,
            "lean": lean,
            "lean_label": lean_label,
            "emotion": emo_mix,
            "emotion_top": emo_top,
            "demo_mix": demo_mix,
            "demo_top": demo_top,
            "demo_insight": demo_insight,
            "narrative_split_pct": split_pct,
            "top_issues": top_issues,
            "confidence": confidence_level(total),
            "sentiment_labeled_pct": round(labeled / total * 100, 1) if total else 0.0,
            "engagement_total": sum(r["engagement"] for r in matched),
            "engagement_24h": sum(r["engagement"] for r in m24),
            "platforms": dict(plats.most_common(4)),
            "alert_level": alert,
            "top_snippet": snippet,
            "top_snippet_date": snippet_date,
        }

    return {
        "meta": {
            "state": state_key,
            "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "master_source": " + ".join(master_sources),
            "state_rows_scanned": len(state_rows),
            "window_end_utc": window_end.isoformat() if window_end else None,
            "headline_max_age_days": HEADLINE_MAX_AGE_DAYS,
            "window_24h_note": "24j = 24 jam sebelum tarikh crawl terakhir dalam master",
        },
        "byDun": by_dun,
        "rollup": {
            "mentions_total_state": len(state_rows),
            "seats_with_mentions": sum(1 for d in by_dun.values() if d["mentions_total"] > 0),
            "seats_with_recent_headline": sum(1 for d in by_dun.values() if d.get("top_snippet")),
            "top_seats_24h": sorted(
                [(c, d["mentions_24h"]) for c, d in by_dun.items() if d["mentions_24h"] > 0],
                key=lambda x: -x[1],
            )[:8],
            "state_lean": _state_lean(state_rows),
            "state_emotion": _state_emotion(state_rows),
            "state_demo": _state_demo(state_rows),
            "top_issues_state": _state_top_issues(state_rows),
        },
    }


def _state_lean(rows: List[dict]) -> dict:
    total = len(rows) or 1
    pos = sum(1 for r in rows if r["sentiment"] == "positive")
    neg = sum(1 for r in rows if r["sentiment"] == "negative")
    neu = total - pos - neg
    return {
        "sokong": round(pos / total * 100, 1),
        "atas_pagar": round(neu / total * 100, 1),
        "menentang": round(neg / total * 100, 1),
    }


def _state_emotion(rows: List[dict]) -> dict:
    c = Counter(r["emotion"] for r in rows)
    total = len(rows) or 1
    return {k: round(v / total * 100, 1) for k, v in c.most_common() if k != "neutral"}


def _state_demo(rows: List[dict]) -> dict:
    c = Counter(r.get("demographic") or "unknown" for r in rows)
    total = len(rows) or 1
    return {k: round(v / total * 100, 1) for k, v in c.most_common()}


def _state_top_issues(rows: List[dict]) -> list:
    c: Counter = Counter()
    for r in rows:
        for iss in detect_issues(r["text"]):
            c[iss] += 1
    return [{"issue": k, "mentions": v} for k, v in c.most_common(8)]


def find_pas_break_master() -> Optional[Path]:
    master_dir = ROOT / "data/projects/political/pas_break_2026/master"
    candidates = sorted(
        master_dir.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def find_johor_master() -> Optional[Path]:
    master_dir = ROOT / "data/projects/political/PRN/PRN_Johor/master"
    candidates = sorted(
        master_dir.glob("PRN_Johor_Master_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_geo_seats(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
