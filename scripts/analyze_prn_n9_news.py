#!/usr/bin/env python3
"""PRN N9 — Smart Analyze Tier A: sentiment + emotion on direct scrape + komen (bukan 710 penuh)."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from prn_paths import crawls, reference, ensure_state_dirs  # noqa: E402

ensure_state_dirs("N9")
PROJECT = reference("N9").parent
CRAWL_DIR = crawls("N9", "news")
ANALYZED_DIR = crawls("N9", "news_analyzed")
SUMMARY_JSON = reference("N9") / "prn_n9_news_analyzed_summary.json"
COMMUNITY_LABELS = {
    "umum": "Umum / PRN",
    "melayu": "Komuniti Melayu",
    "islam": "Islam / PAS / Harakah",
    "cina": "Komuniti Cina",
    "india": "Komuniti India / Tamil",
    "lain": "Lain-lain",
    "ekonomi": "Ekonomi & Kos Hidup",
}

_NEG_KW = re.compile(
    r"goyah|risiko|krisis|pecah|split|khianat|bantah|protest|gagal|skandal|"
    r"负面|危机|批评|争议|susah|marah|bantah|negative|worst|crisis|turun",
    re.I,
)
_POS_KW = re.compile(
    r"menang|jaya|stabil|positif|成功|支持|harmoni|baik|untung|growth|"
    r"positive|strong|support|menyokong",
    re.I,
)


_HF_CACHE = Path.home() / ".cache/huggingface/hub"
_HF_MODEL_DIRS = (
    "models--rmtariq--ft-Malay-bert",
    "models--rmtariq--multilingual-emotion-classifier",
    "models--cardiffnlp--twitter-roberta-base-sentiment-latest",
    "models--uer--roberta-base-finetuned-chinanews-chinese",
    "models--nlptown--bert-base-multilingual-uncased-sentiment",
)


def _prepare_ml_environment() -> None:
    """Buang proxy Apify/sandbox; load HF token; offline jika model sudah cache."""
    for key in (
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
        "APIFY_PROXY_URL", "SCRAPLING_PROXY_URL",
    ):
        os.environ.pop(key, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)
        except ImportError:
            pass
    # Pastikan proxy tidak dipulihkan selepas load_dotenv
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(key, None)

    if _HF_CACHE.exists() and all((_HF_CACHE / d).exists() for d in _HF_MODEL_DIRS):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        print("   📦 Model cache tempatan — HF offline mode")


def apply_keyword_sentiment_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """Fallback bila model HF gagal load — keyword heuristic + narrative flags tetap jalan."""
    for col in ("Sentiment", "sentiment_label", "emotion_primary", "detected_language", "demographic", "analysis_mode"):
        if col not in df.columns:
            df[col] = ""
        else:
            # Kolum sedia ada boleh jadi float64 (semua NaN) — paksa object supaya
            # penetapan label string tidak ditolak oleh pandas 2.x.
            df[col] = df[col].astype("object")
    for idx, row in df.iterrows():
        text = str(row.get("Text", ""))
        t = text.lower()
        if _NEG_KW.search(text):
            label, score = "negative", 0.25
        elif _POS_KW.search(text):
            label, score = "positive", 0.85
        else:
            label, score = "neutral", 0.5
        df.at[idx, "sentiment_label"] = label
        df.at[idx, "Sentiment"] = label
        df.at[idx, "sentiment_score"] = score
        df.at[idx, "sentiment_confidence"] = 0.55
        df.at[idx, "emotion_primary"] = "concern" if label == "negative" else ("joy" if label == "positive" else "neutral")
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            df.at[idx, "detected_language"] = "zh-cn"
            df.at[idx, "demographic"] = "Chinese"
        elif _NEG_KW.search(t) or _POS_KW.search(t):
            df.at[idx, "detected_language"] = "ms"
            df.at[idx, "demographic"] = "Malay"
        else:
            df.at[idx, "detected_language"] = "en"
            df.at[idx, "demographic"] = "Unknown"
    df["analysis_mode"] = "keyword_fallback"
    return df


def add_geo_narrative(df: pd.DataFrame) -> pd.DataFrame:
    t = df["Text"].fillna("").astype(str).str.lower()
    df["geo_ns"] = t.str.contains(
        r"negeri sembilan|\bns\b|aminuddin|seremban|森美兰|森州|芙蓉",
        regex=True,
        na=False,
    )
    df["narrative_solo"] = t.str.contains(
        r"pas solo|pas bergerak solo|gerak solo|plot sd", regex=True, na=False
    )
    df["narrative_split"] = t.str.contains(
        r"putus|berpisah|perpecahan|retak|khianat|pecah|split|hentikan kerjasama",
        regex=True,
        na=False,
    )
    return df


def run_ml_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Cuba model HF; fallback keyword jika gagal."""
    _prepare_ml_environment()
    sys.path.insert(0, str(ROOT / "web_backend"))
    try:
        import asyncio
        from analyze_exco_master_sentiment import analyze_missing  # noqa: WPS433
        from web_backend.simple_app import initialize_models  # noqa: WPS433
        from web_backend import simple_app  # noqa: WPS433

        asyncio.run(initialize_models())
        if simple_app.sentiment_pipelines:
            out = analyze_missing(df.copy())
            out["analysis_mode"] = "ml_models"
            return out
    except Exception as exc:
        print(f"⚠️  Model HF gagal ({exc}) — guna keyword fallback")
    return apply_keyword_sentiment_fallback(df.copy())


