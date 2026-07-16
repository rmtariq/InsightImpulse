"""Text analysis: Jieba segmentation, word clouds, trending."""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

try:
    import jieba
    JIEBA_OK = True
except ImportError:
    JIEBA_OK = False

try:
    from wordcloud import WordCloud
    WC_OK = True
except ImportError:
    WC_OK = False

import matplotlib.pyplot as plt

ZH_STOP = set("的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这".split())
MS_STOP = set("yang dan di ke dari pada untuk dengan ada ini itu dia kita anda".split())
EN_STOP = set("the a an is are was were be been being in on at to for of and or but".split())


def _tokenize_chinese(texts: pd.Series) -> list[str]:
    words = []
    for t in texts.dropna().astype(str):
        if JIEBA_OK:
            for w in jieba.cut(t):
                w = w.strip()
                if len(w) >= 2 and w not in ZH_STOP and not w.isdigit():
                    words.append(w)
        else:
            for w in re.findall(r"[\u4e00-\u9fff]{2,}", t):
                if w not in ZH_STOP:
                    words.append(w)
    return words


def _tokenize_latin(texts: pd.Series, stop: set) -> list[str]:
    words = []
    for t in texts.dropna().astype(str):
        for w in re.findall(r"[a-zA-Z\u00C0-\u024F]{3,}", t.lower()):
            if w not in stop:
                words.append(w)
    return words


def top_keywords(df: pd.DataFrame, lang: str = "zh", n: int = 20) -> pd.DataFrame:
    if df.empty or "post_text" not in df.columns:
        return pd.DataFrame(columns=["keyword", "count"])
    texts = df["post_text"]
    if lang == "zh":
        words = _tokenize_chinese(texts)
    elif lang == "ms":
        sub = df[df["language_detected"].astype(str).str.startswith("ms", na=False)] if "language_detected" in df.columns else df
        words = _tokenize_latin(sub["post_text"], MS_STOP)
    else:
        sub = df[df["language_detected"].astype(str).str.startswith("en", na=False)] if "language_detected" in df.columns else df
        words = _tokenize_latin(sub["post_text"], EN_STOP)
    counts = Counter(words).most_common(n)
    return pd.DataFrame(counts, columns=["keyword", "count"])


def chinese_wordcloud_figure(df: pd.DataFrame):
    if df.empty or not WC_OK:
        return None
    zh = df[df["language_detected"].astype(str).str.startswith("zh", na=False)] if "language_detected" in df.columns else df
    text = " ".join(zh["post_text"].dropna().astype(str).tolist())
    if not text.strip():
        text = " ".join(df["post_text"].dropna().astype(str).tolist())
    if not text.strip():
        return None
    wc = WordCloud(width=800, height=400, background_color="white", font_path=None).generate(text)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig


def compute_trending_narratives(df: pd.DataFrame) -> pd.DataFrame:
    """Trending score per issue_cluster as narrative proxy."""
    if df.empty or "issue_cluster" not in df.columns:
        return pd.DataFrame()

    risk_weight = {"Low": 0.25, "Medium": 0.5, "High": 0.75, "Critical": 1.0}
    rows = []
    for issue, grp in df.groupby("issue_cluster"):
        mentions = len(grp)
        eng = grp["engagement_total"].sum() if "engagement_total" in grp.columns else 0
        first = grp["published_at"].min() if "published_at" in grp.columns else None
        latest = grp["published_at"].max() if "published_at" in grp.columns else None
        growth = 0.0
        if "published_at" in grp.columns and pd.notna(first) and pd.notna(latest):
            mid = first + (latest - first) / 2
            early = len(grp[grp["published_at"] < mid])
            late = len(grp[grp["published_at"] >= mid])
            growth = ((late - early) / max(early, 1)) * 100
        risk = grp["risk_level"].map(lambda x: risk_weight.get(str(x), 0.25)).mean() if "risk_level" in grp.columns else 0.25
        sent = grp["sentiment"].mode().iloc[0] if "sentiment" in grp.columns and len(grp) else "neutral"
        rows.append({
            "Naratif": issue,
            "mentions": mentions,
            "engagement": int(eng),
            "sentiment": sent,
            "first_detected": first,
            "latest_detected": latest,
            "growth_pct": round(growth, 1),
            "risk_weight": round(risk, 2),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    for col in ["mentions", "engagement", "growth_pct"]:
        mx = out[col].max() or 1
        out[f"n_{col}"] = out[col] / mx

    out["trending_score"] = (
        0.35 * out["n_mentions"]
        + 0.30 * out["n_engagement"]
        + 0.20 * out["n_growth_pct"].clip(lower=0)
        + 0.15 * out["risk_weight"]
    ).round(3)

    return out.sort_values("trending_score", ascending=False)


def compute_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed risk_score column."""
    if df.empty:
        return df
    out = df.copy()
    sens = (
        out.get("ethnic_sensitive_flag", False).astype(int)
        + out.get("religion_sensitive_flag", False).astype(int)
    ) / 2
    mis = out.get("misinformation_flag", False).astype(int)
    neg = (out.get("sentiment", pd.Series(dtype=str)).astype(str).str.lower() == "negative").astype(int)
    eng = out.get("engagement_total", pd.Series(0)).astype(float)
    eng_norm = eng / max(eng.max(), 1)

    if "published_at" in out.columns:
        daily = out.groupby(out["published_at"].dt.date).size()
        growth = daily.pct_change().fillna(0).mean() if len(daily) > 1 else 0
    else:
        growth = 0
    growth_norm = min(abs(growth), 1)

    out["risk_score"] = (
        0.25 * sens + 0.20 * mis + 0.20 * neg + 0.20 * eng_norm + 0.15 * growth_norm
    ).round(3)
    return out
