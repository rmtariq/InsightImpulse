#!/usr/bin/env python3
"""Sync Keputusan Hari Ini + ML Analytics — satu sumber kebenaran (n9_daily_ops.json)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_daily_ops.json"
ML_PATH = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_ml_predictions.json"
CULA_PATH = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/cula_poll_summary_N9.json"
BUNDLE_PATH = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_social_summary.json"
MYT = timezone(timedelta(hours=8))

# 20 kerusi sasaran MN (HQ) — selari kumpulan A/B/C/D dalam ML panel
MN20_CODES = [
    "N02", "N03", "N05", "N06", "N07", "N09", "N14", "N15", "N16", "N17",
    "N19", "N20", "N25", "N26", "N27", "N28", "N31", "N32", "N34", "N35",
]

GROUP_BM = {
    "defend": {"id": "A", "label": "JANGAN GAGAL", "effort": "Tinggi", "hari_ini": "Jentera penuh — jangan kurang staf"},
    "winnable": {"id": "B", "label": "PUSH MENANG", "effort": "Tinggi", "hari_ini": "Digital + ground — kejar undi"},
    "tough": {"id": "C", "label": "JUJUR & TIPIS", "effort": "Sederhana", "hari_ini": "Kempen minimum konsisten"},
    "not_priority": {"id": "D", "label": "MAINTAIN MN", "effort": "Rendah", "hari_ini": "WhatsApp + monitor sahaja"},
}


def _load(path: Path) -> Dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _pct_ml(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{round(float(v) * 100)}%"


def _plain_action(seat: Dict[str, Any]) -> str:
    code = seat.get("code", "")
    name = seat.get("name", "")
    g = GROUP_BM.get(seat.get("kategoriPas", ""), {})
    ml = _pct_ml(seat.get("ml_competitive_prob"))
    return (
        f"{code} {name}: {g.get('hari_ini', 'Pantau')} "
        f"(peluang ML {ml} · model PAS {seat.get('pasWinProb', '—')}%)"
    )


def build() -> Dict[str, Any]:
    ml = _load(ML_PATH)
    cula = _load(CULA_PATH)
    social = _load(BUNDLE_PATH)

    mn = cula.get("mnVsSolo", {})
    labu = cula.get("pasLabu", {})
    mn_exp = mn.get("bucketsExpanded", {})
    mn_clear = 68
    if mn_exp.get("MN") and mn_exp.get("Solo"):
        mn_clear = round(mn_exp["MN"] / (mn_exp["MN"] + mn_exp["Solo"]) * 100)

    coalition = (social.get("coalition") or [{}])[0]
    top_issue = (social.get("issues") or {}).get("top") or [{}]
    if isinstance(top_issue, list):
        top_issue = top_issue[0] if top_issue else {}

    seats_by_code = {s["code"]: s for s in ml.get("seat_predictions", []) if s.get("code")}
    mn_seats = [seats_by_code[c] for c in MN20_CODES if c in seats_by_code]

    groups: Dict[str, List[Dict[str, Any]]] = {k: [] for k in GROUP_BM}
    for s in mn_seats:
        kat = s.get("kategoriPas", "tough")
        if kat not in groups:
            kat = "tough"
        g = GROUP_BM[kat]
        groups[kat].append({
            "code": s["code"],
            "name": s.get("name", ""),
            "kumpulan": g["id"],
            "kumpulan_label": g["label"],
            "peluang_ml_pct": round((s.get("ml_competitive_prob") or 0) * 100),
            "model_pas_pct": s.get("pasWinProb"),
            "majoriti_2023": s.get("majority"),
            "hari_ini": g["hari_ini"],
            "tindakan_ringkas": _plain_action(s),
        })

    push_count = sum(len(groups[k]) for k in ("defend", "winnable", "tough"))
    maintain_count = len(groups["not_priority"])

    ml_actions = []
    for a in (ml.get("prescriptive_actions") or [])[:5]:
        entity = a.get("entity", "")
        seat = seats_by_code.get(entity, {})
        ml_actions.append({
            "rank": a.get("rank"),
            "urgency": a.get("urgency", "monitor"),
            "code": entity,
            "name": seat.get("name", ""),
            "title_bm": f"Hari ini: gerak jentera + digital ke {entity} {seat.get('name', '')}",
            "detail_bm": _plain_action(seat) if seat else a.get("detail", ""),
        })

    keputusan = {
        "headline": "MN kekal laluan utama",
        "ringkasan": (
            f"Data CULA + ML: kekalkan naratif MN (bukan debat solo). "
            f"MN jelas {mn_clear}% vs Solo · Pro-PAS {mn.get('pct', {}).get('Pro-PAS', '—')}% · "
            f"Labu sokong PAS {labu.get('pct', {}).get('Sokong PAS', '—')}%. "
            f"Model majoriti: {coalition.get('name', 'MN')} lead {coalition.get('pct', '—')}%."
        ),
        "mn_vs_solo_pct": mn_clear,
        "labu_sokong_pct": labu.get("pct", {}).get("Sokong PAS"),
        "coalition_lead": coalition.get("name"),
        "coalition_lead_pct": coalition.get("pct"),
    }

    tindakan_72jam = [
        {"kesukaran": "mudah", "label": "Mudah", "teks": "Semua admin FB: skrip sama — 'pilih MN (A), elak pecah undi, PH kalah'."},
        {"kesukaran": "mudah", "label": "Mudah", "teks": f"N20 Labu: gerak 'Labu for PAS' — sokongan digital {labu.get('pct', {}).get('Sokong PAS', '—')}%."},
        {"kesukaran": "sederhana", "label": "Sederhana", "teks": "N26/N27 Rembau: balas 30 komen Pro-PH dengan fakta tempatan."},
        {"kesukaran": "sukar", "label": "Sukar", "teks": f"Selaraskan MN dengan UMNO/BN — elak isu {top_issue.get('label', 'perpaduan')} pecah momentum."},
    ]

    # Top 3 ML = tambahan selari dengan Keputusan
    for ma in ml_actions[:3]:
        tindakan_72jam.insert(0, {
            "kesukaran": "segera",
            "label": "ML Segera",
            "teks": ma["title_bm"] + " — " + ma["detail_bm"],
        })

    fokus = []
    for code in ("N20", "N27", "N26", "N28", "N33"):
        s = seats_by_code.get(code, {})
        fokus.append({
            "code": code,
            "name": s.get("name", code),
            "sebab": {
                "N20": "Labu: sokongan PAS digital",
                "N27": "Rantau: kritik panas",
                "N26": "Chembong: balas kritik",
                "N28": "Kota: ulang poll",
                "N33": "PD: naikkan volume",
            }.get(code, "Pantau"),
            "peluang_ml_pct": round((s.get("ml_competitive_prob") or 0) * 100) if s else None,
        })

    return {
        "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "mn20_codes": MN20_CODES,
        "mn_majority": 19,
        "keputusan": keputusan,
        "kpi": {
            "sasaran_mn": len(MN20_CODES),
            "push_abc": push_count,
            "maintain_d": maintain_count,
            "formula": f"80% tenaga → {push_count} kerusi push · 20% → {maintain_count} maintain",
        },
        "kumpulan": {
            kat: {"meta": GROUP_BM[kat], "seats": groups[kat]}
            for kat in GROUP_BM
        },
        "tindakan_72jam": tindakan_72jam,
        "ml_actions_top5": ml_actions,
        "fokus_kawasan": fokus,
        "model_cv": {
            name: {
                "accuracy": stats.get("cv_accuracy_mean"),
                "f1": stats.get("cv_f1_mean"),
            }
            for name, stats in (ml.get("predictive", {}).get("models") or {}).items()
            if stats.get("cv_accuracy_mean") is not None
        },
        "disclaimer": "Satu fail untuk Command Center + ML panel — refresh selepas crawl & build_n9_ml_predictions.py",
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {OUT}")
    print(f"   Keputusan: {payload['keputusan']['headline']}")
    print(f"   MN20 push: {payload['kpi']['push_abc']} · maintain: {payload['kpi']['maintain_d']}")
    print(f"   Tindakan: {len(payload['tindakan_72jam'])} item (selari ML + CULA)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