def find_latest_crawl() -> Optional[Path]:
    files = sorted(CRAWL_DIR.glob("PRN_N9_News_Multilingual_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def select_tier_a(df: pd.DataFrame, max_rows: int = 120) -> pd.DataFrame:
    """Tier A: direct scrape posts + all reader comments."""
    if df.empty:
        return df

    chunks: List[pd.DataFrame] = []
    if "Type" in df.columns:
        comments = df[df["Type"].fillna("").astype(str).str.lower() == "comment"]
        if not comments.empty:
            chunks.append(comments)

    if "CrawlMethod" in df.columns and "Type" in df.columns:
        direct = df[
            (df["CrawlMethod"] == "direct_scrape")
            & (df["Type"].fillna("").astype(str).str.lower() == "post")
        ]
        if not direct.empty:
            chunks.append(direct)

    if not chunks:
        return pd.DataFrame()

    out = pd.concat(chunks, ignore_index=True)
    if "URL" in out.columns:
        out = out.sort_values("Date", ascending=False) if "Date" in out.columns else out
        out = out.drop_duplicates(subset=["URL"], keep="first")
    if "ID" in out.columns:
        out = out.drop_duplicates(subset=["ID"], keep="first")
    return out.head(max_rows).copy()


def _sentiment_breakdown(sub: pd.DataFrame) -> dict:
    if sub.empty:
        return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "neg_pct": 0.0}
    col = "sentiment_label" if "sentiment_label" in sub.columns else "Sentiment"
    if col not in sub.columns:
        return {"total": len(sub), "positive": 0, "neutral": len(sub), "negative": 0, "neg_pct": 0.0}
    vc = sub[col].fillna("").astype(str).str.lower()
    pos = int(vc.str.contains("pos").sum())
    neg = int(vc.str.contains("neg").sum())
    neu = int(vc.str.contains("neut").sum())
    if pos + neg + neu == 0:
        neu = len(sub)
    total = len(sub)
    return {
        "total": total,
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "neg_pct": round(neg / total * 100, 1) if total else 0.0,
    }


def _top_items(sub: pd.DataFrame, sentiment: str, limit: int = 5) -> List[dict]:
    if sub.empty:
        return []
    col = "sentiment_label" if "sentiment_label" in sub.columns else "Sentiment"
    if col not in sub.columns:
        return []
    mask = sub[col].fillna("").astype(str).str.lower().str.contains(sentiment[:3])
    rows = sub[mask].head(limit)
    out = []
    for _, r in rows.iterrows():
        out.append({
            "text": str(r.get("Text", ""))[:200],
            "url": str(r.get("URL", "")),
            "community": str(r.get("Community", "")),
            "type": str(r.get("Type", "post")),
            "sentiment": str(r.get(col, "")),
            "emotion": str(r.get("emotion_primary", "")),
            "domain": str(r.get("PublisherDomain", "")),
        })
    return out


def build_summary(analyzed: pd.DataFrame, source_csv: Path, out_csv: Path, skipped: int) -> dict:
    posts = analyzed[analyzed["Type"].str.lower() == "post"] if "Type" in analyzed.columns else analyzed
    comments = analyzed[analyzed["Type"].str.lower() == "comment"] if "Type" in analyzed.columns else pd.DataFrame()

    by_community: Dict[str, Any] = {}
    if "Community" in analyzed.columns:
        for comm in analyzed["Community"].dropna().unique():
            sub = posts[posts["Community"] == comm] if not posts.empty else pd.DataFrame()
            tone = _sentiment_breakdown(sub)
            emo = ""
            if not sub.empty and "emotion_primary" in sub.columns:
                emo = str(sub["emotion_primary"].mode().iloc[0]) if len(sub["emotion_primary"].mode()) else ""
            by_community[str(comm)] = {
                "label": COMMUNITY_LABELS.get(str(comm), str(comm)),
                "posts": int(len(sub)),
                "neg_pct": tone["neg_pct"],
                "top_emotion": emo,
            }

    narrative_alerts: List[dict] = []
    if "narrative_split" in analyzed.columns and analyzed["narrative_split"].any():
        n = int(analyzed["narrative_split"].sum())
        sample = analyzed[analyzed["narrative_split"]].iloc[0]["Text"] if n else ""
        narrative_alerts.append({
            "type": "narrative_split",
            "count": n,
            "severity": "warning" if n >= 3 else "watch",
            "sample": str(sample)[:160],
            "message": f"Naratif split PAS/PN muncul dalam {n} artikel/komen media (Tier A)",
        })
    if "narrative_solo" in analyzed.columns and analyzed["narrative_solo"].any():
        n = int(analyzed["narrative_solo"].sum())
        sample = analyzed[analyzed["narrative_solo"]].iloc[0]["Text"] if n else ""
        narrative_alerts.append({
            "type": "narrative_solo",
            "count": n,
            "severity": "watch",
            "sample": str(sample)[:160],
            "message": f"Naratif PAS solo dalam {n} artikel/komen media",
        })

    t = analyzed["Text"].fillna("").astype(str).str.lower()
    palace = t.str.contains(r"undang|palace|宫廷|institution|sultan", regex=True, na=False)
    if palace.any():
        n = int(palace.sum())
        narrative_alerts.append({
            "type": "palace_institution",
            "count": n,
            "severity": "warning" if n >= 2 else "watch",
            "sample": str(analyzed[palace].iloc[0]["Text"])[:160],
            "message": f"Isu istana/institusi dalam {n} item media — pantau naratif",
        })

    return {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "tier": "A",
        "layer": "media_and_comments",
        "layer_note": "Media Tone (artikel) + Public Voice (komen) — berasingan dari socmed master",
        "source_csv": str(source_csv.relative_to(ROOT)),
        "analyzed_csv": str(out_csv.relative_to(ROOT)),
        "rows_analyzed": len(analyzed),
        "rows_skipped": skipped,
        "posts_analyzed": len(posts),
        "comments_analyzed": len(comments),
        "media_tone": _sentiment_breakdown(posts),
        "public_voice": _sentiment_breakdown(comments),
        "by_community": by_community,
        "narrative_alerts": narrative_alerts,
        "top_negative": _top_items(analyzed, "negative", 5),
        "top_positive": _top_items(analyzed, "positive", 5),
        "analysis_mode": str(analyzed["analysis_mode"].iloc[0]) if "analysis_mode" in analyzed.columns and not analyzed.empty else "unknown",
    }


def run_analyze(csv_path: Optional[Path] = None, max_rows: int = 120, keyword_only: bool = False) -> dict:
    source = csv_path or find_latest_crawl()
    if not source or not source.exists():
        print("⚠️  Tiada crawl CSV — jalankan crawl_prn_n9_news_multilingual.py dahulu")
        return {}

    print(f"📥 Crawl: {source.name} ({source.stat().st_size // 1024} KB)")
    df = pd.read_csv(source, low_memory=False)
    tier = select_tier_a(df, max_rows=max_rows)
    skipped = len(df) - len(tier)
    print(f"🎯 Tier A: {len(tier)} baris (skip {skipped} Google News bulk)")

    if tier.empty:
        print("⚠️  Tier A kosong — tiada direct scrape / komen")
        return {}

    if keyword_only:
        tier = apply_keyword_sentiment_fallback(tier)
    else:
        tier = run_ml_sentiment(tier)
    tier = add_geo_narrative(tier)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ANALYZED_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = ANALYZED_DIR / f"PRN_N9_News_Analyzed_TierA_{ts}.csv"
    tier.to_csv(out_csv, index=False, encoding="utf-8-sig")

    summary = build_summary(tier, source, out_csv, skipped)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    posts = tier[tier["Type"].str.lower() == "post"] if "Type" in tier.columns else tier
    print(f"💾 Analyzed: {out_csv.name}")
    print(f"   Media tone: {_sentiment_breakdown(posts)}")
    if summary.get("narrative_alerts"):
        for a in summary["narrative_alerts"]:
            print(f"   ⚠️  {a['message']}")
    print(f"   Summary: {SUMMARY_JSON.relative_to(ROOT)}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Smart Analyze Tier A for PRN N9 news")
    parser.add_argument("--csv", type=Path, default=None, help="Crawl CSV path (default: latest)")
    parser.add_argument("--max-rows", type=int, default=120)
    parser.add_argument("--keyword-only", action="store_true", help="Skip HF models; keyword fallback only")
    args = parser.parse_args()

    if args.keyword_only:
        print("🏷️  Keyword-only mode (no HF models)")
        summary = run_analyze(args.csv, max_rows=args.max_rows, keyword_only=True)
        return 0 if summary else 1

    print("🤖 Loading sentiment + emotion models (local cache)...")
    _prepare_ml_environment()
    summary = run_analyze(args.csv, max_rows=args.max_rows)
    return 0 if summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
