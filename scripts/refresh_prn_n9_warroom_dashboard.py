#!/usr/bin/env python3
"""
Refresh PRN N9 War Room dashboard — Pengundi 4-post + 36 DUN + naratif Cina/India.

Jalankan selepas crawl/merge baru:
  python3 scripts/refresh_prn_n9_warroom_dashboard.py
  python3 scripts/refresh_prn_n9_warroom_dashboard.py --skip-build   # hanya patch JSON
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
DUN_JSON = PROTO / "warroom_dun_N9_production.json"
NARRATIVE_JSON = PROTO / "n9_narrative_community.json"
SOCIAL_JSON = PROTO / "n9_social_summary.json"
BUNDLE_JSON = PROTO / "n9_production_bundle.json"
ACTIONS_JSON = PROTO / "n9_actions_v2.json"
PY = ROOT / "NEImpulse/bin/python"


def _py() -> str:
    if PY.exists():
        return str(PY)
    return sys.executable


def norm_dun(code: str) -> str:
    if not code:
        return ""
    s = str(code).strip().upper().replace(".", "")
    m = re.match(r"^(?:NS-)?N0*(\d+)$", s)
    return f"N{int(m.group(1)):02d}" if m else s


def _load(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_builds() -> None:
    py = _py()
    for script in (
        "scripts/build_warroom_narrative_json.py",
        "scripts/build_warroom_production_bundle.py",
    ):
        print(f"▶ {script}")
        subprocess.run([py, str(ROOT / script)], cwd=str(ROOT), check=False)

    print("▶ scripts/sync_pengundi_4posts_warroom.py")
    subprocess.run([py, str(ROOT / "scripts/sync_pengundi_4posts_warroom.py")], cwd=str(ROOT), check=False)


def _narrative_index(narr: dict) -> dict:
    """Map N01..N36 → narrative row + actions."""
    n9 = (narr or {}).get("N9") or {}
    by_code: dict[str, dict] = {}

    for row in n9.get("dunRows") or []:
        if not row:
            continue
        code = norm_dun(row[0])
        by_code.setdefault(code, {})
        by_code[code]["dunRow"] = {
            "code": code,
            "name": row[1] if len(row) > 1 else "",
            "tier": row[2] if len(row) > 2 else "Pantau",
            "topIssue": row[3] if len(row) > 3 else "Other",
            "sentiment": row[4] if len(row) > 4 else "Neutral",
        }

    for act in n9.get("actions") or []:
        meta = act.get("meta") or []
        dun_raw = next((m for m in meta if re.search(r"N\d+", str(m), re.I)), None)
        if not dun_raw:
            continue
        code = norm_dun(str(dun_raw))
        slot = by_code.setdefault(code, {})
        slot.setdefault("actions", []).append({
            "id": act.get("id"),
            "p": act.get("p"),
            "comm": act.get("comm"),
            "title": act.get("title"),
            "body": (act.get("body") or "")[:200],
            "response": act.get("response"),
            "team": act.get("team"),
        })

    return {
        "by_code": by_code,
        "state": {
            "chinese": n9.get("chinese") or {},
            "indian": n9.get("indian") or {},
            "issues": n9.get("issues") or {},
            "responses": n9.get("responses") or {},
            "label": n9.get("label") or "Negeri Sembilan",
            "dun": n9.get("dun") or 36,
        },
        "meta": (narr or {}).get("meta") or {},
    }


def _pengundi_state_signal(social: dict) -> dict:
    block = (social or {}).get("pengundiMacPosts") or {}
    post3 = block.get("post3_poll") or {}
    posts = block.get("posts") or []
    coop_pcts = []
    for p in posts:
        ins = p.get("insight") or ""
        if "Setuju" in ins or "setuju" in ins:
            m = re.search(r"(\d+(?:\.\d+)?)%", ins)
            if m:
                coop_pcts.append(float(m.group(1)))
    return {
        "label": block.get("label"),
        "updated": block.get("updated"),
        "total_comments": (block.get("summary") or {}).get("total_comments_crawled"),
        "total_engagement": (block.get("summary") or {}).get("total_engagement"),
        "poll_bn_pn_pct": post3.get("sokong_bn_pn_pct"),
        "poll_ph_pct": post3.get("sokong_ph_pct"),
        "cooperation_setuju_avg": round(sum(coop_pcts) / len(coop_pcts), 1) if coop_pcts else None,
        "headline": block.get("strategic_headline"),
        "kesimpulan": block.get("kesimpulan_gabungan"),
    }


def _tactical_note(seat: dict, narr_idx: dict, peng: dict) -> str:
    demo = seat.get("demo") or {}
    chinese = float(demo.get("chinese") or 0)
    indian = float(demo.get("indian") or 0)
    code = norm_dun(seat.get("id", ""))
    row = (narr_idx["by_code"].get(code) or {}).get("dunRow") or {}
    issues = narr_idx["state"]["issues"]
    parts = []

    if row.get("topIssue") and row["topIssue"] != "Other":
        parts.append(f"Isu naratif: {row['topIssue']} ({row.get('sentiment', '—')})")
    elif chinese >= 30:
        top = (issues.get("chinese") or [[None]])[0]
        if top and top[0] != "Other":
            parts.append(f"Komuniti Cina {chinese:.0f}% — isu: {top[0]}")
    elif indian >= 15:
        top = (issues.get("indian") or [[None]])[0]
        if top and top[0] != "Other":
            parts.append(f"Komuniti India {indian:.0f}% — isu: {top[0]}")

    if peng.get("poll_bn_pn_pct"):
        parts.append(f"Signal Pengundi MY: BN+PN {peng['poll_bn_pn_pct']}% (poll N9)")
    if peng.get("cooperation_setuju_avg"):
        parts.append(f"Kerjasama UMNO-PAS ~{peng['cooperation_setuju_avg']}% setuju (komen)")

    mn = seat.get("demo") and float(demo.get("malay") or 0) >= 55
    if mn and not parts:
        parts.append("Majoriti Melayu — frame MN + adat/Undang (selari Post 1–2 Pengundi MY)")

    return " · ".join(parts) if parts else "Pantau naratif negeri + ground cula"


def patch_dun_seats(narr_idx: dict, peng: dict) -> int:
    seats = _load(DUN_JSON)
    if not isinstance(seats, list):
        print("⚠ Skip DUN patch — warroom_dun_N9_production.json missing")
        return 0

    state_issues = narr_idx["state"]["issues"]
    top_chinese = (state_issues.get("chinese") or [["Other", 0]])[0]
    top_indian = (state_issues.get("indian") or [["Other", 0]])[0]

    for seat in seats:
        code = norm_dun(seat.get("id", ""))
        demo = seat.get("demo") or {}
        chinese_pct = float(demo.get("chinese") or 0)
        indian_pct = float(demo.get("indian") or 0)
        slot = narr_idx["by_code"].get(code) or {}
        row = slot.get("dunRow") or {}
        actions = slot.get("actions") or []

        comm = {
            "chinese": None,
            "indian": None,
            "pengundi": peng,
            "actions": actions[:3],
            "tacticalNote": _tactical_note(seat, narr_idx, peng),
        }

        if row or chinese_pct >= 20:
            comm["chinese"] = {
                "tier": row.get("tier") or ("Pantau" if chinese_pct >= 25 else "Rujukan"),
                "topIssue": row.get("topIssue") or top_chinese[0],
                "sentiment": row.get("sentiment") or "Neutral",
                "dpiPct": round(chinese_pct, 1),
                "statePosts": narr_idx["state"]["chinese"].get("posts"),
            }
        if row or indian_pct >= 10:
            comm["indian"] = {
                "tier": row.get("tier") or ("Pantau" if indian_pct >= 12 else "Rujukan"),
                "topIssue": row.get("topIssue") if row.get("comm") == "indian" else top_indian[0],
                "sentiment": row.get("sentiment") or "Neutral",
                "dpiPct": round(indian_pct, 1),
                "statePosts": narr_idx["state"]["indian"].get("posts"),
            }

        seat["narrativeComm"] = comm
        if comm["tacticalNote"]:
            extra = comm["tacticalNote"]
            if extra not in (seat.get("action") or ""):
                seat["action"] = f"{seat.get('action', '')} · {extra}".strip(" ·")

    _save(DUN_JSON, seats)
    return len(seats)


def _bump_coalition(coalition: list, name: str, mp_delta: int, reason: str) -> None:
    for c in coalition or []:
        if c.get("name") == name:
            c["majorityPct"] = int(max(2, min(97, (c.get("majorityPct") or 0) + mp_delta)))
            c["pengundiNudge"] = reason
            if c.get("expectedSeats") is not None and mp_delta:
                c["expectedSeats"] = round((c.get("expectedSeats") or 0) + mp_delta * 0.05, 1)
            break


def patch_social_and_bundle(peng: dict, narr_idx: dict) -> None:
    for path in (SOCIAL_JSON, BUNDLE_JSON):
        data = _load(path)
        if not isinstance(data, dict):
            continue

        target = data
        if path == BUNDLE_JSON:
            target = data.setdefault("socialSummary", data)

        cf = target.setdefault("coalitionFormation", {})
        signals = cf.setdefault("crawlSignals", {})
        signals["pengundiMac4Posts"] = {
            "comments": peng.get("total_comments"),
            "engagement": peng.get("total_engagement"),
            "poll_bn_pn_pct": peng.get("poll_bn_pn_pct"),
            "poll_ph_pct": peng.get("poll_ph_pct"),
            "cooperation_setuju_avg": peng.get("cooperation_setuju_avg"),
            "updated": peng.get("updated"),
        }
        notes = list(cf.get("crawlNotes") or [])
        if peng.get("poll_bn_pn_pct"):
            note = (
                f"Pengundi MY 4-post: poll BN+PN {peng['poll_bn_pn_pct']}% vs PH {peng.get('poll_ph_pct')}% "
                f"({peng.get('total_comments', 0):,} komen)"
            )
            if note not in notes:
                notes.insert(0, note)
        cf["crawlNotes"] = notes[:12]

        coalition = target.get("coalition") or []
        if peng.get("poll_bn_pn_pct") and float(peng["poll_bn_pn_pct"]) >= 65:
            _bump_coalition(coalition, "MN (PAS+BN)", +3, "Pengundi MY poll BN+PN dominan")
            _bump_coalition(coalition, "PH (Madani)", -2, "Pengundi MY poll PH lemah")
            _bump_coalition(coalition, "#3 MN ★", +2, "Pengundi MY — sokongan komen MN")
        target["coalition"] = sorted(coalition, key=lambda x: -(x.get("majorityPct") or x.get("pct") or 0))

        target["narrativeCommunity"] = {
            "updated": narr_idx["meta"].get("generated_at"),
            "chinese_posts": narr_idx["state"]["chinese"].get("posts"),
            "indian_posts": narr_idx["state"]["indian"].get("posts"),
            "top_chinese_issue": (narr_idx["state"]["issues"].get("chinese") or [[None]])[0][0],
            "top_indian_issue": (narr_idx["state"]["issues"].get("indian") or [[None]])[0][0],
            "dun_with_narrative": len(narr_idx["by_code"]),
            "pengundi_sync": peng.get("updated"),
        }

        if path == BUNDLE_JSON:
            data["socialSummary"] = target
            if data.get("pengundiMacPosts"):
                data["narrativeCommunity"] = target["narrativeCommunity"]
        _save(path, data)


def patch_narrative_actions(narr_idx: dict) -> int:
    actions_data = _load(ACTIONS_JSON)
    if not isinstance(actions_data, dict):
        return 0

    existing_ids = {a.get("id") for a in actions_data.get("actions") or []}
    added = 0
    new_actions = list(actions_data.get("actions") or [])

    for code, slot in narr_idx["by_code"].items():
        for act in slot.get("actions") or []:
            aid = act.get("id")
            if not aid or aid in existing_ids:
                continue
            comm = act.get("comm") or "chinese"
            new_actions.append({
                "id": aid,
                "title": act.get("title") or f"Naratif {comm} — {code}",
                "category": "naratif",
                "priority": act.get("p") or "p1",
                "status": "baru",
                "owner": act.get("team") or "Communications",
                "due": "Hari ini",
                "dun": code,
                "seat": (slot.get("dunRow") or {}).get("name") or code,
                "locality": f"Komuniti {comm}",
                "reason": (act.get("body") or "")[:180],
                "evidence": [f"Naratif {comm} live", f"DUN {code}"],
                "recommended_steps": [
                    act.get("response") or "Semak fakta dan sediakan respons rasmi.",
                    "Kelulusan pengurus komunikasi sebelum siar.",
                ],
                "impact_metric": "1 respons disahkan + 1 saluran komuniti",
                "source": "narrative_community",
            })
            existing_ids.add(aid)
            added += 1

    actions_data["actions"] = new_actions
    actions_data.setdefault("meta", {})["narrativeSync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save(ACTIONS_JSON, actions_data)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh PRN N9 War Room dashboard")
    parser.add_argument("--skip-build", action="store_true", help="Skip narrative/bundle rebuild")
    args = parser.parse_args()

    if not args.skip_build:
        run_builds()
    else:
        py = _py()
        subprocess.run([py, str(ROOT / "scripts/sync_pengundi_4posts_warroom.py")], cwd=str(ROOT), check=False)

    social = _load(SOCIAL_JSON) or {}
    narr = _load(NARRATIVE_JSON) or {}
    narr_idx = _narrative_index(narr if isinstance(narr, dict) else {})
    peng = _pengundi_state_signal(social)

    dun_count = patch_dun_seats(narr_idx, peng)
    patch_social_and_bundle(peng, narr_idx)
    narr_actions = patch_narrative_actions(narr_idx)

    print("")
    print("✅ PRN N9 War Room dashboard refreshed")
    print(f"   36 DUN patched: {dun_count} kerusi · narrativeComm overlay")
    print(f"   Pengundi: {peng.get('total_comments', 0):,} komen · poll BN+PN {peng.get('poll_bn_pn_pct')}%")
    print(f"   Naratif Cina: {narr_idx['state']['chinese'].get('posts', 0)} post · India: {narr_idx['state']['indian'].get('posts', 0)} post")
    print(f"   Action Center: +{narr_actions} tindakan naratif P1")
    print("   Refresh browser: http://localhost:8080/ (Cmd+Shift+R)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
