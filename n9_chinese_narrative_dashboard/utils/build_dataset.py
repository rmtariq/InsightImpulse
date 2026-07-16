"""Build combined 3-state dataset for the dashboard."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INSIGHT_ROOT = ROOT.parent
DATA_DIR = ROOT / "data"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.crawl_normalizer import latest_crawl_file, normalize_crawl_df, prefix_dun  # noqa: E402
from utils.data_cleaner import clean_posts  # noqa: E402
from utils.sample_data_generator import generate_posts, generate_posts_for_state  # noqa: E402

CRAWL_NEWS_DIRS = [
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_N9/crawls/chinese_news",
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_Johor/crawls/chinese_news",
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_Melaka/crawls/chinese_news",
]
CRAWL_NEWS_DIR = CRAWL_NEWS_DIRS[0]
CRAWL_MULTILINGUAL_DIR = INSIGHT_ROOT / "data/projects/political/PRN/PRN_N9/crawls/news"
CRAWL_INDIAN_DIRS = [
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_N9/crawls/indian_narrative",
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_Johor/crawls/indian_narrative",
    INSIGHT_ROOT / "data/projects/political/PRN/PRN_Melaka/crawls/indian_narrative",
]
CRAWL_INDIAN_DIR = CRAWL_INDIAN_DIRS[0]
CRAWL_SOCIAL_DIRS = {
    "Negeri Sembilan": INSIGHT_ROOT / "data/projects/political/PRN/PRN_N9/crawls/social",
    "Johor": INSIGHT_ROOT / "data/projects/political/PRN/PRN_Johor/crawls/social",
    "Melaka": INSIGHT_ROOT / "data/projects/political/PRN/PRN_Melaka/crawls/social",
}
# Harakat / PAS-BN response issue crawls (Jul 2026) — merge into narrative dataset
HARAKAT_CRAWL_DIR = INSIGHT_ROOT / "data/projects/political/Cina_Narative_2026/crawls"

OUTPUT = DATA_DIR / "prn_chinese_narrative_posts_3negeri.csv"
OUTPUT_LEGACY = DATA_DIR / "n9_chinese_narrative_posts.csv"

def _load_state_keywords() -> tuple[str, ...]:
    try:
        sys.path.insert(0, str(INSIGHT_ROOT / "scripts"))
        from prn_indian_seeds_loader import state_keywords_for_filter  # noqa: WPS433

        return state_keywords_for_filter()
    except Exception:
        return (
            "negeri sembilan", "seremban", "nilai", "bahau", "port dickson", "tampin",
            "kuala pilah", "jelebu", "rembau", "jempol", "森美兰", "芙蓉", "马口", "波德申",
            "johor", "melaka", "skudai", "batu pahat", "muar", "kluang",
        )


STATE_KEYWORDS = _load_state_keywords()
OFF_TOPIC_ONLY = (
    "sarawak", "kuching", "sabah", "kota kinabalu", "pasir mas", "kelantan",
    "kota bharu", "mindanao", "beckham", "paris:", "london:",
)
TAMIL_MEDIA_DOMAINS = (
    "makkalosai", "nanban", "malaysiannanban", "makkal", "varnam", "vanakkam",
    "tamilmalar", "astroulagam",
)


def _load_india_query_ids() -> set[str]:
    try:
        sys.path.insert(0, str(INSIGHT_ROOT / "scripts"))
        from prn_indian_news_queries import query_ids  # noqa: WPS433

        ids = query_ids()
        ids.update({"IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "IN8"})
        return ids
    except Exception:
        return {"IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "IN8"}


INDIA_QUERY_IDS = _load_india_query_ids()


def _keyword_in_text(keyword: str, text: str) -> bool:
    """Avoid false positives e.g. 'nilai' inside 'bernilai' / 'nilai bidaan'."""
    kw = keyword.lower()
    if kw == "nilai":
        if "bernilai" in text:
            return False
        if re.search(r"\bnilai\s+(bidaan|jualan|pemakanan|pasaran|wang|aset)\b", text, re.I):
            return False
        return bool(re.search(r"\bnilai\b", text, re.I))
    if len(kw) <= 5:
        return bool(re.search(rf"\b{re.escape(kw)}\b", text, re.I))
    return kw in text


def _text_lower(row_or_text) -> str:
    if isinstance(row_or_text, str):
        return row_or_text.lower()
    text = str(row_or_text.get("Text") or row_or_text.get("post_text") or "")
    return text.lower()


def _is_prn_relevant(text: str, community: str = "") -> bool:
    t = text.lower()
    if not t.strip():
        return False
    state_hit = any(_keyword_in_text(k, t) for k in STATE_KEYWORDS)
    off_topic = any(_keyword_in_text(k, t) for k in OFF_TOPIC_ONLY)
    if off_topic and not state_hit:
        return False
    if community == "india":
        if re.search(r"[\u0B80-\u0BFF]", t):
            return True
        india_hit = any(
            _keyword_in_text(k, t) if len(k) <= 5 else k in t
            for k in (
                "indian", "tamil", "hindu", "komuniti india", "pengundi india",
                "maicci", "malaysia nanban", "makkal osai",
            )
        ) or re.search(r"\bmic\b", t, re.I)
        return state_hit or india_hit
    return True


def _filter_india_posts(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    if "Type" in df.columns:
        df = df[df["Type"].astype(str).str.lower() == "post"]
    if "Community" in df.columns:
        df = df[df["Community"].astype(str).str.lower() == "india"]
    elif "community" in df.columns:
        df = df[df["community"].astype(str).str.lower() == "india"]
    else:
        return pd.DataFrame()

    keep = []
    for _, row in df.iterrows():
        text = _text_lower(row)
        raw_text = str(row.get("Text") or row.get("post_text") or "")
        qid = str(row.get("QueryID") or row.get("query_id") or "")
        domain = str(row.get("PublisherDomain") or row.get("URL") or "").lower()
        sid = str(row.get("SourceID") or "").upper()
        pipeline = str(row.get("CrawlPipeline") or "").lower()
        is_tamil_media = any(d in domain or d in sid.lower() for d in TAMIL_MEDIA_DOMAINS)
        if pipeline == "indian_narrative":
            keep.append(row)
            continue
        if is_tamil_media and (
            re.search(r"[\u0B80-\u0BFF]", raw_text)
            or _is_prn_relevant(text, "india")
        ):
            keep.append(row)
            continue
        if qid in INDIA_QUERY_IDS or any(d in domain for d in TAMIL_MEDIA_DOMAINS):
            if _is_prn_relevant(text, "india"):
                keep.append(row)
                continue
        if _is_prn_relevant(text, "india"):
            keep.append(row)
    return pd.DataFrame(keep) if keep else pd.DataFrame()


def _load_existing_sample() -> pd.DataFrame:
    sample = DATA_DIR / "sample_n9_chinese_narrative_posts.csv"
    if sample.exists():
        df = pd.read_csv(sample, low_memory=False)
        if "state" not in df.columns:
            df["state"] = "Negeri Sembilan"
        if "dun_code" in df.columns:
            df["dun_code"] = df["dun_code"].apply(lambda d: prefix_dun(str(d), "Negeri Sembilan"))
        return df
    return generate_posts(180)


def _recent_crawl_files(directory: Path, pattern: str = "*.csv", max_age_hours: int = 72) -> list[Path]:
    """All crawl CSVs from the last N hours (newest first), for daily incremental merges."""
    if not directory.exists():
        return []
    cutoff = pd.Timestamp.now().timestamp() - max_age_hours * 3600
    files = [p for p in directory.glob(pattern) if p.stat().st_mtime >= cutoff]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _merge_crawl_files(files: list[Path], default_state: str = "") -> pd.DataFrame:
    if not files:
        return pd.DataFrame()
    parts = []
    seen_ids: set[str] = set()
    for f in files:
        raw = pd.read_csv(f, low_memory=False)
        norm = normalize_crawl_df(raw, default_state=default_state)
        if norm.empty:
            continue
        keep = []
        for _, row in norm.iterrows():
            rid = str(row.get("post_id") or row.get("url") or "")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            keep.append(row)
        if keep:
            parts.append(pd.DataFrame(keep))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _load_crawl_news() -> pd.DataFrame:
    parts = []
    for directory in CRAWL_NEWS_DIRS:
        files = _recent_crawl_files(directory, "PRN_Chinese_News_all_*.csv")
        if not files:
            files = _recent_crawl_files(directory, "PRN_Chinese_News_*.csv")
        if not files:
            f = latest_crawl_file(directory, "PRN_Chinese_News_*.csv")
            files = [f] if f else []
        merged = _merge_crawl_files(files)
        if not merged.empty:
            parts.append(merged)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _merge_india_crawl_files(files: list[Path]) -> pd.DataFrame:
    if not files:
        return pd.DataFrame()
    parts = []
    seen_ids: set[str] = set()
    for path in files[:5]:
        raw = pd.read_csv(path, low_memory=False)
        india_raw = _filter_india_posts(raw)
        if india_raw.empty:
            continue
        norm = normalize_crawl_df(india_raw, default_state="Negeri Sembilan")
        if norm.empty:
            continue
        keep = []
        for _, row in norm.iterrows():
            rid = str(row.get("post_id") or row.get("source_url") or "")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            keep.append(row)
        if keep:
            parts.append(pd.DataFrame(keep))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _load_crawl_india_news() -> pd.DataFrame:
    """Merge India/Tamil posts from dedicated + multilingual news crawls."""
    indian_files: list[Path] = []
    for directory in CRAWL_INDIAN_DIRS:
        files = _recent_crawl_files(directory, "PRN_Indian_Narrative_*.csv", max_age_hours=720)
        if not files:
            f = latest_crawl_file(directory, "PRN_Indian_Narrative_*.csv")
            if f:
                files = [f]
        indian_files.extend(files)

    multi_files = _recent_crawl_files(
        CRAWL_MULTILINGUAL_DIR, "PRN_N9_News_Multilingual_*.csv", max_age_hours=720,
    )
    if not multi_files:
        f = latest_crawl_file(CRAWL_MULTILINGUAL_DIR, "PRN_N9_News_Multilingual_*.csv")
        multi_files = [f] if f else []

    parts = [
        _merge_india_crawl_files(indian_files),
        _merge_india_crawl_files(multi_files),
    ]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame()

    combined = pd.concat(parts, ignore_index=True)
    seen: set[str] = set()
    keep = []
    for _, row in combined.iterrows():
        rid = str(row.get("post_id") or row.get("source_url") or "")
        if rid and rid in seen:
            continue
        if rid:
            seen.add(rid)
        keep.append(row)
    return pd.DataFrame(keep) if keep else pd.DataFrame()


def _load_crawl_social() -> pd.DataFrame:
    parts = []
    for state, directory in CRAWL_SOCIAL_DIRS.items():
        files = _recent_crawl_files(directory, "PRN_Chinese_*.csv")
        if not files:
            files = _recent_crawl_files(directory, "*.csv")
        merged = _merge_crawl_files(files, default_state=state)
        if not merged.empty:
            parts.append(merged)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _load_harakat_issue_crawls() -> pd.DataFrame:
    """Merge Cina_Narative_2026 crawls (Harakat/PAS-BN issue, Jul 2026)."""
    if not HARAKAT_CRAWL_DIR.exists():
        return pd.DataFrame()
    files = sorted(HARAKAT_CRAWL_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return pd.DataFrame()
    merged = _merge_crawl_files(files)
    if merged.empty:
        return merged
    merged["crawl_pipeline"] = "harakat_issue_20260705"
    merged["issue_cluster"] = merged.get("issue_cluster", pd.Series(dtype=str)).fillna("Harakat/PAS-BN")
    return merged


def _ensure_state_samples() -> pd.DataFrame:
    """Johor/Melaka sample posts when socmed crawl not yet available."""
    parts = []
    for state, n in [("Johor", 80), ("Melaka", 60)]:
        path = DATA_DIR / f"sample_{state.lower().replace(' ', '_')}_chinese_narrative_posts.csv"
        if path.exists():
            parts.append(pd.read_csv(path, low_memory=False))
        else:
            df = generate_posts_for_state(state, n)
            df.to_csv(path, index=False)
            parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def build_dataset() -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    frames = [
        _load_existing_sample(),
        _load_crawl_news(),
        _load_crawl_india_news(),
        _load_crawl_social(),
        _load_harakat_issue_crawls(),
        _ensure_state_samples(),
    ]
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    cleaned = clean_posts(combined)
    cleaned.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    # Legacy single-file alias for N9-only workflows
    cleaned.to_csv(OUTPUT_LEGACY, index=False, encoding="utf-8-sig")
    return cleaned


if __name__ == "__main__":
    df = build_dataset()
    print(f"✅ {OUTPUT} — {len(df):,} rows")
    if "state" in df.columns:
        print(df["state"].value_counts().to_string())
    from utils.community import add_community_column
    tagged = add_community_column(df)
    if "community" in tagged.columns:
        print("\nKomuniti:")
        print(tagged["community"].value_counts().to_string())
