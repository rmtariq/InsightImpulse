#!/usr/bin/env python3
"""Digital culaan — CSV storage, validation, hub aggregation (N9, Johor, Melaka)."""
from __future__ import annotations

import csv
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
PRN_ROOT = ROOT / "data/projects/political/PRN"
CULA_ROOT = PRN_ROOT / "digital_cula"
PROTOTYPE_DATA = (
    ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data"
)
N9_DPI = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_dpi_updates.json"

STATES = ("N9", "Johor", "Melaka")
WARROOM_DUN = {
    "N9": PROTOTYPE_DATA / "warroom_dun_N9.json",
    "Johor": PROTOTYPE_DATA / "warroom_dun_Johor.json",
    "Melaka": PROTOTYPE_DATA / "warroom_dun_Melaka.json",
}

TEMPLATE_HEADERS = [
    "tarikh_lawatan",
    "kod_dun",
    "pdm",
    "pelapor_id",
    "pelapor_nama",
    "jenis_aktiviti",
    "rumah_dilawati",
    "cula_baharu",
    "cula_bulan",
    "cula_condong",
    "cula_atas_pagar",
    "cula_dacing",
    "catatan",
]

CSV_FIELDS = [
    "id",
    "created_at",
    "tarikh_lawatan",
    "state",
    "kod_dun",
    "dun_name",
    "pdm",
    "pelapor_id",
    "pelapor_nama",
    "jenis_aktiviti",
    "rumah_dilawati",
    "cula_baharu",
    "cula_bulan",
    "cula_condong",
    "cula_atas_pagar",
    "cula_dacing",
    "catatan",
    "status",
    "reviewer",
    "reviewed_at",
    "reviewer_note",
    "flags",
]

MYT = timezone(timedelta(hours=8))


def now_myt() -> datetime:
    return datetime.now(MYT)


def now_iso() -> str:
    return now_myt().strftime("%Y-%m-%d %H:%M:%S")


def state_dir(state: str) -> Path:
    if state not in STATES:
        raise ValueError(f"Negeri tidak sah: {state}")
    d = CULA_ROOT / state
    d.mkdir(parents=True, exist_ok=True)
    return d


def csv_path(state: str) -> Path:
    p = state_dir(state) / "submissions.csv"
    if not p.exists():
        with p.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()
    return p


def hub_path(state: str) -> Path:
    return state_dir(state) / "cula_hub.json"


def prototype_hub_path(state: str) -> Path:
    PROTOTYPE_DATA.mkdir(parents=True, exist_ok=True)
    return PROTOTYPE_DATA / f"cula_hub_{state}.json"


