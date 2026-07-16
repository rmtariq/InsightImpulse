#!/usr/bin/env python3
"""
Build War Room Modul #6 JSON from live Chinese + Indian narrative crawls.

Reads:
  n9_chinese_narrative_dashboard/data/prn_chinese_narrative_posts_3negeri.csv
  (optional fallback) PRN_N9/crawls/indian_narrative/*.csv

Output:
  data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_narrative_community.json

Usage:
  python3 scripts/build_warroom_narrative_json.py
  python3 scripts/build_warroom_narrative_json.py --rebuild-dataset
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "n9_chinese_narrative_dashboard"
CHINESE_CSV = DASH / "data/prn_chinese_narrative_posts_3negeri.csv"
INDIAN_DIR = ROOT / "data/projects/political/PRN/PRN_N9/crawls/indian_narrative"
OUT_JSON = (
    ROOT
    / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_narrative_community.json"
)
OUT_JOHOR_JSON = ROOT / "data/projects/political/PRN/PRN_Johor/reference/johor_narrative_warroom.json"
OUT_JOHOR_WARROOM = (
    ROOT
    / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/johor_narrative_community.json"
)

MYT = timezone(timedelta(hours=8))

STATE_CFG = {
    "Negeri Sembilan": {"key": "N9", "label": "Negeri Sembilan", "dun": 36},
    "Johor": {"key": "Johor", "label": "Johor", "dun": 56},
    "Melaka": {"key": "Melaka", "label": "Melaka", "dun": 28},
}

DEFAULT_RESPONSES = {
    "N9": {
        "chinese": {
            "bm": "Kerajaan Negeri Sembilan komited memperkukuh perkhidmatan dan memastikan polisi sara hidup kekal mampu milik.",
            "zh": "森州政府致力于改善民生与营商环境，我们将与社区代表直接对话。",
        },
        "indian": {
            "bm": "Kerajaan Negeri Sembilan sedang pantau isu komuniti India/Tamil dan komited memastikan keperluan pendidikan serta ekonomi dipenuhi.",
            "ta": "நெகரி செம்பிலான் அரசு SJKT மற்றும் வேலைவாய்ப்பு குறித்து கவனம் செலுத்தி வருகிறது.",
        },
    },
    "Johor": {
        "chinese": {"bm": "Kerajaan Johor komited menyokong perniagaan kecil.", "zh": "柔佛州政府支持小贩与中小企业。"},
        "indian": {"bm": "Isu pekerjaan dan komuniti India dipantau rapat.", "ta": "வேலைவாய்ப்பு பிரச்சினைகள் கண்காணிக்கப்படுகின்றன."},
    },
    "Melaka": {
        "chinese": {"bm": "Melaka komited memacu pelancongan dan SME.", "zh": "马六甲致力于推动旅游与中小企业发展。"},
        "indian": {"bm": "Isu komuniti dipantau dengan sensitiviti.", "ta": "சமூக விவகாரங்கள் கவனத்துடன் கண்காணிக்கப்படுகின்றன."},
    },
}


def _py() -> None:
    if str(DASH) not in sys.path:
        sys.path.insert(0, str(DASH))
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))


def _is_chinese_row(row: pd.Series) -> bool:
    if str(row.get("crawl_community") or "").lower() == "india":
        return False
    _py()
    from utils.community import infer_community  # noqa: WPS433

    if infer_community(row) == "indian":
        return False
    if infer_community(row) == "chinese":
        return True
    lang = str(row.get("language_detected") or "")
    if lang.startswith("zh"):
        return True
    text = str(row.get("post_text") or row.get("translated_text_bm") or "")
    if re.search(r"[\u4e00-\u9fff]", text):
        return True
    jenis = str(row.get("jenis_suara") or "").lower()
    if jenis in ("media_chinese", "proxy_about_chinese", "seat_bandar", "party_official"):
        return True
    plat = str(row.get("platform") or "").lower()
    if "chinese" in plat:
        return True
    qid = str(row.get("query_id") or row.get("QueryID") or "").upper()
    if re.match(r"^S[123X]", qid):
        return True
    return False


def _is_indian_row(row: pd.Series) -> bool:
    return str(row.get("crawl_community") or "").lower() == "india"


def _parse_date(val: Any) -> Optional[datetime]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        ts = pd.to_datetime(val, utc=True, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:
        return None


def _sent_bucket(sent: str) -> str:
    s = str(sent or "").lower()
    if s in ("negative", "neg", "negatif"):
        return "neg"
    if s in ("positive", "pos", "positif"):
        return "pos"
    return "neu"


def _neg_pct(df: pd.DataFrame) -> int:
    if df.empty or "sentiment" not in df.columns:
        return 0
    return int(round((df["sentiment"].astype(str).str.lower() == "negative").mean() * 100))


def _delta_24h(df: pd.DataFrame) -> int:
    if df.empty or "published_at" not in df.columns:
        return 0
    now = datetime.now(MYT)
    cutoff = now - timedelta(hours=24)
    recent = 0
    for _, row in df.iterrows():
        dt = _parse_date(row.get("published_at"))
        if dt and dt.replace(tzinfo=MYT) >= cutoff:
            recent += 1
    return recent


def _top_issues(df: pd.DataFrame, limit: int = 4) -> List[List[Any]]:
    _py()
    from utils.keyword_classifier import classify_issue  # noqa: WPS433

    if df.empty:
        return [["Other", 100]]
    clusters: Counter[str] = Counter()
    for _, row in df.iterrows():
        text = str(row.get("post_text") or "")
        ic = str(row.get("issue_cluster") or "").strip()
        clusters[classify_issue(text, ic)] += 1
    total = sum(clusters.values()) or 1
    top = clusters.most_common(limit)
    return [[name, int(round(count / total * 100))] for name, count in top]


def _top_issue_name(issues: List[List[Any]]) -> str:
    return str(issues[0][0]) if issues else "Other"


def _sample_posts(df: pd.DataFrame, limit: int = 3) -> List[Dict[str, str]]:
    if df.empty:
        return []
    work = df.copy()
    if "engagement_total" in work.columns:
        work = work.sort_values("engagement_total", ascending=False)
    elif "published_at" in work.columns:
        work = work.sort_values("published_at", ascending=False)
    out: List[Dict[str, str]] = []
    for _, row in work.head(limit).iterrows():
        text = str(row.get("post_text") or row.get("translated_text_bm") or "")[:280]
        if not text.strip():
            continue
        loc = str(row.get("constituency") or row.get("district") or row.get("state") or "")
        plat = str(row.get("platform") or row.get("account_name") or "media")
        eng = int(row.get("engagement_total") or 0)
        meta = " · ".join(x for x in [loc, plat, f"{eng} engagement" if eng else ""] if x)
        out.append({"text": text, "sent": _sent_bucket(str(row.get("sentiment") or "")), "meta": meta})
    return out


def _priority_band(score: float, neg_pct: float) -> str:
    if score >= 0.65 or neg_pct >= 55:
        return "p1"
    if score >= 0.4 or neg_pct >= 35:
        return "p2"
    return "p3"


def _build_actions(df: pd.DataFrame, comm: str, state_key: str, limit: int = 6) -> List[Dict[str, Any]]:
    _py()
    from utils.action_engine import build_action_candidates  # noqa: WPS433

    if df.empty:
        return []
    candidates = build_action_candidates(df)
    if candidates.empty:
        return []
    actions: List[Dict[str, Any]] = []
    for i, row in candidates.head(limit).iterrows():
        neg = float(row.get("negative_percentage") or 0)
        score = float(row.get("priority_score") or 0)
        p = _priority_band(score, neg)
        dun = str(row.get("dun") or row.get("location") or "").strip()
        plat = str(row.get("platform") or "media")
        ic = str(row.get("issue_cluster") or "Isu")
        act_id = f"ACT-{state_key[:2].upper()}{comm[0].upper()}-{i+1:03d}"
        title = f"{ic}" + (f" — {dun}" if dun else "")
        body = str(row.get("detected_narrative") or row.get("narrative_summary") or ic)
        due = "Hari ini" if p == "p1" else ("48 jam" if p == "p2" else "Monitor")
        meta = [
            dun or state_key,
            plat,
            f"Sentimen: {str(row.get('sentiment') or 'mixed').title()}",
            f"Due: {due}",
        ]
        actions.append({
            "id": act_id,
            "p": p,
            "comm": comm,
            "title": title[:120],
            "body": body[:300],
            "meta": meta,
            "team": str(row.get("responsible_team") or "Communications"),
            "response": str(row.get("recommended_action") or "Pantau dan sediakan penjelasan berasaskan fakta."),
        })
    return actions


def _load_posts(rebuild: bool) -> pd.DataFrame:
    if rebuild or not CHINESE_CSV.exists():
        print("🔨 Bina semula dataset gabungan Cina/India…")
        _py()
        from utils.build_dataset import build_dataset  # noqa: WPS433

        build_dataset()
    if not CHINESE_CSV.exists():
        raise SystemExit(f"Dataset tidak dijumpai: {CHINESE_CSV}\nJalankan crawl dahulu.")
    return pd.read_csv(CHINESE_CSV, low_memory=False)


def _latest_indian_csv() -> Optional[Path]:
    if not INDIAN_DIR.exists():
        return None
    files = sorted(INDIAN_DIR.glob("PRN_Indian_Narrative_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _build_dun_rows(df: pd.DataFrame, limit: int = 4) -> List[List[str]]:
    if df.empty or "dun_code" not in df.columns:
        return []
    rows_out: List[List[str]] = []
    grp = df[df["dun_code"].astype(str).str.len() > 2].copy()
    if grp.empty:
        return []
    counts = grp.groupby("dun_code").size().sort_values(ascending=False)
    for dun, _ in counts.head(limit).items():
        sub = grp[grp["dun_code"] == dun]
        loc = str(sub["constituency"].iloc[0] if "constituency" in sub.columns and len(sub) else dun)
        top_issue = str(sub["issue_cluster"].mode().iloc[0]) if "issue_cluster" in sub.columns and len(sub["issue_cluster"].mode()) else "—"
        sent = str(sub["sentiment"].mode().iloc[0]) if "sentiment" in sub.columns and len(sub["sentiment"].mode()) else "Mixed"
        sent_label = {"negative": "Negatif", "positive": "Positif", "neutral": "Neutral"}.get(sent.lower(), sent.title())
        rows_out.append([str(dun), loc[:24], "Pantau", top_issue[:28], sent_label])
    return rows_out


def _state_bundle(state_name: str, chinese: pd.DataFrame, indian: pd.DataFrame) -> Dict[str, Any]:
    cfg = STATE_CFG[state_name]
    key = cfg["key"]
    neg_ch = _neg_pct(chinese)
    neg_in = _neg_pct(indian)
    issues_ch = _top_issues(chinese)
    issues_in = _top_issues(indian)
    actions = _build_actions(chinese, "chinese", key, 4) + _build_actions(indian, "indian", key, 4)
    actions.sort(key=lambda a: {"p1": 0, "p2": 1, "p3": 2}[a["p"]])
    return {
        "label": cfg["label"],
        "dun": cfg["dun"],
        "chinese": {
            "posts": len(chinese),
            "neg": neg_ch,
            "topIssue": _top_issue_name(issues_ch),
            "delta": str(_delta_24h(chinese)),
        },
        "indian": {
            "posts": len(indian),
            "neg": neg_in,
            "topIssue": _top_issue_name(issues_in),
            "delta": str(_delta_24h(indian)),
        },
        "issues": {"chinese": issues_ch, "indian": issues_in},
        "actions": actions[:8],
        "samples": {
            "chinese": _sample_posts(chinese),
            "indian": _sample_posts(indian),
        },
        "responses": DEFAULT_RESPONSES.get(key, DEFAULT_RESPONSES["N9"]),
        "dunRows": _build_dun_rows(pd.concat([chinese, indian], ignore_index=True) if not chinese.empty or not indian.empty else pd.DataFrame()),
    }


def build(rebuild_dataset: bool = False) -> Dict[str, Any]:
    df = _load_posts(rebuild_dataset)
    indian_csv = _latest_indian_csv()
    payload: Dict[str, Any] = {
        "meta": {
            "mode": "live",
            "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "source_csv": str(CHINESE_CSV.relative_to(ROOT)),
            "indian_crawl": str(indian_csv.relative_to(ROOT)) if indian_csv else None,
            "total_rows": len(df),
        }
    }
    for state_name in STATE_CFG:
        sub = df[df["state"].astype(str) == state_name] if "state" in df.columns else pd.DataFrame()
        chinese = sub[sub.apply(_is_chinese_row, axis=1)] if not sub.empty else pd.DataFrame()
        indian = sub[sub.apply(_is_indian_row, axis=1)] if not sub.empty else pd.DataFrame()
        key = STATE_CFG[state_name]["key"]
        payload[key] = _state_bundle(state_name, chinese, indian)
        print(
            f"  {key}: Cina {len(chinese)} · India {len(indian)} · "
            f"P1 {sum(1 for a in payload[key]['actions'] if a['p']=='p1')}"
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build War Room narrative JSON (Modul #6)")
    parser.add_argument("--rebuild-dataset", action="store_true", help="Rebuild combined CSV before export")
    args = parser.parse_args()

    print("📊 War Room narrative export…")
    payload = build(rebuild_dataset=args.rebuild_dataset)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if payload.get("Johor"):
        johor_only = {"meta": {**payload["meta"], "state_focus": "Johor"}, "Johor": payload["Johor"]}
        OUT_JOHOR_WARROOM.write_text(json.dumps(johor_only, ensure_ascii=False, indent=2), encoding="utf-8")
        OUT_JOHOR_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JOHOR_JSON.write_text(json.dumps(johor_only, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {OUT_JSON} ({OUT_JSON.stat().st_size // 1024} KB)")
    if OUT_JOHOR_WARROOM.exists():
        print(f"✅ {OUT_JOHOR_WARROOM} (Johor Modul #6)")
        print(f"✅ {OUT_JOHOR_JSON} (PRN_Johor reference)")
    print("   Refresh War Room Modul #6: Cmd+Shift+R")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
