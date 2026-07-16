#!/usr/bin/env python3
"""Load PRN Chinese Narrative keyword streams from Excel / JSON / built-in pack."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data/projects/political/pas_break_2026/reference"
DEFAULT_JSON = REF / "PRN_Chinese_Narrative_keywords.json"
DEFAULT_XLSX_CANDIDATES = [
    Path("/Users/rmtariq/Downloads/PRN_ChineseNarrative_Keywords_2026.xlsx"),
    REF / "PRN_Chinese_Narrative_NS_Melaka_Johor.xlsx",
    REF / "PRN_ChineseNarrative_Keywords_2026.xlsx",
]

STATE_BY_PREFIX = {
    "S1": "Negeri Sembilan",
    "S2": "Johor",
    "S3": "Melaka",
    "SX": "Semua",
}


@dataclass
class KeywordStream:
    stream_id: str
    label: str
    negeri: str
    platforms: List[str]
    jenis: str
    prioriti: str
    query: str

    def state_key(self) -> str:
        if self.negeri == "Johor":
            return "Johor"
        if self.negeri == "Melaka":
            return "Melaka"
        if self.negeri in ("Semua", "3 Negeri (Cross)"):
            return "N9"
        return "N9"


def _parse_platforms(raw: str) -> List[str]:
    mapping = {
        "news": "news",
        "facebook": "facebook",
        "fb": "facebook",
        "x": "x",
        "twitter": "x",
        "instagram": "instagram",
        "tiktok": "tiktok",
    }
    out: List[str] = []
    for part in re.split(r"[,/|]+", str(raw or "").lower()):
        p = part.strip()
        if p in mapping and mapping[p] not in out:
            out.append(mapping[p])
    return out or ["news"]


def _builtin_streams() -> List[KeywordStream]:
    """Fallback — same 17 streams as Excel KEYWORD MASTER."""
    rows = [
        ("S1A1", "Media Cina NS", "Negeri Sembilan", "news", "media_chinese", "Tinggi",
         '"Sin Chew" OR "China Press" OR "星洲日报" OR "中国报" Negeri Sembilan OR 森美兰 when:30d'),
        ("S1A2", "Proxy BM NS", "Negeri Sembilan", "news", "proxy_about_chinese", "Rendah",
         '"pengundi Cina" OR "komuniti Cina" "Negeri Sembilan" PRN when:30d'),
        ("S1B1", "DAP/PH NS", "Negeri Sembilan", "news,facebook", "party_official", "Tinggi",
         'DAP OR "Pakatan Harapan" "Negeri Sembilan" PRN when:30d'),
        ("S1B2", "Bandar NS (Seremban/Nilai)", "Negeri Sembilan", "news,facebook,x", "seat_bandar", "Tinggi",
         'Seremban OR Nilai calon OR PRN "Negeri Sembilan" when:30d'),
        ("S1B3", "MCA/BN NS", "Negeri Sembilan", "news,facebook", "party_official", "Sederhana",
         'MCA OR "Barisan Nasional" "Negeri Sembilan" PRN when:30d'),
        ("S2A1", "Media Cina Johor", "Johor", "news", "media_chinese", "Tinggi",
         '"Sin Chew" OR "China Press" OR "星洲日报" OR "中国报" Johor OR 柔佛 when:30d'),
        ("S2A2", "Proxy BM Johor", "Johor", "news", "proxy_about_chinese", "Rendah",
         '"pengundi Cina" OR "komuniti Cina" "Johor" PRN when:30d'),
        ("S2B1", "DAP/PH Johor", "Johor", "news,facebook", "party_official", "Tinggi",
         'DAP OR "Pakatan Harapan" "Johor" PRN when:30d'),
        ("S2B2", "Bandar Johor (JB/Skudai/Stulang)", "Johor", "news,facebook,x", "seat_bandar", "Tinggi",
         'Johor Bahru OR Skudai OR Stulang calon OR PRN "Johor" when:30d'),
        ("S2B3", "MCA/BN Johor", "Johor", "news,facebook", "party_official", "Sederhana",
         'MCA OR "Barisan Nasional" "Johor" PRN when:30d'),
        ("S3A1", "Media Cina Melaka", "Melaka", "news", "media_chinese", "Tinggi",
         '"Sin Chew" OR "China Press" OR "星洲日报" OR "中国报" Melaka OR 马六甲 when:30d'),
        ("S3A2", "Proxy BM Melaka", "Melaka", "news", "proxy_about_chinese", "Rendah",
         '"pengundi Cina" OR "komuniti Cina" "Melaka" PRN when:30d'),
        ("S3B1", "DAP/PH Melaka", "Melaka", "news,facebook", "party_official", "Tinggi",
         'DAP OR "Pakatan Harapan" "Melaka" PRN when:30d'),
        ("S3B2", "Bandar Melaka (Bandar Hilir)", "Melaka", "news,facebook,x", "seat_bandar", "Tinggi",
         'Melaka OR "Bandar Hilir" calon OR PRN "Melaka" when:30d'),
        ("S3B3", "MCA/BN Melaka", "Melaka", "news,facebook", "party_official", "Sederhana",
         'MCA OR "Barisan Nasional" "Melaka" PRN when:30d'),
        ("SX1", "Media Cina — 3 Negeri", "Semua", "news", "media_chinese", "Tinggi",
         '"Sin Chew" OR "China Press" ("Negeri Sembilan" OR Johor OR Melaka) PRN when:30d'),
        ("SX2", "Pengundi Cina — 3 Negeri", "Semua", "news,facebook", "proxy_about_chinese", "Rendah",
         '"pengundi Cina" ("Negeri Sembilan" OR Johor OR Melaka) when:30d'),
    ]
    return [
        KeywordStream(sid, label, negeri, _parse_platforms(plat), jenis, pri, q)
        for sid, label, negeri, plat, jenis, pri, q in rows
    ]


def _load_from_excel(path: Path) -> List[KeywordStream]:
    xl = pd.ExcelFile(path)
    sheet = "KEYWORD MASTER" if "KEYWORD MASTER" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    streams: List[KeywordStream] = []
    for _, row in df.iterrows():
        sid = str(row.iloc[1] if len(row) > 1 else "").strip()
        if not re.match(r"^S[123X]", sid):
            continue
        label = str(row.iloc[2] if len(row) > 2 else sid).strip()
        negeri = str(row.iloc[3] if len(row) > 3 else "").strip()
        plat_raw = str(row.iloc[4] if len(row) > 4 else "news").strip()
        jenis = str(row.iloc[5] if len(row) > 5 else "").strip()
        prioriti = str(row.iloc[6] if len(row) > 6 else "Tinggi").strip()
        query = str(row.iloc[7] if len(row) > 7 else "").strip()
        if not query or query.lower() == "query string":
            continue
        streams.append(KeywordStream(
            stream_id=sid,
            label=label,
            negeri=negeri or STATE_BY_PREFIX.get(sid[:2], "Semua"),
            platforms=_parse_platforms(plat_raw),
            jenis=jenis,
            prioriti=prioriti,
            query=query,
        ))
    if not streams:
        for name in ("NS", "Johor", "Melaka"):
            if name not in xl.sheet_names:
                continue
            sub = pd.read_excel(path, sheet_name=name, header=None)
            for _, row in sub.iterrows():
                sid = str(row.iloc[1] if len(row) > 1 else "").strip()
                if not re.match(r"^S[123X]", sid):
                    continue
                streams.append(KeywordStream(
                    stream_id=sid,
                    label=str(row.iloc[2] if len(row) > 2 else sid).strip(),
                    negeri=name if name != "NS" else "Negeri Sembilan",
                    platforms=_parse_platforms(str(row.iloc[3] if len(row) > 3 else "news")),
                    jenis=str(row.iloc[4] if len(row) > 4 else "").strip(),
                    prioriti=str(row.iloc[5] if len(row) > 5 else "Tinggi").strip(),
                    query=str(row.iloc[6] if len(row) > 6 else "").strip(),
                ))
    return streams


def _load_from_json(path: Path) -> List[KeywordStream]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [KeywordStream(**item) for item in data.get("streams", [])]


def resolve_excel_path(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.exists() else None
    env = __import__("os").environ.get("PRN_CHINESE_KEYWORDS_XLSX")
    if env and Path(env).exists():
        return Path(env)
    for p in DEFAULT_XLSX_CANDIDATES:
        if p.exists():
            return p
    return None


def load_streams(
    excel_path: Optional[str] = None,
    prefer_json: bool = False,
) -> tuple[List[KeywordStream], str]:
    """Return (streams, source_label). Excel wins unless prefer_json and JSON is newer."""
    xlsx = resolve_excel_path(excel_path)
    if xlsx and not prefer_json:
        streams = _load_from_excel(xlsx)
        if streams:
            sync_json(streams, source=str(xlsx))
            return streams, str(xlsx)
    if DEFAULT_JSON.exists():
        streams = _load_from_json(DEFAULT_JSON)
        if streams:
            return streams, str(DEFAULT_JSON)
    if xlsx:
        streams = _load_from_excel(xlsx)
        if streams:
            sync_json(streams, source=str(xlsx))
            return streams, str(xlsx)
    streams = _builtin_streams()
    sync_json(streams, source="builtin")
    return streams, "builtin"


def sync_json(streams: List[KeywordStream], source: str = "") -> Path:
    REF.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "streams": [asdict(s) for s in streams],
    }
    DEFAULT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return DEFAULT_JSON


# Daily batch groups — ANDA pilih bila run (bukan auto-schedule)
DAILY_SLOTS = {
    "morning": {
        "label": "Pagi — Bandar + Media Cina",
        "stream_ids": ["S2B2", "S3B2", "S1B2", "S2A1", "S3A1", "S1A1"],
        "prioriti": None,
    },
    "midday": {
        "label": "Tengah hari — Parti (DAP/PH + MCA/BN)",
        "stream_ids": ["S2B1", "S3B1", "S1B1", "S2B3", "S3B3", "S1B3"],
        "prioriti": None,
    },
    "evening": {
        "label": "Petang — Proxy + Cross-state + rebuild",
        "stream_ids": ["S2A2", "S3A2", "S1A2", "SX1", "SX2"],
        "prioriti": None,
    },
    "tinggi": {
        "label": "Semua prioriti Tinggi",
        "stream_ids": None,
        "prioriti": "Tinggi",
    },
    "full": {
        "label": "Semua 17 stream",
        "stream_ids": None,
        "prioriti": None,
    },
}


def filter_streams(
    streams: List[KeywordStream],
    slot: str = "full",
    stream_ids: Optional[List[str]] = None,
    prioriti: Optional[str] = None,
    negeri: Optional[str] = None,
) -> List[KeywordStream]:
    cfg = DAILY_SLOTS.get(slot, DAILY_SLOTS["full"])
    ids = stream_ids or cfg.get("stream_ids")
    pri = prioriti or cfg.get("prioriti")
    out = streams
    if ids:
        id_set = set(ids)
        out = [s for s in out if s.stream_id in id_set]
    if pri:
        out = [s for s in out if s.prioriti.lower() == pri.lower()]
    if negeri:
        key = negeri.lower()
        out = [s for s in out if s.negeri.lower().startswith(key) or s.negeri == "Semua"]
    return out