def norm_dun_code(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip().upper().replace(".", "")
    m = re.search(r"\bN(\d{1,2})\b", s)
    if m:
        return f"N{int(m.group(1)):02d}"
    return None


def load_dun_catalog(state: str) -> Dict[str, str]:
    path = WARROOM_DUN.get(state)
    out: Dict[str, str] = {}
    if not path or not path.exists():
        return out
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        code = norm_dun_code(row.get("id"))
        if code:
            out[code] = str(row.get("name") or code)
    return out


def read_submissions(state: str) -> List[dict]:
    path = csv_path(state)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_submissions(state: str, rows: List[dict]) -> None:
    path = csv_path(state)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def _int(val: Any, default: int = 0) -> int:
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except (TypeError, ValueError):
        return default


def validate_submission(payload: dict, state: str) -> Tuple[dict, List[str]]:
    errors: List[str] = []
    flags: List[str] = []
    catalog = load_dun_catalog(state)

    kod = norm_dun_code(payload.get("kod_dun"))
    if not kod:
        errors.append("Kod DUN wajib (contoh N05).")
    elif catalog and kod not in catalog:
        errors.append(f"Kod DUN {kod} tidak dijumpai untuk negeri {state}.")

    tarikh = str(payload.get("tarikh_lawatan") or "").strip()
    if not tarikh:
        errors.append("Tarikh lawatan wajib.")
    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarikh):
        errors.append("Tarikh lawatan mesti YYYY-MM-DD.")

    pelapor_id = str(payload.get("pelapor_id") or "").strip()
    if len(pelapor_id) < 2:
        errors.append("ID pelapor wajib (min 2 aksara).")

    pdm = str(payload.get("pdm") or "").strip()
    if len(pdm) < 2:
        errors.append("PDM / kawasan wajib.")

    jenis = str(payload.get("jenis_aktiviti") or "").strip()
    allowed_jenis = {"door_to_door", "program", "follow_up", "lain"}
    if jenis not in allowed_jenis:
        errors.append("Jenis aktiviti tidak sah.")

    rumah = _int(payload.get("rumah_dilawati"))
    cula = _int(payload.get("cula_baharu"))
    bulan = _int(payload.get("cula_bulan"))
    condong = _int(payload.get("cula_condong"))
    pagar = _int(payload.get("cula_atas_pagar"))
    dacing = _int(payload.get("cula_dacing"))
    pecahan = bulan + condong + pagar + dacing

    if rumah < 0 or cula < 0:
        errors.append("Rumah dilawati dan cula baharu tidak boleh negatif.")
    if rumah == 0 and cula == 0:
        errors.append("Isi sekurang-kurangnya rumah dilawati atau cula baharu.")
    if pecahan > 0 and pecahan != cula:
        flags.append("pecahan_mismatch")
    if cula > 0 and rumah > 0 and cula > rumah * 3:
        flags.append("cula_high_vs_rumah")
    if cula > 500:
        flags.append("cula_volume_high")

    clean = {
        "id": str(payload.get("id") or uuid.uuid4().hex[:16]),
        "created_at": str(payload.get("created_at") or now_iso()),
        "tarikh_lawatan": tarikh,
        "state": state,
        "kod_dun": kod or "",
        "dun_name": catalog.get(kod, str(payload.get("dun_name") or "")),
        "pdm": pdm,
        "pelapor_id": pelapor_id,
        "pelapor_nama": str(payload.get("pelapor_nama") or "").strip(),
        "jenis_aktiviti": jenis,
        "rumah_dilawati": str(rumah),
        "cula_baharu": str(cula),
        "cula_bulan": str(bulan),
        "cula_condong": str(condong),
        "cula_atas_pagar": str(pagar),
        "cula_dacing": str(dacing),
        "catatan": str(payload.get("catatan") or "").strip()[:500],
        "status": str(payload.get("status") or "pending").lower(),
        "reviewer": str(payload.get("reviewer") or ""),
        "reviewed_at": str(payload.get("reviewed_at") or ""),
        "reviewer_note": str(payload.get("reviewer_note") or ""),
        "flags": "|".join(flags),
    }
    if clean["status"] not in {"pending", "verified", "rejected"}:
        clean["status"] = "pending"
    return clean, errors


def norm_date(raw: Any) -> Optional[str]:
    s = str(raw or "").strip()
    if not s:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def template_csv_text() -> str:
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(TEMPLATE_HEADERS)
    w.writerow([
        "2026-06-17", "N25", "Paroi A", "PDM-Paroi", "Ketua PDM Paroi",
        "door_to_door", "20", "12", "3", "5", "2", "2", "Contoh baris",
    ])
    return buf.getvalue()


def parse_csv_upload(text: str) -> List[dict]:
    """Parse CSV/TSV upload — header row required."""
    text = text.strip("\ufeff")
    if not text.strip():
        return []
    sample = text.splitlines()[0]
    delim = "\t" if sample.count("\t") >= sample.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delim)
    if not reader.fieldnames:
        return []
    norm_map = {}
    for h in reader.fieldnames:
        key = (h or "").strip().lower().replace(" ", "_")
        aliases = {
            "tarikh": "tarikh_lawatan",
            "date": "tarikh_lawatan",
            "dun": "kod_dun",
            "kod": "kod_dun",
            "kawasan": "pdm",
            "pelapor": "pelapor_id",
            "rumah": "rumah_dilawati",
            "cula": "cula_baharu",
            "bulan": "cula_bulan",
            "condong": "cula_condong",
            "pagar": "cula_atas_pagar",
            "atas_pagar": "cula_atas_pagar",
            "dacing": "cula_dacing",
        }
        norm_map[h] = aliases.get(key, key)
    out = []
    for i, row in enumerate(reader, start=2):
        mapped = {norm_map.get(k, k): v for k, v in row.items()}
        mapped["_line"] = i
        out.append(mapped)
    return out


