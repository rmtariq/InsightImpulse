#!/usr/bin/env python3
"""Sync Action Center tasks from digital cula hub + verified submissions."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
PRN_ROOT = ROOT / "data/projects/political/PRN"
LIVE_ROOT = PRN_ROOT / "warroom_live"
PROTO_DATA = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"

PRODUCTION_DUN = {
    "N9": PROTO_DATA / "warroom_dun_N9_production.json",
}

MYT = timezone(timedelta(hours=8))
URGENT_KEYWORDS = re.compile(r"segera|kritikal|urgent|penting|viral|risiko", re.I)


def cula_actions_path(state: str) -> Path:
    return LIVE_ROOT / state / "cula_generated_actions.json"


def norm_dun_code(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip().upper().replace(".", "")
    m = re.search(r"\bN(\d{1,2})\b", s)
    if m:
        return f"N{int(m.group(1)):02d}"
    return None


def now_iso() -> str:
    return datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")


def load_mn_seats(state: str) -> Set[str]:
    path = PRODUCTION_DUN.get(state)
    codes: Set[str] = set()
    if not path or not path.exists():
        return codes
    seats = json.loads(path.read_text(encoding="utf-8"))
    for seat in seats if isinstance(seats, list) else []:
        bv = (seat.get("spr2023") or {}).get("blocVotes") or {}
        pn = int(bv.get("PN") or 0)
        bn = int(bv.get("BN") or 0)
        ph = int(bv.get("PH") or 0)
        if pn + bn <= ph:
            continue
        code = norm_dun_code(seat.get("id"))
        if code:
            codes.add(code)
    return codes


def _parse_ts(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[: len(fmt)], fmt)
            return dt.replace(tzinfo=MYT)
        except ValueError:
            continue
    return None


def sync_cula_actions(state: str, hub: dict, submissions: List[dict]) -> dict:
    """Rebuild auto-generated Action Center rows from cula data."""
    mn_seats = load_mn_seats(state)
    by_dun: Dict[str, dict] = hub.get("byDun") or {}
    actions: List[dict] = []
    generated = now_iso()
    seen_ids: Set[str] = set()

    def add(action: dict) -> None:
        aid = action.get("id")
        if not aid or aid in seen_ids:
            return
        seen_ids.add(aid)
        actions.append(action)

    for code in sorted(mn_seats):
        slot = by_dun.get(code) or {}
        name = slot.get("name") or code
        delta_24h = int(slot.get("verified_delta_24h") or 0)
        if delta_24h > 0:
            continue
        last = slot.get("last_verified_at") or "tiada"
        add({
            "id": f"ACT-{state}-CULA-GAP-{code}",
            "title": f"Sahkan kemas kini cula di {code} {name}",
            "category": "lapangan",
            "priority": "p1",
            "status": "baru",
            "owner": "Ketua Operasi DUN",
            "due": "Hari ini 18:00",
            "dun": code,
            "seat": name,
            "locality": "Semua PDM",
            "reason": "Tiada kemasukan cula verified dalam 24 jam terakhir untuk kerusi sasaran MN.",
            "evidence": [
                f"Delta cula 24j: {delta_24h}",
                f"Kemaskini terakhir: {last}",
                "Kerusi dalam sasaran 20 MN",
            ],
            "recommended_steps": [
                "Hubungi ketua PDM dan sahkan lawatan hari ini.",
                "Hantar laporan cula melalui borang atau CSV batch.",
                "Tandakan Mula/Siap di Action Center sebelum war room malam.",
            ],
            "impact_metric": "Sekurang-kurangnya 1 laporan cula verified hari ini",
            "source": "cula_auto",
            "cula_rule": "gap_24h",
            "generated_at": generated,
        })

    for code in sorted(mn_seats):
        slot = by_dun.get(code) or {}
        pending = int(slot.get("pending_count") or 0)
        if pending <= 0:
            continue
        name = slot.get("name") or code
        add({
            "id": f"ACT-{state}-CULA-PEND-{code}",
            "title": f"Semak {pending} laporan cula pending — {code} {name}",
            "category": "lapangan",
            "priority": "p2",
            "status": "baru",
            "owner": "HQ Operasi",
            "due": "Hari ini",
            "dun": code,
            "seat": name,
            "locality": "HQ semakan",
            "reason": f"{pending} laporan cula menunggu pengesahan HQ untuk kerusi MN.",
            "evidence": [f"Pending count: {pending}", "Sumber: Laporan Cula Harian"],
            "recommended_steps": [
                "Semak rekod pending di modul Laporan Cula.",
                "Verify atau reject dengan nota reviewer.",
                "Pastikan hub cula dikemaskini selepas semakan.",
            ],
            "impact_metric": "Semua pending DUN ini diselesaikan hari ini",
            "source": "cula_auto",
            "cula_rule": "pending_review",
            "generated_at": generated,
        })

    cut = datetime.now(MYT) - timedelta(hours=48)
    for row in submissions:
        if (row.get("status") or "").lower() != "verified":
            continue
        catatan = (row.get("catatan") or "").strip()
        if len(catatan) < 8 or catatan.lower() in {"whatsapp batch", "batch upload"}:
            continue
        code = norm_dun_code(row.get("kod_dun"))
        if not code or code not in mn_seats:
            continue
        reviewed = _parse_ts(row.get("reviewed_at") or row.get("created_at") or "")
        if reviewed and reviewed < cut:
            continue
        sub_id = str(row.get("id") or "")
        if not sub_id:
            continue
        short_id = re.sub(r"[^A-Za-z0-9]", "", sub_id)[:10].upper()
        name = row.get("dun_name") or (by_dun.get(code) or {}).get("name") or code
        pdm = row.get("pdm") or "PDM"
        cula = int(float(row.get("cula_baharu") or 0))
        priority = "p1" if URGENT_KEYWORDS.search(catatan) else "p2"
        title = catatan if len(catatan) <= 90 else catatan[:87] + "…"
        add({
            "id": f"ACT-{state}-CULA-NOTE-{short_id}",
            "title": title,
            "category": "lapangan",
            "priority": priority,
            "status": "baru",
            "owner": (row.get("pelapor_nama") or row.get("pelapor_id") or "Ketua Operasi DUN").strip(),
            "due": "Hari ini" if priority == "p1" else "Esok 12:00",
            "dun": code,
            "seat": name,
            "locality": pdm,
            "reason": f"Laporan cula {row.get('tarikh_lawatan')} — {pdm}: {catatan}",
            "evidence": [
                f"Cula baharu: {cula}",
                f"Pelapor: {row.get('pelapor_id') or '—'}",
                f"Tarikh lawatan: {row.get('tarikh_lawatan') or '—'}",
            ],
            "recommended_steps": [
                "Semak catatan lapangan dan sahkan dengan ketua PDM.",
                "Ambil tindakan susulan jika isu kritikal.",
                "Rekod impak selepas tindakan selesai.",
            ],
            "impact_metric": "Susulan catatan lapangan direkod dalam 24 jam",
            "source": "cula_auto",
            "cula_rule": "field_note",
            "submission_id": sub_id,
            "generated_at": generated,
        })

    payload = {
        "meta": {
            "state": state,
            "generated": generated,
            "source": "cula_action_bridge",
            "mn_seats": len(mn_seats),
            "count": len(actions),
        },
        "actions": actions,
    }
    out = cula_actions_path(state)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from digital_cula_lib import hub_path, read_submissions, rebuild_hub

    st = sys.argv[1] if len(sys.argv) > 1 else "N9"
    hub = json.loads(hub_path(st).read_text(encoding="utf-8"))
    subs = read_submissions(st)
    result = sync_cula_actions(st, hub, subs)
    print(f"Synced {result['meta']['count']} cula actions for {st}")
