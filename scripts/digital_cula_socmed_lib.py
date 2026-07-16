#!/usr/bin/env python3
"""Digital cula socmed — seed post planning, URL registry, crawl trigger (N9 first)."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUERIES_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_36dun_crawl_queries.json"
MANIFEST_JSON = (
    ROOT
    / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/insightpulse/prn-monitoring/data/prn_excel_intel_manifest.json"
)
CULA_ROOT = ROOT / "data/projects/political/PRN/digital_cula"
BATCH_DIR = ROOT / "data/projects/political/PRN/_shared/url_batches/cula_seeds_N9"
API_BASE = "http://localhost:8001"
MYT = timezone(timedelta(hours=8))

TREKS = ("lokaliti", "umdap", "isu")
STATUSES = ("planned", "posted", "url_registered", "crawl_queued", "crawled", "failed")

# Jam tunggu sebelum crawl disyorkan (fleksibel — bukan fix 3 hari)
WAIT_PRESETS = (
    {"hours": 12, "label": "12 jam"},
    {"hours": 24, "label": "24 jam (1 hari)"},
    {"hours": 48, "label": "2 hari"},
    {"hours": 72, "label": "3 hari"},
    {"hours": 0, "label": "Segera (bila URL didaftar)"},
)
DEFAULT_WAIT_HOURS = 24

SEED_TEMPLATES = {
    "WAJIB-PAS23": [
        'agaknya di {name} ni PAS menang ok ke? tengok ramai bincang pasal {issue} je',
        'korang area {landmark} — undi kali ni ikut parti ke ikut calon?',
        'siapa lagi kat {name} rasa {issue} makin susah ni?',
    ],
    "IMBANG": [
        'area {name} — BN ke PAS ke PH yg lebih sesuai kali ni?',
        'tengok {landmark}, ramai bincang pasal {issue}. korang macam mana?',
        'agaknya kerusi {name} flip ke kali ni?',
    ],
    "LAWAN": [
        'korang {name} — kestabilan ke perubahan yg korang nak?',
        'tengok isu {issue} kat {landmark}, ada calon yg boleh selesaikan ke?',
        'PRN kali ni {name} — sokong status quo ke nak perubahan?',
    ],
}

TREK_EXTRA = {
    "umdap": [
        'korang {name} — UMDAP ni ok ke? UMNO+DAP rasa pelik sikit',
        'area {landmark} — ramai cakap tolak kerajaan perpaduan. korang setuju?',
        '{name}: Melayu Islam kekal dengan UMNO asal ke ikut UMDAP?',
    ],
    "isu": [
        'isu {issue} kat {landmark} — siapa yg boleh selesaikan untuk {name}?',
        'warga {name}, {issue} makin teruk. calon mana yg dengar suara kita?',
        'korang {name} — isu {issue} jadi faktor undi ke?',
    ],
}

PLATFORM_HINTS = {
    "bandar": ["facebook", "tiktok", "threads"],
    "felda": ["facebook"],
    "mixed": ["facebook", "tiktok"],
    "default": ["facebook", "tiktok"],
}


def now_iso() -> str:
    return datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")


def wait_label(hours: int) -> str:
    if hours <= 0:
        return "segera"
    if hours < 24:
        return f"{hours} jam"
    if hours % 24 == 0:
        d = hours // 24
        return f"{d} hari" if d > 1 else "1 hari"
    return f"{hours} jam"


def parse_wait_hours(body: dict, fallback: int = DEFAULT_WAIT_HOURS) -> int:
    if body.get("wait_hours") is not None:
        try:
            return max(0, int(body["wait_hours"]))
        except (TypeError, ValueError):
            pass
    preset = str(body.get("wait_preset") or "").strip().lower()
    for p in WAIT_PRESETS:
        if preset == p["label"].lower() or preset == str(p["hours"]):
            return p["hours"]
    return fallback


def parse_dt_myt(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    s = str(raw).strip()
    for fmt, n in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            dt = datetime.strptime(s[:n], fmt)
            return dt.replace(tzinfo=MYT)
        except ValueError:
            continue
    return None


def compute_crawl_due(posted_at: str, wait_hours: int) -> str:
    base = parse_dt_myt(posted_at) or datetime.now(MYT)
    due = base + timedelta(hours=wait_hours)
    return due.strftime("%Y-%m-%d %H:%M:%S")


def is_due(crawl_due_at: Optional[str]) -> bool:
    """True if crawl/recommended window has passed (or no due set)."""
    if not crawl_due_at:
        return True
    due = parse_dt_myt(crawl_due_at)
    if not due:
        return True
    return datetime.now(MYT) >= due


def seeds_path(state: str) -> Path:
    d = CULA_ROOT / state
    d.mkdir(parents=True, exist_ok=True)
    return d / "socmed_seeds.json"


def hub_path(state: str) -> Path:
    return CULA_ROOT / state / "socmed_hub.json"


def load_seeds(state: str) -> List[dict]:
    p = seeds_path(state)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("seeds", [])
    except json.JSONDecodeError:
        return []


def save_seeds(state: str, seeds: List[dict]) -> None:
    seeds_path(state).write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")


def norm_dun(raw: str) -> Optional[str]:
    s = str(raw or "").strip().upper().replace(".", "")
    m = re.search(r"\bN(\d{1,2})\b", s)
    return f"N{int(m.group(1)):02d}" if m else None


def load_n9_seats() -> List[dict]:
    if not QUERIES_JSON.exists():
        return []
    return json.loads(QUERIES_JSON.read_text(encoding="utf-8")).get("seats", [])


def load_intel_map() -> Dict[str, dict]:
    if not MANIFEST_JSON.exists():
        return {}
    data = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    out: Dict[str, dict] = {}
    for row in data.get("dun_keywords", []):
        if row.get("state") != "Negeri Sembilan":
            continue
        code = norm_dun(row.get("dun_code"))
        if code:
            out[code] = row
    return out


def first_part(raw: str, fallback: str = "") -> str:
    part = str(raw or "").split(";")[0].strip()
    return part or fallback


def suggest_posts(seat: dict, intel: dict, trek: str) -> List[str]:
    name = seat["name"]
    landmark = first_part(intel.get("local_landmarks"), name)
    issue = first_part(intel.get("local_issues") or intel.get("service_keywords"), "kos hidup")
    tier = seat.get("tier") or "LAWAN"

    if trek == "umdap":
        templates = TREK_EXTRA["umdap"]
    elif trek == "isu":
        templates = TREK_EXTRA["isu"]
    else:
        templates = SEED_TEMPLATES.get(tier, SEED_TEMPLATES["LAWAN"])

    return [t.format(name=name, landmark=landmark, issue=issue) for t in templates]


def platform_hints(seat: dict, intel: dict) -> List[str]:
    area = str(intel.get("area_type") or "").lower()
    issues = str(intel.get("local_issues") or "").lower()
    if "felda" in issues:
        return PLATFORM_HINTS["felda"]
    if area == "urban":
        return PLATFORM_HINTS["bandar"]
    if "cina" in str(intel.get("ethnic_mix") or "").lower():
        return PLATFORM_HINTS["mixed"]
    return PLATFORM_HINTS["default"]


def get_plan(state: str, kod_dun: str, trek: str = "lokaliti") -> dict:
    if state != "N9":
        return {"ok": False, "error": "Socmed seed plan — N9 sahaja setakat ini"}
    if trek not in TREKS:
        return {"ok": False, "error": f"Trek tidak sah: {trek}"}

    code = norm_dun(kod_dun)
    seats = {s["code"]: s for s in load_n9_seats()}
    seat = seats.get(code or "")
    if not seat:
        return {"ok": False, "error": f"Kerusi tidak dijumpai: {kod_dun}"}

    intel = load_intel_map().get(code, {})
    return {
        "ok": True,
        "state": state,
        "kod_dun": code,
        "dun_name": seat["name"],
        "tier": seat.get("tier"),
        "trek": trek,
        "trek_label": {"lokaliti": "Lokaliti DUN", "umdap": "UMDAP / Koalisi", "isu": "Isu Tempatan"}[trek],
        "landmarks": intel.get("local_landmarks") or seat["name"],
        "local_issues": intel.get("local_issues") or "kos hidup",
        "district": intel.get("district"),
        "suggested_posts": suggest_posts(seat, intel, trek),
        "platforms": platform_hints(seat, intel),
        "wait_presets": WAIT_PRESETS,
        "default_wait_hours": DEFAULT_WAIT_HOURS,
        "rules": [
            "Post santai — bukan page parti rasmi",
            "Kumpulan warga tempatan sahaja",
            "Tunggu tempoh pilihan (12j–3 hari) supaya komen organik masuk",
            "Paste URL post (bukan profil) — crawl bila ready",
        ],
    }


def validate_post_url(url: str) -> Tuple[bool, str]:
    u = (url or "").strip()
    if not u.startswith("http"):
        return False, "URL mesti bermula dengan http/https"
    low = u.lower()
    if any(x in low for x in ("facebook.com/profile.php?id=",)) and "/posts/" not in low and "story_fbid" not in low and "permalink" not in low:
        if "/groups/" not in low or "/posts/" not in low:
            pass  # allow group posts checked below
    if re.match(r"https?://(www\.)?facebook\.com/[^/]+/?$", u):
        return False, "Ini URL profil/halaman — paste URL post spesifik"
    host = urlparse(u).netloc.lower()
    if not any(d in host for d in ("facebook.com", "fb.com", "tiktok.com", "instagram.com", "threads.net", "x.com", "twitter.com")):
        return False, "Platform tidak disokong — guna FB/TikTok/IG/Threads/X"
    return True, ""


def _append_batch_file(code: str, name: str, url: str) -> None:
    if not BATCH_DIR.exists():
        return
    safe = name.replace(" ", "_")
    path = BATCH_DIR / f"{code}_{safe}_PASTE_ONLY.txt"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if url in text:
        return
    path.write_text(text.rstrip() + "\n" + url + "\n", encoding="utf-8")


def create_seed(state: str, body: dict) -> Tuple[dict, List[str]]:
    errors: List[str] = []
    code = norm_dun(body.get("kod_dun"))
    trek = (body.get("trek") or "lokaliti").lower()
    if not code:
        errors.append("kod_dun wajib")
    if trek not in TREKS:
        errors.append("trek mesti lokaliti | umdap | isu")
    if errors:
        return {}, errors

    plan = get_plan(state, code, trek)
    if not plan.get("ok"):
        return {}, [plan.get("error", "Plan gagal")]

    idx = int(body.get("suggestion_index") or 0)
    suggestions = plan.get("suggested_posts") or []
    post_text = (body.get("post_text") or "").strip() or (suggestions[idx] if suggestions else "")

    wait_hours = parse_wait_hours(body)
    seeds = load_seeds(state)
    posted_now = now_iso()
    row = {
        "id": str(uuid.uuid4()),
        "created_at": posted_now,
        "state": state,
        "kod_dun": code,
        "dun_name": plan["dun_name"],
        "tier": plan.get("tier"),
        "trek": trek,
        "trek_label": plan.get("trek_label"),
        "post_text_suggested": suggestions[idx] if suggestions else post_text,
        "post_text_actual": post_text,
        "platform": (body.get("platform") or "facebook").lower(),
        "group_name": (body.get("group_name") or "").strip(),
        "pelapor_id": (body.get("pelapor_id") or "HQ").strip(),
        "wait_hours": wait_hours,
        "wait_label": wait_label(wait_hours),
        "status": "posted" if body.get("mark_posted") else "planned",
        "posted_at": body.get("posted_at") or (posted_now if body.get("mark_posted") else None),
        "crawl_due_at": None,
        "post_url": None,
        "crawl_task_id": None,
        "crawl_at": None,
        "results": None,
        "notes": (body.get("notes") or "").strip(),
    }
    if row["status"] == "posted":
        if len(str(row["posted_at"])) <= 10:
            row["posted_at"] = posted_now
        row["crawl_due_at"] = compute_crawl_due(row["posted_at"], wait_hours)

    seeds.append(row)
    save_seeds(state, seeds)
    rebuild_socmed_hub(state)
    return row, []


def update_seed(state: str, seed_id: str, body: dict) -> Tuple[Optional[dict], Optional[str]]:
    seeds = load_seeds(state)
    idx = next((i for i, s in enumerate(seeds) if s.get("id") == seed_id), None)
    if idx is None:
        return None, "Rekod tidak dijumpai"

    row = seeds[idx]
    if body.get("mark_posted"):
        wh = parse_wait_hours(body, fallback=row.get("wait_hours", DEFAULT_WAIT_HOURS))
        row["status"] = "posted"
        row["posted_at"] = body.get("posted_at") or now_iso()
        row["wait_hours"] = wh
        row["wait_label"] = wait_label(wh)
        row["crawl_due_at"] = compute_crawl_due(row["posted_at"], wh)
        if body.get("post_text_actual"):
            row["post_text_actual"] = body["post_text_actual"]

    if body.get("post_url"):
        ok, err = validate_post_url(body["post_url"])
        if not ok:
            return None, err
        url = body["post_url"].strip().split()[0]
        row["post_url"] = url
        row["status"] = "url_registered"
        row["platform"] = body.get("platform") or row.get("platform") or "facebook"
        row["group_name"] = body.get("group_name") or row.get("group_name") or ""
        _append_batch_file(row["kod_dun"], row["dun_name"], url)

    if body.get("notes") is not None:
        row["notes"] = body["notes"]

    seeds[idx] = row
    save_seeds(state, seeds)
    rebuild_socmed_hub(state)
    return row, None


def list_due(state: str) -> List[dict]:
    due = []
    for s in load_seeds(state):
        if s.get("status") != "url_registered" or not s.get("post_url"):
            continue
        if is_due(s.get("crawl_due_at")):
            due.append(s)
    return due


def trigger_crawl(state: str, *, seed_ids: Optional[List[str]] = None, all_ready: bool = False) -> dict:
    import requests

    seeds = load_seeds(state)
    if seed_ids:
        targets = [s for s in seeds if s.get("id") in seed_ids and s.get("post_url")]
    elif all_ready:
        targets = list_due(state)
    else:
        targets = [s for s in seeds if s.get("status") == "url_registered" and s.get("post_url")]

    if not targets:
        return {"ok": False, "error": "Tiada URL siap untuk crawl", "tasks": []}

    by_dun: Dict[str, List[dict]] = {}
    for t in targets:
        by_dun.setdefault(t["kod_dun"], []).append(t)

    tasks = []
    api_ok = False
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        api_ok = r.status_code == 200
    except Exception:
        try:
            r = requests.get(f"{API_BASE}/", timeout=5)
            api_ok = r.status_code in (200, 404)
        except Exception:
            api_ok = False

    if not api_ok:
        return {
            "ok": False,
            "error": "InsightPulse backend (:8001) tidak hidup — jalankan ./start_full_app.sh",
            "tasks": [],
        }

    id_by_seed = {s["id"]: i for i, s in enumerate(seeds)}
    for code, group in sorted(by_dun.items()):
        urls = [g["post_url"] for g in group if g.get("post_url")]
        name = group[0].get("dun_name", code)
        payload = {
            "query": f"Cula seed {code} {name}",
            "platforms": ["facebook", "tiktok", "instagram", "x"],
            "analysis_type": "social_listening",
            "date_range": "7days",
            "dataset_size": 1000,
            "use_crawl_strategy": True,
            "project_id": "pas_break_2026",
            "analysis_focus": "comprehensive",
            "comment_sampling": "smart",
            "crawl_mode": "direct_url",
            "direct_urls": urls,
        }
        task_id = None
        err = None
        try:
            r = requests.post(f"{API_BASE}/analyze_async", json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            task_id = data.get("task_id")
        except Exception as exc:
            err = str(exc)

        for g in group:
            sid = g["id"]
            if sid not in id_by_seed:
                continue
            i = id_by_seed[sid]
            seeds[i]["status"] = "crawl_queued" if task_id else "failed"
            seeds[i]["crawl_task_id"] = task_id
            seeds[i]["crawl_at"] = now_iso() if task_id else None
            if err:
                seeds[i]["notes"] = (seeds[i].get("notes") or "") + f" crawl_err: {err}"

        tasks.append({"kod_dun": code, "dun_name": name, "urls": urls, "task_id": task_id, "error": err})

    save_seeds(state, seeds)
    rebuild_socmed_hub(state)
    return {"ok": True, "tasks": tasks, "count": len(tasks)}


def rebuild_socmed_hub(state: str) -> dict:
    seeds = load_seeds(state)
    today = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
    by_dun: Dict[str, dict] = {}

    for s in seeds:
        code = s.get("kod_dun")
        if not code:
            continue
        bucket = by_dun.setdefault(
            code,
            {
                "kod_dun": code,
                "dun_name": s.get("dun_name"),
                "seeds_total": 0,
                "posted": 0,
                "url_registered": 0,
                "crawl_queued": 0,
                "crawled": 0,
                "due_for_crawl": 0,
                "treks": {"lokaliti": 0, "umdap": 0, "isu": 0},
            },
        )
        bucket["seeds_total"] += 1
        st = s.get("status") or "planned"
        if st in bucket:
            bucket[st] = bucket.get(st, 0) + 1
        trek = s.get("trek") or "lokaliti"
        if trek in bucket["treks"]:
            bucket["treks"][trek] += 1
        if st == "url_registered" and s.get("post_url") and is_due(s.get("crawl_due_at")):
            bucket["due_for_crawl"] += 1

    hub = {
        "updated_at": now_iso(),
        "state": state,
        "seeds_total": len(seeds),
        "seats_active": len(by_dun),
        "due_for_crawl": sum(b["due_for_crawl"] for b in by_dun.values()),
        "by_dun": by_dun,
        "recent": list(reversed(seeds[-20:])),
    }
    hub_path(state).write_text(json.dumps(hub, ensure_ascii=False, indent=2), encoding="utf-8")
    proto = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
    proto.mkdir(parents=True, exist_ok=True)
    (proto / f"cula_socmed_hub_{state}.json").write_text(
        json.dumps(hub, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return hub