def parse_whatsapp_lines(
    text: str,
    *,
    default_tarikh: str,
    default_pelapor: str,
) -> List[dict]:
    """
    Satu baris = satu laporan. Format:
      N25 | Paroi A | 20 rumah | 12 cula
      N25, Paroi A, 20, 12, 3, 5, 2, 2
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in re.split(r"[|,;]", line) if p.strip()]
        if len(parts) < 4:
            continue
        kod = norm_dun_code(parts[0])
        pdm = parts[1]
        rumah = re.sub(r"\D", "", parts[2]) or "0"
        cula = re.sub(r"\D", "", parts[3]) or "0"
        row = {
            "tarikh_lawatan": default_tarikh,
            "kod_dun": kod,
            "pdm": pdm,
            "pelapor_id": default_pelapor,
            "jenis_aktiviti": "door_to_door",
            "rumah_dilawati": rumah,
            "cula_baharu": cula,
            "cula_bulan": parts[4] if len(parts) > 4 else "0",
            "cula_condong": parts[5] if len(parts) > 5 else "0",
            "cula_atas_pagar": parts[6] if len(parts) > 6 else "0",
            "cula_dacing": parts[7] if len(parts) > 7 else "0",
            "catatan": "WhatsApp batch",
        }
        rows.append(row)
    return rows


def add_submission(state: str, payload: dict, *, auto_verify: bool = False, reviewer: str = "") -> Tuple[dict, List[str]]:
    row, errors = validate_submission(payload, state)
    if errors:
        return row, errors

    rows = read_submissions(state)
    if not auto_verify:
        cutoff = now_myt() - timedelta(minutes=10)
        for existing in reversed(rows[-50:]):
            if (
                existing.get("pelapor_id") == row["pelapor_id"]
                and existing.get("kod_dun") == row["kod_dun"]
                and existing.get("tarikh_lawatan") == row["tarikh_lawatan"]
                and existing.get("cula_baharu") == row["cula_baharu"]
                and existing.get("status") != "rejected"
            ):
                try:
                    created = datetime.strptime(existing["created_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=MYT)
                except ValueError:
                    created = cutoff
                if created >= cutoff:
                    return existing, ["Duplikat dihantar dalam 10 minit — rekod sedia ada dikekalkan."]

    row["status"] = "verified" if auto_verify else "pending"
    if auto_verify:
        rev = (reviewer or payload.get("pelapor_id") or "HQ").strip()
        row["reviewer"] = rev
        row["reviewed_at"] = now_iso()
        row["reviewer_note"] = str(payload.get("reviewer_note") or "Auto-verify batch upload")
    rows.append(row)
    write_submissions(state, rows)
    rebuild_hub(state)
    return row, []


def bulk_import(
    state: str,
    items: List[dict],
    *,
    uploader: str,
    auto_verify: bool = True,
    default_tarikh: str = "",
) -> dict:
    """Import many rows — default auto_verify (upload = sudah disemak HQ)."""
    if len(uploader.strip()) < 2:
        return {"ok": False, "error": "ID uploader HQ/PDM wajib.", "imported": 0, "errors": []}

    fallback_tarikh = norm_date(default_tarikh) or now_myt().strftime("%Y-%m-%d")
    imported = 0
    errors: List[str] = []
    for item in items:
        tarikh = norm_date(item.get("tarikh_lawatan")) or fallback_tarikh
        payload = {
            **item,
            "tarikh_lawatan": tarikh,
            "pelapor_id": str(item.get("pelapor_id") or uploader).strip(),
            "jenis_aktiviti": item.get("jenis_aktiviti") or "door_to_door",
            "reviewer_note": f"Batch upload by {uploader}",
        }
        row, row_errors = add_submission(
            state, payload, auto_verify=auto_verify, reviewer=uploader
        )
        line = item.get("_line")
        prefix = f"Baris {line}: " if line else ""
        if row_errors:
            errors.append(prefix + "; ".join(row_errors))
        else:
            imported += 1
    hub = rebuild_hub(state)
    return {
        "ok": len(errors) == 0 or imported > 0,
        "imported": imported,
        "errors": errors,
        "hub_summary": hub.get("summary"),
    }


def review_submission(
    state: str,
    submission_id: str,
    status: str,
    reviewer: str,
    note: str = "",
) -> Tuple[Optional[dict], Optional[str]]:
    status = status.lower()
    if status not in {"verified", "rejected", "pending"}:
        return None, "Status semakan tidak sah."
    if len(reviewer.strip()) < 2:
        return None, "Nama/code reviewer PDM wajib."

    rows = read_submissions(state)
    found = None
    for row in rows:
        if row.get("id") == submission_id:
            row["status"] = status
            row["reviewer"] = reviewer.strip()
            row["reviewed_at"] = now_iso()
            row["reviewer_note"] = (note or "").strip()[:500]
            found = row
            break
    if not found:
        return None, "Rekod tidak dijumpai."
    write_submissions(state, rows)
    rebuild_hub(state)
    return found, None


def load_n9_baseline() -> Dict[str, dict]:
    if not N9_DPI.exists():
        return {}
    data = json.loads(N9_DPI.read_text(encoding="utf-8"))
    return data.get("byCode") or {}


def rebuild_hub(state: str) -> dict:
    catalog = load_dun_catalog(state)
    rows = read_submissions(state)
    baseline = load_n9_baseline() if state == "N9" else {}

    now = now_myt()
    cut_24h = now - timedelta(hours=24)

    by_dun: Dict[str, dict] = {}
    for code, name in catalog.items():
        base = baseline.get(code, {})
        by_dun[code] = {
            "name": name,
            "verified_delta_total": 0,
            "verified_delta_24h": 0,
            "pending_count": 0,
            "rejected_count": 0,
            "rumah_dilawati_total": 0,
            "breakdown": {"bulan": 0, "condong": 0, "atas_pagar": 0, "dacing": 0},
            "baseline_cula_pas_total": base.get("culaPasTotal"),
            "baseline_cula_pct": base.get("culaPct"),
            "registered_voters_dpi": base.get("registeredVotersDpi"),
            "skt51": base.get("skt51"),
            "last_verified_at": None,
        }

    summary = {
        "verified_delta_total": 0,
        "verified_delta_24h": 0,
        "pending_count": 0,
        "rejected_count": 0,
        "submission_count": len(rows),
    }

    for row in rows:
        code = norm_dun_code(row.get("kod_dun"))
        if not code:
            continue
        if code not in by_dun:
            by_dun[code] = {
                "name": row.get("dun_name") or code,
                "verified_delta_total": 0,
                "verified_delta_24h": 0,
                "pending_count": 0,
                "rejected_count": 0,
                "rumah_dilawati_total": 0,
                "breakdown": {"bulan": 0, "condong": 0, "atas_pagar": 0, "dacing": 0},
                "baseline_cula_pas_total": None,
                "baseline_cula_pct": None,
                "registered_voters_dpi": None,
                "skt51": None,
                "last_verified_at": None,
            }

        st = (row.get("status") or "pending").lower()
        cula = _int(row.get("cula_baharu"))
        slot = by_dun[code]

        if st == "pending":
            slot["pending_count"] += 1
            summary["pending_count"] += 1
        elif st == "rejected":
            slot["rejected_count"] += 1
            summary["rejected_count"] += 1
        elif st == "verified":
            slot["verified_delta_total"] += cula
            slot["rumah_dilawati_total"] += _int(row.get("rumah_dilawati"))
            slot["breakdown"]["bulan"] += _int(row.get("cula_bulan"))
            slot["breakdown"]["condong"] += _int(row.get("cula_condong"))
            slot["breakdown"]["atas_pagar"] += _int(row.get("cula_atas_pagar"))
            slot["breakdown"]["dacing"] += _int(row.get("cula_dacing"))
            summary["verified_delta_total"] += cula

            reviewed = row.get("reviewed_at") or row.get("created_at") or ""
            try:
                rv = datetime.strptime(reviewed, "%Y-%m-%d %H:%M:%S").replace(tzinfo=MYT)
            except ValueError:
                rv = None
            if rv and rv >= cut_24h:
                slot["verified_delta_24h"] += cula
                summary["verified_delta_24h"] += cula
            if reviewed and (not slot["last_verified_at"] or reviewed > slot["last_verified_at"]):
                slot["last_verified_at"] = reviewed

    # Derived metrics
    for code, slot in by_dun.items():
        base_total = slot.get("baseline_cula_pas_total")
        digital_total = slot["verified_delta_total"]
        if base_total is not None:
            slot["digital_cula_total"] = int(base_total) + digital_total
            dpi = slot.get("registered_voters_dpi")
            if dpi and dpi > 0:
                slot["digital_cula_pct"] = round(slot["digital_cula_total"] / dpi * 100, 2)
            skt = slot.get("skt51")
            if skt is not None:
                slot["bkc_cula"] = slot["digital_cula_total"] - int(skt)
        else:
            slot["digital_cula_total"] = digital_total
            slot["digital_cula_pct"] = None
            slot["bkc_cula"] = None

    hub = {
        "meta": {
            "state": state,
            "generated": now_iso(),
            "dun_count": len(catalog) or len(by_dun),
            "submission_count": len(rows),
        },
        "summary": summary,
        "byDun": dict(sorted(by_dun.items(), key=lambda x: x[0])),
    }

    out = hub_path(state)
    out.write_text(json.dumps(hub, ensure_ascii=False, indent=2), encoding="utf-8")
    proto = prototype_hub_path(state)
    proto.write_text(json.dumps(hub, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        from cula_action_bridge import sync_cula_actions

        sync_cula_actions(state, hub, rows)
    except Exception as exc:
        print(f"[cula_action_bridge] {state}: {exc}", file=__import__("sys").stderr)

    return hub


def init_all_states() -> None:
    for st in STATES:
        csv_path(st)
        rebuild_hub(st)


if __name__ == "__main__":
    init_all_states()
    print(f"Initialized digital cula storage under {CULA_ROOT}")
