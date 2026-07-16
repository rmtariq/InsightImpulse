#!/usr/bin/env python3
"""Pull BNM (+ best-effort DOSM) macro data for PRN Negeri Sembilan dashboard."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
OUT = reference("N9") / "economic_n9.json"

BNM_BASE = "https://api.bnm.gov.my/public"
BNM_HEADERS = {"Accept": "application/vnd.BNM.API.v1+json"}


def _get(url: str, timeout: int = 25) -> Optional[Any]:
    try:
        r = requests.get(url, headers=BNM_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc), "url": url}


def _usd_rate(exchange_payload: dict) -> Optional[dict]:
    rows = exchange_payload.get("data") or []
    for row in rows:
        if row.get("currency_code") == "USD":
            rate = row.get("rate") or {}
            return {
                "date": rate.get("date"),
                "buying": rate.get("buying_rate"),
                "selling": rate.get("selling_rate"),
                "middle": rate.get("middle_rate"),
            }
    return None


def pull_bnm() -> dict:
    opr = _get(f"{BNM_BASE}/opr")
    fx = _get(f"{BNM_BASE}/exchange-rate")
    usd = _usd_rate(fx) if isinstance(fx, dict) else None
    return {
        "opr": opr,
        "exchange_rate_usd": usd,
        "exchange_rate_raw_meta": (fx or {}).get("meta") if isinstance(fx, dict) else None,
    }


def pull_dosm_placeholder() -> dict:
    """
    OpenDOSM CPI N9 — no stable public JSON without catalogue scrape.
    Record intent + manual refresh note for analysts.
    """
    return {
        "status": "manual_or_pending",
        "catalogue": "https://open.dosm.gov.my/data-catalogue/cpi_state",
        "note": "CPI negeri perlu pull dari OpenDOSM dashboard atau API data.gov.my — belum auto-parse.",
        "n9_label": "Negeri Sembilan",
        "last_manual_check": None,
    }


def build_payload() -> dict:
    bnm = pull_bnm()
    opr_level = None
    opr_date = None
    if isinstance(bnm.get("opr"), dict):
        d = bnm["opr"].get("data") or {}
        opr_level = d.get("new_opr_level")
        opr_date = d.get("date")

    usd = bnm.get("exchange_rate_usd") or {}
    headlines = []
    if opr_level is not None:
        headlines.append(f"OPR Malaysia kekal {opr_level}% (BNM, {opr_date or '—'})")
    if usd.get("middle"):
        headlines.append(f"Ringgit vs USD ~RM{usd['middle']:.4f} ({usd.get('date', '—')})")

    return {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source_files": ["EconomicOutlook_api_endpoints_master.numbers"],
        "bnm": bnm,
        "dosm": pull_dosm_placeholder(),
        "macro_headlines": headlines,
        "prn_relevance": {
            "opr": "Impak ansuran pinjaman SME & pembiayaan kereta/rumah — isu bandar NS.",
            "ringgit": "Kos import & harga barang — naratif kos sara hidup pengundi atas pagar.",
            "cpi_n9": "Pending — isu FELDA/LBN apabila data negeri dimasukkan.",
        },
        "official": {
            "opr_pct": opr_level,
            "opr_date": opr_date,
            "usd_myr": usd.get("middle"),
            "usd_date": usd.get("date"),
        },
    }


def main() -> int:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    o = payload.get("official", {})
    print(f"Written: {OUT}")
    print(f"OPR: {o.get('opr_pct')}% ({o.get('opr_date')}) | USD/MYR: {o.get('usd_myr')} ({o.get('usd_date')})")
    if payload["bnm"].get("opr", {}).get("error"):
        print("WARN: BNM OPR fetch issue — check network", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
