#!/usr/bin/env python3
"""Parse SPR Helaian Mata (scoresheet) PRN 2023 N9 — 36 PDF per DUN.

Ekstrak:
  - Jumlah undi setiap calon (rasmi), majoriti, peratus keluar mengundi, undi rosak.
  - Pecahan ikut saluran/pusat mengundi + tag jenis kawasan
    (Melayu/Cina/Ladang-India/Pos-Awal) -> nampak stronghold & kebocoran PAS.

Output:
  - reports/seats/n9_scoresheet_2023.csv        (ringkasan per DUN)
  - reports/seats/n9_scoresheet_streams_2023.json (pecahan saluran + jenis kawasan)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import reports  # noqa: E402

PDF_DIR = ROOT / "JITP_2026/Master_File/Scoresheet PRU DUN15 (2023)"
OUT_CSV = reports("N9") / "seats/n9_scoresheet_2023.csv"
OUT_JSON = reports("N9") / "seats/n9_scoresheet_streams_2023.json"
PROD_JSON = reports("N9") / "war_room/prototype/data/warroom_dun_N9_production.json"

NUM = re.compile(r"^-?[\d,]+$")


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


def _classify(loc: str) -> str:
    u = loc.upper()
    if "UNDI POS" in u or "POS\n" in u or u.strip().startswith("UNDI POS"):
        return "Pos"
    if "UNDI AWAL" in u or "AWAL" in u:
        return "Awal"
    if "(TAMIL)" in u or "TAMIL" in u or "LADANG" in u or "ESTET" in u or "ESTATE" in u or "JKKT" in u:
        return "India/Ladang"
    if "(CINA)" in u or "SJKC" in u or ("JENIS KEBANGSAAN" in u and "CINA" in u):
        return "Cina"
    return "Melayu/Campuran"


def _load_known() -> dict:
    if not PROD_JSON.exists():
        return {}
    data = json.loads(PROD_JSON.read_text(encoding="utf-8"))
    seats = data if isinstance(data, list) else data.get("seats", data)
    out = {}
    if isinstance(seats, list):
        for s in seats:
            c = (s.get("code") or "").upper().replace(".", "")
            m = re.match(r"N0*(\d+)", c)
            if m:
                c = f"N{int(m.group(1)):02d}"
            out[c] = {
                "name": s.get("name"),
                "majority": s.get("majority2023") or s.get("majority"),
                "party2023": s.get("party2023"),
                "winner": s.get("incumbent") or s.get("winnerName"),
            }
    return out


def parse_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
    lines = [ln.strip() for ln in text.splitlines()]

    reg = None
    m = re.search(r"JUMLAH PEMILIH\s*:\s*([\d,]+)", text)
    if m:
        reg = _to_int(m.group(1))

    # Grand total line: "JUMLAH <saluran> <A> <c1..cn> <valid> <C> <D>"
    totals = None
    for ln in lines:
        mm = re.match(r"^JUMLAH\s+((?:[\d,]+\s+){5,}[\d,]+)\s*$", ln)
        if mm:
            nums = [_to_int(x) for x in mm.group(1).split()]
            totals = nums  # keep last (grand total at end)
    if not totals or len(totals) < 6:
        return {"file": path.name, "error": "no totals", "registered": reg}

    # nums = [saluran, A, cand1..candN, valid, C, D]
    saluran, A = totals[0], totals[1]
    tail_valid, tail_C, tail_D = totals[-3], totals[-2], totals[-1]
    cand_votes = totals[2:-3]
    nc = len(cand_votes)

    # candidate names block (first occurrence between UNDI (D) and JUMLAH UNDIAN)
    names_raw = ""
    mn = re.search(r"UNDI \(D\)\s*\n(.+?)\nJUMLAH UNDIAN", text, re.S)
    if mn:
        names_raw = " ".join(mn.group(1).split())

    # stream rows: pure-number lines with exactly nc+5 ints
    streams_by_type: dict[str, list[int]] = {}
    cur_loc_parts: list[str] = []
    want = nc + 5
    for ln in lines:
        toks = ln.split()
        if toks and all(NUM.match(t) for t in toks) and len(toks) == want:
            vals = [_to_int(t) for t in toks]
            cands = vals[2:2 + nc]
            loc = " ".join(cur_loc_parts[-6:])
            typ = _classify(loc)
            acc = streams_by_type.setdefault(typ, [0] * nc)
            for i in range(nc):
                acc[i] += cands[i]
        else:
            # accumulate textual context (location names)
            if ln and not re.match(r"^[\d,\s/]+$", ln):
                cur_loc_parts.append(ln)
            if "UNDI POS" in ln.upper() or "UNDI AWAL" in ln.upper():
                cur_loc_parts.append(ln)

    ranked = sorted(range(nc), key=lambda i: cand_votes[i], reverse=True)
    top1, top2 = ranked[0], (ranked[1] if nc > 1 else ranked[0])
    valid_total = sum(cand_votes)
    majority = cand_votes[top1] - (cand_votes[top2] if nc > 1 else 0)

    return {
        "file": path.name,
        "registered": reg,
        "ballotsA": A,
        "validTotal": valid_total,
        "rejected": tail_C,
        "candVotes": cand_votes,
        "numCands": nc,
        "namesRaw": names_raw,
        "winnerCol": top1,
        "runnerCol": top2,
        "winnerVotes": cand_votes[top1],
        "runnerVotes": cand_votes[top2] if nc > 1 else 0,
        "majority": majority,
        "turnoutPct": round(A / reg * 100, 1) if reg else None,
        "spoiltPct": round(tail_C / (valid_total + tail_C) * 100, 2) if valid_total else None,
        "streamsByType": {k: v for k, v in streams_by_type.items()},
    }


def main():
    known = _load_known()
    rows = []
    for pdf in sorted(PDF_DIR.glob("HelaianMata N.*.pdf")):
        m = re.search(r"N\.(\d+)", pdf.name)
        code = f"N{int(m.group(1)):02d}" if m else pdf.stem
        r = parse_pdf(pdf)
        r["code"] = code
        r["nameFromFile"] = pdf.name.split(maxsplit=1)[1].replace(".pdf", "")
        rows.append(r)

    print(f"{'DUN':5} {'Daftar':>7} {'Keluar%':>7} {'Calon':>5} "
          f"{'Menang':>7} {'Naib':>7} {'Maj(parse)':>10} {'Maj(data)':>9} {'OK':>3}")
    for r in sorted(rows, key=lambda x: x["code"]):
        if r.get("error"):
            print(f"{r['code']:5} ERROR: {r['error']}")
            continue
        k = known.get(r["code"], {})
        kmaj = k.get("majority")
        ok = "✓" if (kmaj and abs((kmaj or 0) - r["majority"]) <= max(3, int((kmaj or 1) * 0.02))) else "?"
        print(f"{r['code']:5} {r['registered'] or 0:>7,} {r['turnoutPct'] or 0:>7} "
              f"{r['numCands']:>5} {r['winnerVotes']:>7,} {r['runnerVotes']:>7,} "
              f"{r['majority']:>10,} {str(kmaj):>9} {ok:>3}")

    # write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "registered", "turnoutPct", "numCands",
                    "winnerVotes", "runnerVotes", "majority", "majorityPct",
                    "rejected", "spoiltPct", "candVotes", "namesRaw"])
        for r in sorted(rows, key=lambda x: x["code"]):
            if r.get("error"):
                continue
            vt = r["validTotal"] or 1
            w.writerow([
                r["code"], r["nameFromFile"], r["registered"], r["turnoutPct"],
                r["numCands"], r["winnerVotes"], r["runnerVotes"], r["majority"],
                round(r["majority"] / vt * 100, 1), r["rejected"], r["spoiltPct"],
                "|".join(str(x) for x in r["candVotes"]), r["namesRaw"],
            ])

    OUT_JSON.write_text(json.dumps(
        {r["code"]: r for r in sorted(rows, key=lambda x: x["code"])},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ CSV : {OUT_CSV}")
    print(f"✅ JSON: {OUT_JSON}")


if __name__ == "__main__":
    main()
