#!/usr/bin/env python3
"""RAG + optional LLM refresh for N9 7-bloc faction brief (dashboard + crawl).

Reads:  reference/n9_pn_faction_rag.json
        master crawl CSV (optional mention counts)
Writes: reports/war_room/prototype/data/n9_bloc_faction_brief.json

Usage:
  python scripts/update_n9_bloc_factions.py
  OPENAI_API_KEY=... python scripts/update_n9_bloc_factions.py --llm
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAG_PATH = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_pn_faction_rag.json"
OUT_PATH = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_bloc_faction_brief.json"
MASTER_GLOB = ROOT / "data/projects/political/pas_break_2026/master"

N9_PAT = re.compile(
    r"negeri sembilan|prn n9|prn negeri sembilan|dun n\d",
    re.I,
)


def _load_rag() -> dict[str, Any]:
    return json.loads(RAG_PATH.read_text(encoding="utf-8"))


def _crawl_mentions() -> dict[str, int]:
    """Light RAG retrieval from master crawl — mention counts N9-scoped."""
    counts = {
        "bersama_rafizi": 0,
        "bersatu_muhyiddin_azmin": 0,
        "team_pn_pejuang_wawasan": 0,
        "mn_muafakat": 0,
    }
    masters = sorted(MASTER_GLOB.glob("PAS_Break_Master*.csv"), key=lambda p: p.stat().st_mtime)
    if not masters:
        return counts
    try:
        import pandas as pd
    except ImportError:
        return counts
    df = pd.read_csv(masters[-1], low_memory=False, usecols=lambda c: c in ("Text",))
    if "Text" not in df.columns:
        return counts
    text = df["Text"].fillna("").astype(str).str.lower()
    n9 = text.str.contains(N9_PAT)

    def n9_count(pat: str) -> int:
        return int((text.str.contains(pat, regex=True, na=False) & n9).sum())

    counts["bersama_rafizi"] = n9_count(r"parti bersama|bersama rafizi|rafizi ramli")
    not_team = text.str.contains(r"mahathir|tun m\b|pejuang|wawasan|hamzah", regex=True, na=False)
    counts["bersatu_muhyiddin_azmin"] = int(
        (text.str.contains(r"\bbersatu\b|muhyiddin|azmin ali", regex=True, na=False) & ~not_team & n9).sum()
    )
    counts["team_pn_pejuang_wawasan"] = int(
        (
            text.str.contains(r"pejuang|wawasan|mahathir|mukhriz|hamzah", regex=True, na=False)
            & text.str.contains(r"pn|perikatan", regex=True, na=False)
            & n9
        ).sum()
    )
    counts["mn_muafakat"] = int(
        (text.str.contains(r"muafakat|pas umno|pas bn", regex=True, na=False) & n9).sum()
    )
    return counts


def _rule_brief(rag: dict[str, Any], mentions: dict[str, int]) -> dict[str, Any]:
    b7 = rag["blocs"]["7_bersatu_faction"]
    b4 = rag["blocs"]["4_team_pn"]
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "rag_rule_based",
        "executive_summary": (
            "Team PN (#4) = PAS + Pejuang (Mahathir penasihat) + Wawasan (Hamzah) + Gerakan/PRIM. "
            "Slider #7 hanya Bersatu (Muhyiddin · Azmin) — risiko solo pecah PN. "
            "Hamzah & Mahathir BUKAN dalam bucket #7."
        ),
        "bloc_labels": {
            "pas_solo": rag["blocs"]["1_pas_solo"]["label"],
            "umno_solo": rag["blocs"]["2_umno_bn_solo"]["label"],
            "mn": rag["blocs"]["3_mn"]["label"],
            "pn": b4["short_label"],
            "ph": rag["blocs"]["5_ph"]["label"],
            "bersama": rag["blocs"]["6_bersama"]["label"],
            "bersatu": b7["label"],
        },
        "team_pn_roster": [
            f"{c['party']}" + (f" ({', '.join(c.get('leaders', []))})" if c.get("leaders") else "")
            + (f" · {c['note']}" if c.get("note") else "")
            for c in b4["components"]
        ],
        "bersatu_faction": {
            "leaders": b7["leaders"],
            "not_included": b7["explicitly_not"],
            "operational_note": b7["split_risk"],
        },
        "slider_hints": {
            "bersamaPct": {
                "label": rag["blocs"]["6_bersama"]["label"],
                "default": rag["blocs"]["6_bersama"]["default_pct"],
                "crawl_posts_n9": mentions.get("bersama_rafizi", 0),
            },
            "bersatuPct": {
                "label": b7["label"],
                "default": b7["default_pct"],
                "crawl_posts_n9": mentions.get("bersatu_muhyiddin_azmin", 0),
            },
        },
        "crawl_mentions_n9": mentions,
        "war_room_actions": [
            "Crawl Batch 8: Batch A Bersama · Batch B Bersatu (Muhyiddin/Azmin, exclude Mahathir/Hamzah) · Batch C Team PN",
            "Brief lapangan: Hamzah=Wawasan=Team PN; Mahathir=Pejuang=Team PN; jangan kelirukan dengan slider #7",
            "Monitor kemelut PAS–Bersatu — naikkan slider #7 jika isyarat 3 penjuru kuat di socmed N9",
        ],
    }


def _llm_enhance(rag: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return base
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        ctx = json.dumps(
            {"rag_blocs": rag["blocs"], "mentions": base.get("crawl_mentions_n9"), "base": base["executive_summary"]},
            ensure_ascii=False,
        )[:8000]
        prompt = f"""Anda analis war room PRN Negeri Sembilan 2026 (PAS/PN lens).
RAG context JSON:
{ctx}

Kemaskini pemetaan faksi:
- Team PN: PAS, Pejuang+Mahathir, Wawasan+Hamzah, Gerakan — BUKAN pecah
- Slider pecah PN: Bersatu Muhyiddin/Azmin SAHAJA (bukan Hamzah, bukan Mahathir)

Hasilkan JSON sahaja dengan keys:
executive_summary (3 ayat BM),
team_pn_bullet (array 4 string — siapa dalam Team PN),
bersatu_risk_bullet (array 3 string — risiko Muhyiddin/Azmin solo),
n9_ops_note (2 ayat untuk petugas N9),
confidence_note (1 ayat — bukan polling).
BM formal, operasi sahaja."""

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=900,
        )
        text = resp.choices[0].message.content or ""
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            parsed = json.loads(m.group())
            base.update(parsed)
            base["source"] = "rag_llm"
            base["llm_model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    except Exception as exc:
        base["llm_error"] = str(exc)[:200]
    return base


def main() -> None:
    rag = _load_rag()
    mentions = _crawl_mentions()
    brief = _rule_brief(rag, mentions)
    if "--llm" in os.sys.argv or os.getenv("FORCE_LLM"):
        brief = _llm_enhance(rag, brief)
    brief["rag_version"] = rag["meta"]["updated"]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"  source={brief['source']}  mentions={mentions}")


if __name__ == "__main__":
    main()
