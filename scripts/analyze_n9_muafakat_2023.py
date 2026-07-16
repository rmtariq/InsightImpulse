#!/usr/bin/env python3
"""Analisis muafakat MN dari Helaian Mata PRN 2023 (data rasmi SPR).

Kira baseline sebenar PN/PAS + matematik muafakat (PN+BN vs PH) untuk 13 kerusi MN,
serta kebocoran ikut jenis kawasan (Melayu/Cina/India-Ladang).

Output: reports/seats/n9_mn13_muafakat_2023.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reports  # noqa: E402

STREAMS = reports("N9") / "seats/n9_scoresheet_streams_2023.json"
OUT_CSV = reports("N9") / "seats/n9_mn13_muafakat_2023.csv"

# Label parti ikut susunan candVotes (terkurasi dari nama calon + barisan 2023).
# P=PH(DAP/PKR/Amanah) · N=PN(PAS/Bersatu) · B=BN(UMNO/MCA) · X=kecil/bebas
MN13 = {
    "N25": {"name": "Paroi", "tier": "wajib", "hold": "PN", "cols": ["X", "B", "N"]},
    "N31": {"name": "Bagan Pinang", "tier": "wajib", "hold": "PN", "cols": ["N", "B"]},
    "N05": {"name": "Serting", "tier": "wajib", "hold": "PN", "cols": ["N", "B"]},
    "N20": {"name": "Labu", "tier": "wajib", "hold": "PN", "cols": ["N", "P"]},
    "N34": {"name": "Gemas", "tier": "wajib", "hold": "PN", "cols": ["N", "B"]},
    "N14": {"name": "Ampangan", "tier": "wajib", "hold": "PH", "cols": ["P", "N", "B"]},
    "N13": {"name": "Sikamat", "tier": "wajib", "hold": "PH", "cols": ["N", "P", "X", "X"]},
    "N18": {"name": "Pilah", "tier": "wajib", "hold": "PH", "cols": ["N", "P"]},
    "N04": {"name": "Klawang", "tier": "wajib", "hold": "PH", "cols": ["B", "N", "P"]},
    "N33": {"name": "Sri Tanjung", "tier": "berhasrat", "hold": "PH", "cols": ["N", "P"]},
    "N10": {"name": "Nilai", "tier": "berhasrat", "hold": "PH", "cols": ["N", "B", "X", "P"]},
    "N01": {"name": "Chennah", "tier": "berhasrat", "hold": "PH", "cols": ["N", "P"]},
    "N36": {"name": "Repah", "tier": "berhasrat", "hold": "PH", "cols": ["B", "P"]},
}


def main():
    data = json.loads(STREAMS.read_text(encoding="utf-8"))
    out_rows = []
    print(f"{'DUN':4} {'Nama':13} {'Tier':9} {'Pegang':6} "
          f"{'PH':>6} {'PN':>6} {'BN':>6} {'Muafakat':>9} {'vs PH':>7} {'Verdikt'}")
    print("-" * 96)
    for code, cfg in MN13.items():
        r = data[code]
        votes = r["candVotes"]
        cols = cfg["cols"]
        tally = {"P": 0, "N": 0, "B": 0, "X": 0}
        for v, c in zip(votes, cols):
            tally[c] += v
        ph, pn, bn = tally["P"], tally["N"], tally["B"]
        muafakat = pn + bn
        # gap muafakat vs PH (positif = bloc Melayu/muafakat menang)
        mvp = muafakat - ph
        winner_now = max(votes)
        runner_now = sorted(votes, reverse=True)[1] if len(votes) > 1 else 0
        margin_now = winner_now - runner_now

        # kebocoran ikut kawasan: undi PH di kawasan Cina + India/Ladang
        st = r.get("streamsByType", {})

        def area_split(area):
            arr = st.get(area)
            if not arr:
                return None
            t = {"P": 0, "N": 0, "B": 0, "X": 0}
            for v, c in zip(arr, cols):
                t[c] += v
            return t

        india = area_split("India/Ladang")
        cina = area_split("Cina")
        melayu = area_split("Melayu/Campuran")

        if cfg["hold"] == "PN":
            verdict = f"PERTAHAN (PAS/PN menang +{margin_now:,})"
        elif mvp > 1500:
            verdict = f"FLIP KUAT (muafakat +{mvp:,})"
        elif mvp > 0:
            verdict = f"FLIP RAPAT (muafakat +{mvp:,})"
        elif mvp > -1500:
            verdict = f"SUKAR (muafakat {mvp:,})"
        else:
            verdict = f"SANGAT SUKAR (muafakat {mvp:,})"

        print(f"{code:4} {cfg['name']:13} {cfg['tier']:9} {cfg['hold']:6} "
              f"{ph:>6,} {pn:>6,} {bn:>6,} {muafakat:>9,} {mvp:>+7,} {verdict}")

        out_rows.append({
            "code": code, "name": cfg["name"], "tier": cfg["tier"], "hold": cfg["hold"],
            "registered": r["registered"], "turnoutPct": r["turnoutPct"],
            "PH_2023": ph, "PN_2023": pn, "BN_2023": bn,
            "muafakat_PN_BN": muafakat, "muafakat_vs_PH": mvp,
            "margin_now": margin_now, "verdict": verdict,
            "melayu_PH": (melayu or {}).get("P"), "melayu_PN": (melayu or {}).get("N"),
            "melayu_BN": (melayu or {}).get("B"),
            "cina_PH": (cina or {}).get("P"), "cina_PN": (cina or {}).get("N"),
            "india_PH": (india or {}).get("P"), "india_PN": (india or {}).get("N"),
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"\n✅ CSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
