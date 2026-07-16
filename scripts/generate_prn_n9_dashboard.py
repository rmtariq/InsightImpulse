#!/usr/bin/env python3
"""Generate prn-negeri-sembilan-dashboard.html from master data files."""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
from n9_scenario_engine import scenario_engine_js
from n9_seat_analytics import build_analytics_summary, enrich_and_save
from n9_war_room import build_war_room_payload, save_war_room

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prn_paths import (  # noqa: E402
    PAS_BREAK,
    SHARED,
    crawls,
    reference,
    reports,
    resolve_existing,
)

WAR_ROOM_JS = ROOT / "scripts/n9_war_room_dashboard.js"

SEATS_JSON = resolve_existing(
    reports("N9") / "seats/n9_seats_export.json",
    ROOT / "data/projects/political/pas_break_2026/reports/n9_seats_export.json",
)
ANALYTICS_JSON = resolve_existing(
    reports("N9") / "seats/n9_seats_analytics.json",
    ROOT / "data/projects/political/pas_break_2026/reports/n9_seats_analytics.json",
)
EXCEL_SEATS = ROOT / "JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx"
PAS_DATA = resolve_existing(
    PAS_BREAK / "reports/pas_break_dashboard_data.json",
)
SME_MASTER = ROOT / "data/projects/sme/smebank/master/SMEBank_Master_20260609.csv"
ECONOMIC_JSON = resolve_existing(
    reference("N9") / "economic_n9.json",
    ROOT / "data/projects/political/pas_break_2026/reference/economic_n9.json",
)
NEWS_JSON = resolve_existing(
    reference("N9") / "prn_n9_news_summary.json",
    ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_news_summary.json",
)
NEWS_ANALYZED_JSON = resolve_existing(
    reference("N9") / "prn_n9_news_analyzed_summary.json",
    ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_news_analyzed_summary.json",
)
ADUN_SOCIAL_JSON = resolve_existing(
    reference("N9") / "prn_n9_adun_social_summary.json",
    ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_adun_social_summary.json",
)
PRN_DATES_JSON = resolve_existing(
    SHARED / "spr/spr_prn_dates_2026.json",
    ROOT / "data/projects/political/pas_break_2026/reference/spr_prn_dates_2026.json",
)
DPI_UPDATES_JSON = resolve_existing(
    reference("N9") / "n9_dpi_updates.json",
    ROOT / "data/projects/political/pas_break_2026/reference/n9_dpi_updates.json",
)
PAS_MASTER_DIR = PAS_BREAK / "master"
OUT = reports("N9") / "dashboards/prn-negeri-sembilan-dashboard.html"
OUT_COPY = ROOT / "JITP_2026/PAS_Break_2026/prn-negeri-sembilan-dashboard.html"
ML_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_ml_predictions.json"
NARRATIVE_INTEL_JSON = ROOT / "data/projects/political/Cina_Narative_2026/reports/cina_narrative_analytics.json"
CINA_META_JSON = ROOT / "data/projects/political/Cina_Narative_2026/metadata.json"

STRESS_PATTERN = (
    r"inflasi|kos naik|sara hidup|harga barang|harga naik|opr|hutang|pinjaman|"
    r"bisnes tutup|kedai tutup|gulung tikar|cashflow|modal habis|sewa naik|tarif|ringgit|ekonomi|gdp"
)
NS_PATTERN = r"negeri sembilan|n\.?\s*sembilan|prn.*sembilan|sembilan.*prn|dun sembilan|prn n9"
PRN_PATTERN = r"prn|pilihan raya negeri|state election|州选|negeri sembilan|johor|melaka|sembilan|\bdun\b"


def generate_volume_trend_30d():
    """Mock 30-day NS discussion volume for sentiment tab."""
    import random
    random.seed(42)
    base = 8
    out = []
    for day in range(30):
        d = datetime(2026, 5, 13).toordinal() + day
        dt = datetime.fromordinal(d)
        bump = 0
        if dt.day >= 5 and dt.month == 6:
            bump = (dt.day - 4) * 18
        if dt.day == 9 and dt.month == 6:
            bump += 40
        vol = max(5, base + bump + random.randint(-3, 8))
        out.append({"date": dt.strftime("%Y-%m-%d"), "volume": vol})
    out[-1]["volume"] = 222
    return out


PROFILE_EXTRAS = {
    "N05": {"tempatan": "Kawasan FELDA Serting — isu harga getah/komoditi, akses klinik.", "agamaIdentiti": "Komuniti Melayu kuat; institusi masjid pusat mobilisasi.", "fenceSitters": "Pengundi FELDA sensitif kos input vs subsidi."},
    "N25": {"tempatan": "Paroi — bandaraya Seremban; trafik, perumahan mampu milik.", "agamaIdentiti": "Campuran bandar; isu sekolah vernakular kurang dominan.", "fenceSitters": "Profesional muda — swing 6–10% boleh ubah majoriti PAS."},
    "N31": {"tempatan": "Bagan Pinang — pantai Port Dickson; pelancongan & nelayan.", "agamaIdentiti": "Melayu pantai; naratif perpaduan vs pembangunan.", "fenceSitters": "Pengundi ekonomi pelancongan post-COVID."},
    "N01": {"tempatan": "Palong/Chennah — bandar Seremban; kos hidup, parking, banjir.", "agamaIdentiti": "Bandar berbilang kaum; DAP stronghold.", "fenceSitters": "Pengundi Cina-India + Melayu bandar muda."},
    "N13": {"tempatan": "Sikamat — semi-urban; industrial ring Seremban.", "agamaIdentiti": "Melayu bandar; isu halal & pekerjaan kilang.", "fenceSitters": "Majoriti sempit 1,043 — setiap 500 undi kritikal."},
    "N21": {"tempatan": "Seremban Jaya — bandar raya; MRT/bas, kos sewa.", "agamaIdentiti": "Bandar cosmopolitan; isu identiti kurang dominan.", "fenceSitters": "Gen-Z TikTok — ekonomi & governance."},
    "N20": {"tempatan": "Labu — NILAI hi-tech; pekerja kilang & logistic hub.", "agamaIdentiti": "Melayu pekerja manufacturing dominan.", "fenceSitters": "Bersatu hold — risiko retak jentera PN."},
    "N34": {"tempatan": "Gemas — sempadan NS-Johor; FELDA & ladang.", "agamaIdentiti": "Melayu LBN; isu tanah FELDA & harga komoditi.", "fenceSitters": "Pengundi komuter Johor–NS."},
}


def load_data():
    if EXCEL_SEATS.exists():
        seats = enrich_and_save()
    elif SEATS_JSON.exists():
        seats = json.loads(SEATS_JSON.read_text(encoding="utf-8"))
        try:
            from n9_dpi_updates import apply_to_seats
            seats = apply_to_seats(seats)
        except Exception:
            pass
    else:
        raise FileNotFoundError("Tiada Excel atau n9_seats_export.json")
    pas = json.loads(PAS_DATA.read_text(encoding="utf-8"))
    analytics = build_analytics_summary(seats)
    return seats, pas, analytics


def load_official_economic() -> dict:
    if ECONOMIC_JSON.exists():
        return json.loads(ECONOMIC_JSON.read_text(encoding="utf-8"))
    return {}


def load_news_analyzed_summary() -> dict:
    if NEWS_ANALYZED_JSON.exists():
        return json.loads(NEWS_ANALYZED_JSON.read_text(encoding="utf-8"))
    return {}


def load_news_summary() -> dict:
    if NEWS_JSON.exists():
        return json.loads(NEWS_JSON.read_text(encoding="utf-8"))
    alt = resolve_existing(
        reference("N9") / "prn_n9_news_multilingual_summary.json",
        ROOT / "data/projects/political/pas_break_2026/reference/prn_n9_news_multilingual_summary.json",
    )
    if alt.exists():
        return json.loads(alt.read_text(encoding="utf-8"))
    return {}


def load_adun_social_summary() -> dict:
    if ADUN_SOCIAL_JSON.exists():
        return json.loads(ADUN_SOCIAL_JSON.read_text(encoding="utf-8"))
    return {}


def load_prn_dates() -> dict:
    default = {
        "announced_at": None,
        "negeri_sembilan": {
            "penamaan_display": "TBD",
            "undi_awal_display": "TBD",
            "mengundi_display": "TBD",
            "mengundi": None,
        },
        "johor": {"mengundi_display": "TBD"},
    }
    if not PRN_DATES_JSON.exists():
        return default
    return json.loads(PRN_DATES_JSON.read_text(encoding="utf-8"))


def load_dpi_updates() -> dict:
    if DPI_UPDATES_JSON.exists():
        try:
            return json.loads(DPI_UPDATES_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"meta": {}, "byCode": {}, "mnProposals": [], "highlights": {}}


def load_ml_analytics() -> dict:
    if ML_JSON.exists():
        try:
            return json.loads(ML_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def load_narrative_intel() -> dict:
    intel: dict = {}
    if NARRATIVE_INTEL_JSON.exists():
        try:
            intel = json.loads(NARRATIVE_INTEL_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            intel = {}
    if CINA_META_JSON.exists():
        try:
            meta = json.loads(CINA_META_JSON.read_text(encoding="utf-8"))
            intel["crawl_project"] = meta.get("name")
            intel["crawl_batches"] = len(meta.get("crawls") or [])
            intel["crawl_rows"] = sum(int(c.get("rows") or 0) for c in (meta.get("crawls") or []))
        except json.JSONDecodeError:
            pass
    intel.setdefault("n9_campaign_notes", [
        "Isu syurga/Harakat panas dalam gelembung Melayu X — komuniti Cina hampir tidak respond (5 post 汉字, 0 komen).",
        "Media Cina fokus ketelusan PAS–BN (Johor proxy) — soal sama relevan untuk bandar NS (N01, N13, N21, N23).",
        "Jangan lead dengan teologi syurga ke pengundi Cina; jelaskan MN = stabil + perkhidmatan + ekonomi.",
        "DAP/PH bertahan dengan naratif defensive (Anwar + hak Melayu) — ruang untuk PAS+PN jika messaging ekonomi kuat.",
    ])
    return intel


def days_until(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (target - datetime.now().date()).days
    except ValueError:
        return None


def find_latest_pas_master() -> Path | None:
    """Return newest analyzed PAS-Break master CSV."""
    candidates = sorted(
        PAS_MASTER_DIR.glob("PAS_Break_Master_EXCO_Analyzed_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    fallback = sorted(
        PAS_MASTER_DIR.glob("PAS_Break_Master_EXCO_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return fallback[0] if fallback else None


def _sum_engagement(df: pd.DataFrame) -> dict:
    """Aggregate crawl rows, post/comment rows, comments_count, and engagement."""
    out = {
        "rows": 0,
        "postRows": 0,
        "commentRows": 0,
        "commentsCount": 0,
        "likes": 0,
        "shares": 0,
        "views": 0,
        "total": 0,
        # UI aliases — posts=mention rows, comments=aggregated comments_count on posts
        "posts": 0,
        "comments": 0,
    }
    if df is None or df.empty:
        return out
    out["rows"] = len(df)
    posts_only = df
    if "Type" in df.columns:
        t = df["Type"].fillna("").astype(str).str.lower()
        out["postRows"] = int((t == "post").sum())
        out["commentRows"] = int((t == "comment").sum())
        posts_only = df[t == "post"]
    else:
        out["postRows"] = len(df)
    if "comments_count" in df.columns and not posts_only.empty:
        out["commentsCount"] = int(
            pd.to_numeric(posts_only["comments_count"], errors="coerce").fillna(0).sum()
        )
    else:
        out["commentsCount"] = out["commentRows"]
    for col, key in (("likes", "likes"), ("shares", "shares"), ("views", "views")):
        if col in df.columns:
            out[key] = int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
    if "total_engagement" in df.columns:
        out["total"] = int(pd.to_numeric(df["total_engagement"], errors="coerce").fillna(0).sum())
    if out["total"] == 0:
        out["total"] = out["likes"] + out["shares"] + out["commentsCount"]
    out["posts"] = out["rows"]
    out["comments"] = out["commentsCount"]
    return out


def _fmt_eng(n) -> str:
    if n is None or n == "—":
        return "—"
    try:
        v = int(n)
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"{v:,}"
        return str(v)
    except (TypeError, ValueError):
        return str(n)


def _build_hybrid_credibility(
    hybrid: dict,
    news_analyzed: dict,
    news_sum: dict,
    social_sentiment: dict,
) -> dict:
    """Trust signals, executive insights, and cross-layer synthesis."""
    meta = social_sentiment.get("meta") or {}
    totals = hybrid.get("totals") or {}
    hero = hybrid.get("crawlHero") or {}
    mt = news_analyzed.get("media_tone") or {}
    pv = news_analyzed.get("public_voice") or {}
    media_neg = float(mt.get("neg_pct") or 0)
    ns_neg = float(meta.get("nsNegPct") or 0)
    rows_a = int(news_analyzed.get("rows_analyzed") or 0)
    rows_skip = int(news_analyzed.get("rows_skipped") or 0)
    crawled = int(totals.get("totalPostsCrawled") or 0)
    eng_g = int(totals.get("engagementGlobal") or 0)
    eng_ns = int(totals.get("engagementNS") or 0)
    mode = news_analyzed.get("analysis_mode") or "keyword_fallback"
    analyzed_at = (news_analyzed.get("analyzed_at") or news_sum.get("fetched_at") or "")[:16].replace("T", " ")
    alerts = news_analyzed.get("narrative_alerts") or []

    insights: list[dict] = []
    if media_neg >= 35:
        insights.append({
            "icon": "alert-triangle",
            "severity": "high",
            "title": f"Media Tone: {media_neg:.1f}% negatif (Tier A)",
            "body": (
                f"{rows_a} artikel direct scrape dianalisis ML — bukan headline RSS bulk. "
                f"{rows_skip:,} artikel RSS di-skip untuk kualiti."
            ),
        })
    if crawled >= 50000:
        insights.append({
            "icon": "database",
            "severity": "info",
            "title": f"{crawled:,} rekod socmed — skala enterprise",
            "body": (
                f"{hero.get('postRows', totals.get('postRowsGlobal', 0)):,} posts · "
                f"{hero.get('commentRows', totals.get('commentRowsGlobal', 0)):,} komen · "
                f"{_fmt_eng(eng_g)} engagement merentasi 6 platform."
            ),
        })
    if eng_ns >= 100000:
        insights.append({
            "icon": "zap",
            "severity": "info",
            "title": f"NS discourse: {_fmt_eng(eng_ns)} engagement",
            "body": (
                f"{hero.get('nsPosts', meta.get('totalPosts', 0)):,} mention Negeri Sembilan — "
                f"{(hero.get('nsComments') or totals.get('commentsNS') or 0):,} komen aggregated."
            ),
        })
    if alerts:
        top = alerts[0]
        insights.append({
            "icon": "newspaper",
            "severity": top.get("severity") or "watch",
            "title": "Alert naratif media",
            "body": str(top.get("message") or "")[:180],
        })
    if ns_neg and media_neg:
        gap = abs(ns_neg - media_neg)
        align = "selari" if gap < 15 else "berbeza"
        insights.append({
            "icon": "git-compare",
            "severity": "neutral",
            "title": f"Media vs Socmed: nada {align}",
            "body": (
                f"Media Tier A {media_neg:.1f}% neg · Socmed NS {ns_neg:.1f}% neg — "
                "lapisan kekal berasingan; bandingkan trend, bukan purata."
            ),
        })

    layer_meta = [
        {
            "id": "media_tone",
            "tier": "Tier A",
            "quality": min(98, 70 + rows_a),
            "status": "verified" if mode == "ml_models" else "fallback",
            "statusLabel": "ML Verified" if mode == "ml_models" else "Keyword",
            "sample": f"n={rows_a}",
            "models": "ft-Malay-bert · emotion classifier",
        },
        {
            "id": "public_voice",
            "tier": "Tier B",
            "quality": 25 if not pv.get("total") else 60,
            "status": "pending",
            "statusLabel": "Tiada Komen Lagi",
            "sample": f"n={pv.get('total') or 0}",
            "models": "Coral API · FMT RSS — pipeline OK",
        },
        {
            "id": "socmed_master",
            "tier": "Master",
            "quality": min(99, 80 + (10 if crawled > 60000 else 0)),
            "status": "live",
            "statusLabel": "Live Crawl",
            "sample": f"n={crawled:,}",
            "models": "Apify actors · HF ML sentiment",
        },
    ]

    headline_parts = []
    if media_neg >= 40:
        headline_parts.append(f"media bearish ({media_neg:.0f}% neg)")
    if crawled:
        headline_parts.append(f"{crawled // 1000}K+ rekod socmed")
    if eng_ns:
        headline_parts.append(f"{_fmt_eng(eng_ns)} engagement NS")
    executive_headline = (
        " · ".join(headline_parts).capitalize() + "."
        if headline_parts
        else "Pipeline hybrid aktif — 3 lapisan data berasingan."
    )

    return {
        "executiveHeadline": executive_headline,
        "updatedAt": analyzed_at or "—",
        "trustStrip": [
            {"icon": "shield-check", "label": "3-Lapisan Berasingan", "sub": "Media · Suara · Socmed"},
            {"icon": "cpu", "label": "ML Verified" if mode == "ml_models" else "Keyword Mode", "sub": mode},
            {"icon": "layers", "label": f"n={crawled:,}", "sub": "Sample socmed master"},
            {"icon": "globe", "label": "6 Platform", "sub": "FB · TikTok · X · News · IG · Threads"},
            {"icon": "clock", "label": "Fresh Data", "sub": analyzed_at or "Harian pipeline"},
            {"icon": "badge-check", "label": "RM0 News Crawl", "sub": f"{news_sum.get('total_articles', 0)} artikel"},
        ],
        "insights": insights[:5],
        "layerMeta": layer_meta,
        "methodology": [
            "Tier A = direct scrape sahaja (China Press, Sin Chew, Oriental, BH…) — ML sentiment.",
            f"Tier B bulk RSS ({rows_skip:,} rows) dikecualikan dari skor media.",
            "Socmed master = crawl penuh; filter NS = keyword Negeri Sembilan / PRN N9.",
            "Engagement = likes + shares + views + comments_count — bukan polling SPR.",
        ],
    }


def build_hybrid_model(social_sentiment: dict, news_sum: dict, news_analyzed: dict) -> dict:
    """3-layer hybrid intelligence — Media Tone · Public Voice · Socmed Master."""
    meta = social_sentiment.get("meta") or {}
    eng_ns = meta.get("engagementNS") or {}
    eng_global = meta.get("engagementGlobal") or {}
    eng_prn = meta.get("engagementPRN") or {}
    crawl = meta.get("crawlStats") or {}
    mt = news_analyzed.get("media_tone") or {}
    pv = news_analyzed.get("public_voice") or {}
    by_method = news_sum.get("by_crawl_method") or {}
    master_rows = meta.get("masterTotal") or meta.get("totalPostsCrawled") or 0
    ns_neg_pct = meta.get("nsNegPct")
    hybrid_core = {
        "title": "Hybrid Intelligence Model",
        "subtitle": "3 lapisan berasingan — Media · Suara Awam · Socmed (jangan campur skor)",
        "crawlHero": {
            "totalPostsCrawled": master_rows,
            "postRows": eng_global.get("postRows") or crawl.get("global", {}).get("postRows", 0),
            "commentRows": eng_global.get("commentRows") or crawl.get("global", {}).get("commentRows", 0),
            "engagementGlobal": eng_global.get("total") or 0,
            "nsPosts": meta.get("totalPosts") or 0,
            "nsComments": eng_ns.get("commentsCount") or eng_ns.get("comments") or 0,
            "nsEngagement": eng_ns.get("total") or 0,
            "prnPosts": meta.get("prnMentions") or eng_prn.get("rows") or 0,
            "prnEngagement": eng_prn.get("total") or 0,
            "window": meta.get("window") or "Master crawl minggu lepas",
            "source": meta.get("masterSource") or "pas_break_2026/master/",
        },
        "layers": [
            {
                "id": "media_tone",
                "label": "Media Tone",
                "icon": "📰",
                "desc": "Direct scrape + Tier A ML (China Press, Oriental, Sin Chew, BH…)",
                "posts": news_analyzed.get("posts_analyzed") or 0,
                "comments": news_analyzed.get("comments_analyzed") or 0,
                "engagement": "—",
                "negPct": mt.get("neg_pct"),
                "mode": news_analyzed.get("analysis_mode", "—"),
                "path": "PRN/PRN_N9/crawls/news_analyzed/",
            },
            {
                "id": "public_voice",
                "label": "Public Voice",
                "icon": "💬",
                "desc": (
                    "Komen pembaca — Coral (China Press) + FMT RSS. "
                    "API berfungsi; artikel semasa tiada komen pembaca (total_result=0)."
                ),
                "posts": 0,
                "comments": pv.get("total") or news_sum.get("total_comments") or 0,
                "engagement": "—",
                "negPct": pv.get("neg_pct") if (pv.get("total") or news_sum.get("total_comments")) else None,
                "mode": "Pipeline OK · tiada komen lagi",
                "path": "PRN/PRN_N9/crawls/news/",
                "emptyNote": (
                    "22 artikel China Press + 3 FMT di-crawl — Coral API OK, "
                    "tetapi pembaca belum komen. Akan auto-isi bila komen muncul."
                ),
            },
            {
                "id": "socmed_master",
                "label": "Socmed Master",
                "icon": "📱",
                "desc": (
                    f"FB · TikTok · X · News — {master_rows:,} rows crawl global · "
                    f"filter NS {meta.get('totalPosts') or 0:,} mention"
                ),
                "posts": meta.get("totalPosts") or 0,
                "comments": eng_ns.get("commentsCount") or eng_ns.get("comments") or 0,
                "engagement": eng_ns.get("total") or 0,
                "negPct": ns_neg_pct,
                "mode": "Apify + HF ML",
                "path": "pas_break_2026/master/",
                "crawlGlobal": master_rows,
            },
        ],
        "totals": {
            "newsArticles": news_sum.get("total_articles") or news_sum.get("total") or 0,
            "directScrape": by_method.get("direct_scrape", 0),
            "googleNewsRss": by_method.get("google_news_rss", 0),
            "totalPostsCrawled": master_rows,
            "masterRows": master_rows,
            "postRowsGlobal": eng_global.get("postRows") or 0,
            "commentRowsGlobal": eng_global.get("commentRows") or 0,
            "engagementNS": eng_ns.get("total") or 0,
            "engagementGlobal": eng_global.get("total") or 0,
            "commentsNS": eng_ns.get("commentsCount") or eng_ns.get("comments") or 0,
            "prnMentions": meta.get("prnMentions") or eng_prn.get("rows") or 0,
            "likesNS": eng_ns.get("likes") or 0,
            "viewsNS": eng_ns.get("views") or 0,
        },
    }
    hybrid_core["credibility"] = _build_hybrid_credibility(
        hybrid_core, news_analyzed, news_sum, social_sentiment
    )
    return hybrid_core


def _map_platform_tab(platform: str) -> str:
    p = str(platform).lower()
    if p in ("facebook", "fb"):
        return "facebook"
    if p == "tiktok":
        return "tiktok"
    if p in ("x", "twitter"):
        return "x"
    if p in ("news", "google news", "google_news"):
        return "media"
    return "other"


def _account_from_url(url: str, platform: str) -> str | None:
    url = str(url or "")
    if not url.startswith("http"):
        return None
    plat = str(platform).lower()
    if plat == "tiktok":
        m = re.search(r"tiktok\.com/@([^/?]+)", url, re.I)
        return f"@{m.group(1)}" if m else None
    if plat == "facebook":
        m = re.search(r"facebook\.com/([^/?]+)", url, re.I)
        return m.group(1).replace(".", " ") if m else None
    if plat in ("x", "twitter"):
        m = re.search(r"(?:twitter|x)\.com/([^/?]+)", url, re.I)
        return f"@{m.group(1)}" if m else None
    if plat == "news":
        host = urlparse(url).netloc.replace("www.", "")
        return host or None
    return None


def _sentiment_counts(sub: pd.DataFrame) -> dict:
    primary = sub["sentiment_label"] if "sentiment_label" in sub.columns else pd.Series(dtype=object)
    fallback = sub["Sentiment"] if "Sentiment" in sub.columns else pd.Series(dtype=object)
    labels = primary.combine_first(fallback).fillna("neutral").astype(str).str.lower()
    labels = labels.replace({"nan": "neutral", "none": "neutral"})
    counts = Counter(labels)
    return {
        "positive": int(counts.get("positive", 0)),
        "neutral": int(counts.get("neutral", 0)),
        "negative": int(counts.get("negative", 0)),
    }


def _top_keywords(texts: pd.Series, limit: int = 5) -> list[str]:
    tags = Counter()
    terms = Counter()
    for raw in texts.head(800):
        t = str(raw).lower()
        for tag in re.findall(r"#([\w\u0080-\uFFFF]+)", t):
            tags[tag] += 1
        for w in re.findall(
            r"\b(prn|pas|bersatu|pn|spr|aminuddin|dun|umno|ph|penamaan|negeri sembilan)\b",
            t,
        ):
            terms[w] += 1
    out: list[str] = []
    for tag, _ in tags.most_common(limit):
        out.append(f"#{tag}")
    for term, _ in terms.most_common(limit):
        label = term.upper() if term in ("prn", "pas", "pn", "spr", "ph") else term.title()
        if label not in out:
            out.append(label)
        if len(out) >= limit:
            break
    return out[:limit] or ["PRN NS", "Negeri Sembilan", "PAS", "SPR"]


def _top_influencers(sub: pd.DataFrame, limit: int = 4) -> list[str]:
    if "URL" not in sub.columns:
        return []
    scores: Counter = Counter()
    for _, row in sub.iterrows():
        acct = _account_from_url(row.get("URL", ""), row.get("Platform", ""))
        if not acct:
            continue
        eng = float(row.get("total_engagement") or 0)
        scores[acct] += max(eng, 1)
    return [a for a, _ in scores.most_common(limit)]


def _top_narrative_snippets(sub: pd.DataFrame, limit: int = 4) -> list[str]:
    if sub.empty:
        return []
    sort_col = "total_engagement" if "total_engagement" in sub.columns else None
    ordered = sub.sort_values(sort_col, ascending=False) if sort_col else sub
    out = []
    for text in ordered["Text"].head(limit * 2):
        snippet = re.sub(r"\s+", " ", str(text)).strip()[:90]
        if snippet and snippet not in out:
            out.append(snippet)
        if len(out) >= limit:
            break
    return out


def _top_posts_ns(ns: pd.DataFrame, limit: int = 5) -> list[dict]:
    if ns.empty:
        return []
    sort_col = "total_engagement" if "total_engagement" in ns.columns else None
    ordered = ns.sort_values(sort_col, ascending=False) if sort_col else ns
    posts = []
    for _, row in ordered.head(limit).iterrows():
        sent_col = "sentiment_label" if "sentiment_label" in row.index else "Sentiment"
        sent = str(row.get(sent_col, "Neutral")).title()
        posts.append({
            "platform": str(row.get("Platform", "—")).title(),
            "account": _account_from_url(row.get("URL", ""), row.get("Platform", "")) or "—",
            "summary": re.sub(r"\s+", " ", str(row.get("Text", "")))[:100],
            "engagement": int(float(row.get("total_engagement") or 0)),
            "sentiment": sent,
            "risk": "Tinggi" if sent.lower() == "negative" else ("Sederhana" if sent.lower() == "neutral" else "Rendah"),
        })
    return posts


def extract_social_sentiment_from_master(pas: dict, news_sum: dict) -> dict:
    """Build Sentimen tab from PAS-Break master CSV (NS keyword filter)."""
    states_ns = pas.get("states", {}).get("ns", {})
    master_path = find_latest_pas_master()
    fallback = {
        "facebook": {"volume": 48, "positive": 10, "neutral": 20, "negative": 18},
        "tiktok": {"volume": 142, "positive": 9, "neutral": 11, "negative": 14},
        "x": {"volume": 19, "positive": 5, "neutral": 10, "negative": 4},
        "media": {"volume": news_sum.get("total_articles") or 13, "positive": 3, "neutral": 8, "negative": 2},
    }
    meta = {
        "totalPosts": states_ns.get("rows", 222),
        "politicalRows": pas.get("ns", {}).get("political_rows", states_ns.get("rows", 222)),
        "window": pas.get("meta", {}).get("window", "9–11 Jun 2026"),
        "splitVsSolo": f"{states_ns.get('split', 36)} vs {states_ns.get('solo', 6)}",
        "pnVsMn": f"{states_ns.get('pn', 29)} vs {states_ns.get('mn', 12)}",
        "masterSource": None,
        "masterTotal": 68256,
        "totalPostsCrawled": 68256,
        "otherPlatforms": {},
        "dataNote": "Snapshot politik 222 posts (9–11 Jun) — bukan keseluruhan crawl",
    }

    if not master_path:
        tabs = {}
        for key, base in fallback.items():
            tabs[key] = {
                **base,
                "keywords": ["PRN NS", "PAS", "SPR"],
                "influencers": [],
                "narratives": [],
            }
        return {
            **tabs,
            "volumeTrend": generate_volume_trend_30d(),
            "dominantNarratives": _default_dominant_narratives(states_ns),
            "topPosts": [],
            "meta": meta,
        }

    df = pd.read_csv(master_path, low_memory=False)
    text = df["Text"].fillna("").astype(str)
    ns = df[text.str.contains(NS_PATTERN, case=False, na=False)].copy()
    prn = df[text.str.contains(PRN_PATTERN, case=False, na=False)].copy()
    ns["tab"] = ns["Platform"].apply(_map_platform_tab)
    meta["masterSource"] = str(master_path.relative_to(ROOT))
    meta["masterTotal"] = len(df)
    meta["totalPostsCrawled"] = len(df)
    meta["totalPosts"] = len(ns)
    meta["prnMentions"] = len(prn)
    meta["engagementGlobal"] = _sum_engagement(df)
    meta["engagementNS"] = _sum_engagement(ns)
    meta["engagementPRN"] = _sum_engagement(prn)
    meta["crawlStats"] = {
        "global": meta["engagementGlobal"],
        "nsFocus": meta["engagementNS"],
        "prnBroad": meta["engagementPRN"],
    }
    sent_ns = _sentiment_counts(ns)
    meta["nsSentiment"] = sent_ns
    ns_total = len(ns)
    meta["nsNegPct"] = round(sent_ns["negative"] / ns_total * 100, 1) if ns_total else 0
    political = ns[
        (ns.get("mentions_pas") == True)  # noqa: E712
        | (ns.get("mentions_bersatu") == True)  # noqa: E712
        | (ns.get("narrative_split") == True)  # noqa: E712
    ]
    meta["politicalRows"] = len(political)
    meta["window"] = f"Master crawl · {len(ns):,} mention NS · {len(df):,} rows global"
    meta["dataNote"] = (
        f"Tab platform dari master {master_path.name} — filter keyword NS. "
        f"Snapshot event 9–11 Jun = {states_ns.get('rows', 222)} posts politik."
    )
    other = ns[ns["tab"] == "other"]["Platform"].str.lower().value_counts()
    meta["otherPlatforms"] = {str(k): int(v) for k, v in other.items()}

    tabs = {}
    for tab in ("facebook", "tiktok", "x", "media"):
        sub = ns[ns["tab"] == tab]
        base = fallback[tab]
        if sub.empty:
            tabs[tab] = {
                **base,
                "keywords": ["PRN NS", "Negeri Sembilan"],
                "influencers": [],
                "narratives": [],
            }
            continue
        sent = _sentiment_counts(sub)
        tabs[tab] = {
            "volume": len(sub),
            **sent,
            "keywords": _top_keywords(sub["Text"]),
            "influencers": _top_influencers(sub) or (
                ["Bernama", "Astro Awani"] if tab == "media" else []
            ),
            "narratives": _top_narrative_snippets(sub)
            or [str(h.get("text", h))[:80] for h in (news_sum.get("top_headlines") or [])[:4]]
            or [],
        }

    trend = generate_volume_trend_30d()
    if trend:
        trend[-1]["volume"] = len(ns)

    top_posts = _top_posts_ns(ns)
    if not top_posts:
        top_posts = [
            {
                "platform": p.get("platform", "—").title(),
                "account": "—",
                "summary": str(p.get("text", ""))[:100],
                "engagement": int(p.get("engagement") or 0),
                "sentiment": "Neutral",
                "risk": "Sederhana",
            }
            for p in (pas.get("ns", {}).get("top_posts") or [])[:5]
        ]

    return {
        **tabs,
        "volumeTrend": trend,
        "dominantNarratives": _default_dominant_narratives(states_ns),
        "topPosts": top_posts,
        "meta": meta,
    }


def _default_dominant_narratives(states_ns: dict) -> list[dict]:
    total = max(states_ns.get("split", 0) + states_ns.get("solo", 0) + states_ns.get("pn", 0), 1)
    return [
        {
            "title": "PAS patut solo di NS",
            "share": round(states_ns.get("solo", 6) / total * 100),
            "sentiment": "Campuran",
            "risk": "Sederhana",
        },
        {
            "title": "PAS rugi jika tinggalkan PN",
            "share": round(states_ns.get("split", 36) / total * 100),
            "sentiment": "Negatif",
            "risk": "Tinggi",
        },
        {
            "title": "PAS lebih kuat dengan UMNO",
            "share": round(states_ns.get("mn", 12) / total * 100),
            "sentiment": "Neutral",
            "risk": "Sederhana",
        },
        {
            "title": "PN lemah tanpa perpaduan",
            "share": round(states_ns.get("pn", 29) / total * 100),
            "sentiment": "Negatif",
            "risk": "Tinggi",
        },
    ]


def extract_economic_outlook():
    """Layer persepsi ekonomi from SME Bank crawl — reused for PRN NS context."""
    if not SME_MASTER.exists():
        return {
            "source": "smebank (missing)",
            "status": "pending",
            "crawlWindow": "—",
            "totalPosts": 0,
            "economicStressPosts": 0,
            "sentiment": {"negativePct": 0, "neutralPct": 0, "positivePct": 0},
            "topIssues": [],
            "newsHeadlines": [],
            "nsHeadlines": [],
            "analystBrief": "Data SME belum tersedia.",
            "prnImpact": "—",
            "officialPending": ["BNM OPR", "DOSM CPI N9", "MIDA pelaburan NS"],
        }

    df = pd.read_csv(SME_MASTER, low_memory=False)
    text = df["Text"].fillna("").astype(str).str.lower()
    stress = df[text.str.contains(STRESS_PATTERN, case=False, na=False)]
    sent = Counter(stress["Sentiment"].str.lower())
    total = len(stress) or 1

    words = []
    for row in stress["Text"].head(600):
        words.extend(re.findall(
            r"\b(hutang|harga|kos|sewa|pinjaman|inflasi|opr|ringgit|ekonomi|gdp|tarif|cashflow)\b",
            str(row).lower(),
        ))

    news = df[df["Platform"].str.lower() == "news"]
    news_econ = news[text.loc[news.index].str.contains(
        r"ringgit|inflasi|bnm|opr|cpi|ekonomi|pelaburan|gdp|tarif", case=False, na=False
    )]
    ns = df[text.str.contains(NS_PATTERN, case=False, na=False)]

    neg_pct = round(sent.get("negative", 0) / total * 100, 1)
    official = load_official_economic()
    off = official.get("official") or {}
    macro_h = official.get("macro_headlines") or []
    news_h = load_news_summary().get("top_headlines") or []

    return {
        "source": "data/projects/sme/smebank/master/SMEBank_Master_20260609.csv",
        "status": "active",
        "crawlWindow": "90 hari (Mac–Jun 2026)",
        "totalPosts": len(df),
        "economicStressPosts": len(stress),
        "sentiment": {
            "negative": sent.get("negative", 0),
            "neutral": sent.get("neutral", 0),
            "positive": sent.get("positive", 0),
            "negativePct": neg_pct,
            "neutralPct": round(sent.get("neutral", 0) / total * 100, 1),
            "positivePct": round(sent.get("positive", 0) / total * 100, 1),
        },
        "topIssues": [{"issue": k, "mentions": v} for k, v in Counter(words).most_common(8)],
        "nsMentions": len(ns),
        "nsHeadlines": [str(t)[:160] for t in ns["Text"].head(4)],
        "newsHeadlines": [str(t)[:180] for t in news_econ["Text"].head(5)],
        "macroContext": {
            "ringgit": f"Ringgit ~RM{off.get('usd_myr', '—')}/USD (BNM {off.get('usd_date', '—')})" if off.get("usd_myr") else "Ringgit ~RM4.07/USD (berita crawl Jun 2026)",
            "opr": f"OPR {off.get('opr_pct', '—')}% (BNM {off.get('opr_date', '—')})" if off.get("opr_pct") else "OPR — pending pull",
            "investment": "Pelaburan diluluskan RM92.8B suku pertama (berita crawl SME)",
            "perceptionGap": "Makro positif vs micro-stress SME — jurang naratif politik",
        },
        "officialMacro": official,
        "macroHeadlinesLive": macro_h,
        "newsHeadlinesLive": [h.get("text", "")[:180] for h in news_h[:5]],
        "analystBrief": (
            f"Dari {len(stress):,} posts berkait tekanan ekonomi (crawl SME), {neg_pct}% bertone negatif. "
            "Isu dominan: cashflow, ringgit, hutang — relevan untuk pengundi bandar Seremban/Nilai dan "
            "peniaga kecil FELDA. Bukan pengganti CPI rasmi N9, tetapi proxy kuat untuk mood 'kos sara hidup'."
        ),
        "prnImpact": (
            "PH/BN perlu jawab jurang persepsi: data pelaburan kuat tetapi rakyat bercakap hutang & harga. "
            "PN/PAS boleh tarik naratif 'rakyat susah' di LBN. Kerusi bandar (N01, N21) lebih sensitif isu ini."
        ),
        "officialPending": ["DOSM CPI N9 (OpenDOSM manual)", "MIDA pelaburan NS"],
        "officialStatus": "active" if off.get("opr_pct") else "pending",
    }


def build_mock_data(seats, pas, economic_outlook):
    news_sum = load_news_summary()
    news_analyzed = load_news_analyzed_summary()
    adun_soc = load_adun_social_summary()
    prn_dates = load_prn_dates()
    dpi_updates = load_dpi_updates()
    ml_analytics = load_ml_analytics()
    narrative_intel = load_narrative_intel()
    ns = prn_dates.get("negeri_sembilan", {})
    jh = prn_dates.get("johor", {})
    days_poll = days_until(ns.get("mengundi"))
    days_nom = days_until(ns.get("penamaan"))
    days_poll_s = str(days_poll) if days_poll is not None else "—"
    days_nom_s = str(days_nom) if days_nom is not None else "—"
    eco = economic_outlook
    top_issues = ", ".join(i["issue"] for i in eco.get("topIssues", [])[:4]) or "kos sara hidup, cashflow"
    eco_blurb = (
        f"Proxy SME crawl: {eco.get('economicStressPosts', 0):,} posts tekanan ekonomi, "
        f"{eco.get('sentiment', {}).get('negativePct', 0)}% negatif. Isu: {top_issues}. "
        f"{eco.get('macroContext', {}).get('perceptionGap', '')}"
    )

    coalition_scenarios = [
        {
            "name": "PAS Solo",
            "slug": "solo",
            "probability": 0.18,
            "projectedSeats": 4,
            "winChance": "Rendah–Sederhana",
            "malayVoteImpact": "Pecah undi Melayu PN; identiti PAS lebih jelas",
            "grassrootsRisk": "Tinggi — tekanan akar umbi pro-PN",
            "threeCornerRisk": "Sangat tinggi di 8–12 kerusi",
            "phBnImpact": "PH/BN untung di kerusi marginal Melayu",
            "opportunity": "Identiti parti lebih jelas",
            "risk": "Pecah undi dan hilang kelebihan pakatan",
            "whyReasonable": "Isyarat media PAS NS selepas split global; calon muda mahu profil berbeza.",
            "signals": "Kenyataan Pusat PAS, poster calon solo, penolakan logo PN.",
            "triggers": "Keputusan mesyuarat PAS Negeri, arahan HQ, reaksi Bersatu NS.",
        },
        {
            "name": "PAS kekal bersama PN",
            "slug": "pn",
            "probability": 0.42,
            "projectedSeats": 7,
            "winChance": "Sederhana",
            "malayVoteImpact": "Konsolidasi undi Melayu anti-PH",
            "grassrootsRisk": "Sederhana — kekeliruan selepas split HQ",
            "threeCornerRisk": "Sederhana jika BN bertanding sendiri",
            "phBnImpact": "Tekanan pada kerusi PH marginal (N01, N13, N21)",
            "opportunity": "Kekalkan mesin PN di lapangan",
            "risk": "Credibility jika HQ bercanggah dengan negeri",
            "whyReasonable": "Majoriti jentera NS masih bias PN; 5 kerusi sedia ada.",
            "signals": "Joint statement negeri, logo PN di banner, koordinasi Bersatu.",
            "triggers": "Keputusan SPR penamaan, arahan Tg Abdul Rahman NS.",
        },
        {
            "name": "PAS + UMNO/MN",
            "slug": "mn",
            "probability": 0.22,
            "projectedSeats": 11,
            "winChance": "Tinggi (jika material)",
            "malayVoteImpact": "Gabungan undi Melayu kuat di LBN/FELDA",
            "grassrootsRisk": "Tinggi — sejarah PH-BN masih segar",
            "threeCornerRisk": "Rendah di kerusi Melayu, tinggi di bandar",
            "phBnImpact": "PH terancam di 6+ kerusi; BN komponen bercanggah",
            "opportunity": "Retak PH di zon rural Melayu",
            "risk": "Backlash bandar & komponen PH",
            "whyReasonable": "MN hanya 12 mention NS — ruang naratif belum dipenuhi.",
            "signals": "Pertemuan silaturahim, kenyataan UMNO cawangan, isu FELDA.",
            "triggers": "Keputusan UMNO Negeri, isu calon bertindih.",
        },
        {
            "name": "PAS + jajaran baharu",
            "slug": "new",
            "probability": 0.18,
            "projectedSeats": 6,
            "winChance": "Tidak menentu",
            "malayVoteImpact": "Tarik pengundi muda & neutral",
            "grassrootsRisk": "Sederhana — brand baharu perlu masa",
            "threeCornerRisk": "Tinggi semasa fasa awal",
            "phBnImpact": "PH mungkin kekal jika gabungan tidak stabil",
            "opportunity": "Elak stigma split; imej segar",
            "risk": "Pengundi keliru tanpa logo familiar",
            "whyReasonable": "Opsyen 'Bersatu' branding baharu disebut dalam media.",
            "signals": "Launch manifesto gabungan, calon independen berkoordinasi.",
            "triggers": "Pendaftaran parti, tarikh penamaan.",
        },
    ]

    coalition_watch = [
        {"name": "PAS Solo", "status": "Dipantau", "probability": 0.18, "upside": "Profil ideologi jelas", "risk": "Pecah undi PN"},
        {"name": "PAS + PN", "status": "Kemungkinan tinggi", "probability": 0.42, "upside": "Kekalkan 5 kerusi asas", "risk": "Isyarat HQ vs negeri"},
        {"name": "PAS + MN/UMNO", "status": "Spekulatif", "probability": 0.22, "upside": "LBN/FELDA swing", "risk": "Backlash bandar"},
        {"name": "PAS + gabungan baharu", "status": "Opsyen terbuka", "probability": 0.18, "upside": "Naratif segar", "risk": "Pengundi keliru"},
    ]

    priority_codes = ["N05", "N25", "N31", "N01", "N13", "N21", "N20", "N34"]
    seat_map = {s["code"]: s for s in seats}
    constituency_profiles = []
    for code in priority_codes:
        s = seat_map.get(code, {})
        extras = PROFILE_EXTRAS.get(code, {})
        pct_m = s.get("pctMelayu")
        if pct_m is not None:
            demografi = (
                f"Melayu {pct_m:.1f}% · Cina {s.get('pctCina', 0):.1f}% · "
                f"India {s.get('pctIndia', 0):.1f}% · Pengundi {s.get('registeredVotersDpi', 0):,} (DPI Dec 2025)"
            )
        else:
            demografi = (
                "Melayu ~65–78% (anggaran PRN 2023); bandar muda meningkat di N01/N21."
                if code in ("N01", "N21")
                else "Melayu dominan; komuniti FELDA/signifikan di LBN."
            )
        calon_line = s.get("winnerName", "—")
        if s.get("mnCalon"):
            calon_line += f" · Cadangan MN: {s.get('mnCalon')}"
        constituency_profiles.append({
            "code": code,
            "name": s.get("name", code),
            "demografi": demografi,
            "ekonomi": eco_blurb if code in ("N01", "N21") else (
                f"Manufacturing/FELDA — sensitif {top_issues}. "
                f"Tekanan persepsi {eco.get('sentiment', {}).get('negativePct', 0)}% (SME crawl nasional)."
            ),
            "tempatan": extras.get("tempatan", "Infrastruktur jalan, banjir kilat, akses hospital/klinik."),
            "agamaIdentiti": extras.get("agamaIdentiti", "Isu institusi Islam, sekolah agama, naratif perpaduan ummah."),
            "fenceSitters": extras.get("fenceSitters", "Pengundi muda TikTok-first; swing 5–8% boleh ubah majoriti."),
            "calonStrength": (
                f"Penyandang {s.get('winnerName', '—')} ({s.get('party2023', '—')}); majoriti {s.get('majority', 0):,}. "
                f"Cula PAS {s.get('culaPct', '—')}% · BKC {s.get('bkcCula', '—')}."
            ),
            "priority": "Tinggi" if s.get("threeCornerRisk") == "Tinggi" or s.get("kategoriPas") in ("defend", "winnable") else "Sederhana",
            "jenteraStatus": s.get("jenteraStatus"),
            "culaPct": s.get("culaPct"),
            "bkcCula": s.get("bkcCula"),
        })

    social_sentiment = extract_social_sentiment_from_master(pas, news_sum)
    hybrid_model = build_hybrid_model(social_sentiment, news_sum, news_analyzed)
    ht = hybrid_model["totals"]
    eng_ns = social_sentiment.get("meta", {}).get("engagementNS") or {}
    mt = news_analyzed.get("media_tone") or {}
    by_method = news_sum.get("by_crawl_method") or {}

    data_sources = [
        {
            "name": "🧠 Hybrid Model — Media Tone",
            "status": "active",
            "frequency": "Harian",
            "readiness": "ML live",
            "layer": "media_tone",
            "posts": news_analyzed.get("posts_analyzed", 0),
            "comments": news_analyzed.get("comments_analyzed", 0),
            "engagement": "—",
            "endpoint": "PRN/PRN_N9/crawls/news_analyzed/",
            "note": f"Tier A · {news_analyzed.get('analysis_mode', '—')} · {mt.get('neg_pct', 0)}% neg media · skip {news_analyzed.get('rows_skipped', 0)} bulk RSS",
        },
        {
            "name": "🧠 Hybrid Model — Public Voice",
            "status": "pending" if not news_sum.get("total_comments") else "active",
            "frequency": "Harian",
            "readiness": "Coral+FMT",
            "layer": "public_voice",
            "posts": 0,
            "comments": news_sum.get("total_comments") or 0,
            "engagement": "—",
            "endpoint": "PRN/PRN_N9/crawls/news/ (Type=comment)",
            "note": "Komen pembaca — artikel semasa 0 komen; API Coral berfungsi",
        },
        {
            "name": "PAS-Break Master Crawl (Full Week)",
            "status": "active",
            "frequency": "Minggu lepas",
            "readiness": "Siap",
            "layer": "socmed_master",
            "posts": ht.get("totalPostsCrawled") or social_sentiment["meta"].get("masterTotal", 0),
            "comments": ht.get("commentRowsGlobal") or 0,
            "engagement": ht.get("engagementGlobal") or 0,
            "endpoint": social_sentiment["meta"].get("masterSource") or "pas_break_2026/master/",
            "note": (
                f"Total Posts Crawled · {ht.get('postRowsGlobal', 0):,} post rows · "
                f"{ht.get('commentRowsGlobal', 0):,} comment rows · "
                f"NS {social_sentiment['meta'].get('totalPosts', 0):,} mention · "
                f"komen {_fmt_eng(eng_ns.get('commentsCount') or eng_ns.get('comments', 0))}"
            ),
        },
        {
            "name": "🧠 Hybrid Model — Socmed Master",
            "status": "active",
            "frequency": "On-demand",
            "readiness": "Siap",
            "layer": "socmed_master",
            "posts": social_sentiment["meta"].get("totalPosts", 0),
            "comments": eng_ns.get("commentsCount") or eng_ns.get("comments", 0),
            "engagement": eng_ns.get("total", 0),
            "endpoint": "pas_break_2026/master/PAS_Break_Master_EXCO_Analyzed_*.csv",
            "note": f"NS filter · {_fmt_eng(eng_ns.get('total', 0))} engagement · master {_fmt_eng(ht.get('totalPostsCrawled', 0))} rows crawl",
        },
        {"name": "DPI Pengundi N9 (Dec 2025)", "status": "active", "frequency": "Statik SPR", "readiness": "Siap", "layer": "static", "posts": 36, "comments": "—", "engagement": "—", "endpoint": "JITP_2026/Master_File/N9/Updates_Demografi pengundi N9 DPI Dec 2025.xlsx", "note": "36 DUN · bangsa · jantina · umur · pengundi berdaftar"},
        {"name": "Ranking DUN & Jentera (Jun 2026)", "status": "active", "frequency": "Statik", "readiness": "Siap", "layer": "static", "posts": 36, "comments": "—", "engagement": "—", "endpoint": "JITP_2026/Master_File/N9/Updates_Data DUN ikut ranking.xlsx", "note": "Majoriti · SKT 51% · Cula · BKC · Markah SLU"},
        {"name": "Cadangan Kerusi PAS+BN (MN)", "status": "active", "frequency": "Perbincangan", "readiness": "Siap", "layer": "static", "posts": len(dpi_updates.get("mnProposals", [])), "comments": "—", "engagement": "—", "endpoint": "JITP_2026/Master_File/N9/Updates_Cadangan kerusi - perbincangan MN.xlsx", "note": f"{len(dpi_updates.get('mnProposals', []))} cadangan calon · 10 Jun 2026"},
        {"name": "PRN 2023 Negeri Sembilan", "status": "active", "frequency": "Statik (baseline)", "readiness": "Siap", "layer": "static", "posts": 36, "comments": "—", "engagement": "—", "endpoint": "JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx", "note": "36 kerusi — Keputusan Penuh baseline"},
        {"name": "Scenario Engine (S1–S5)", "status": "active", "frequency": "Model + mock", "readiness": "Siap", "layer": "model", "posts": 5, "comments": "—", "engagement": "—", "endpoint": "PRN/_shared/templates/scenario_input_template.csv", "note": "Verified facts + 5 senario analitik — PapaParse-ready"},
        {"name": "ADUN Social Seeds Crawl", "status": "active" if adun_soc.get("total_rows") else "pending", "frequency": "On-demand", "readiness": "Siap" if adun_soc.get("total_rows") else "Jalankan crawl", "layer": "news", "posts": adun_soc.get("total_rows", 0), "comments": "—", "engagement": "—", "endpoint": "PRN/PRN_N9/reference/prn_n9_adun_social_summary.json", "note": f"{adun_soc.get('seats_crawled', 0)}/36 kerusi · {adun_soc.get('total_rows', 0)} mentions berita"},
        {"name": "Social Media Crawler (NS)", "status": "pending", "frequency": "On-demand", "readiness": "73 seeds", "layer": "socmed", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "InsightPulse app · ./start_full_app.sh", "note": "n9_prn_socmed_v2.xlsx — ADUN & media handles · post-penamaan"},
        {"name": "PAS-Break Event Monitor", "status": "active", "frequency": "Harian", "readiness": "Siap", "layer": "socmed", "posts": social_sentiment["meta"].get("politicalRows", 0), "comments": eng_ns.get("commentsCount") or eng_ns.get("comments", 0), "engagement": eng_ns.get("total", 0), "endpoint": "pas_break_2026/master/", "note": f"Total crawled {ht.get('totalPostsCrawled', 0):,} · NS {social_sentiment['meta'].get('totalPosts', 0):,} mention · {_fmt_eng(eng_ns.get('total', 0))} engagement"},
        {"name": "Sentiment API (HF ML)", "status": "active", "frequency": "Per batch", "readiness": "Siap", "layer": "ml", "posts": news_analyzed.get("rows_analyzed", 0), "comments": 0, "engagement": "—", "endpoint": "rmtariq/ft-Malay-bert + emotion classifier", "note": f"Mode: {news_analyzed.get('analysis_mode', '—')} · offline cache · bukan stance parti"},
        {"name": "SME Bank — Persepsi Ekonomi", "status": "active", "frequency": "90 hari crawl", "readiness": "Siap", "layer": "socmed", "posts": eco.get("economicStressPosts", 0), "comments": "—", "engagement": "—", "endpoint": "data/projects/sme/smebank/master/", "note": f"{eco.get('economicStressPosts', 0):,} posts tekanan ekonomi — proxy nasional"},
        {"name": "BNM OpenAPI — OPR & FX", "status": "active" if eco.get("officialStatus") == "active" else "pending", "frequency": "Harian", "readiness": "Siap", "layer": "official", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "GET https://api.bnm.gov.my/public/opr", "note": f"OPR {eco.get('macroContext', {}).get('opr', '—')} · pull_economic_n9.py"},
        {"name": "PRN NS News Analyze (Tier A)", "status": "active" if news_analyzed.get("rows_analyzed") else "pending", "frequency": "Harian", "readiness": "Siap", "layer": "media_tone", "posts": news_analyzed.get("posts_analyzed", 0), "comments": news_analyzed.get("comments_analyzed", 0), "engagement": "—", "endpoint": "PRN/PRN_N9/reference/prn_n9_news_analyzed_summary.json", "note": f"ML {news_analyzed.get('analysis_mode', '—')} · {news_analyzed.get('rows_analyzed', 0)} direct · neg {mt.get('neg_pct', 0)}%"},
        {"name": "PRN NS News Crawl (Komuniti)", "status": "active" if news_sum.get("total_articles") else "pending", "frequency": "Harian", "readiness": "Siap", "layer": "media_tone", "posts": news_sum.get("total_articles", 0), "comments": news_sum.get("total_comments", 0), "engagement": "—", "endpoint": "PRN/PRN_N9/reference/prn_n9_news_summary.json", "note": f"{news_sum.get('total_articles', 0)} artikel · direct {by_method.get('direct_scrape', 0)} · RSS {by_method.get('google_news_rss', 0)} · RM0"},
        {"name": "Direct Scrape — Sin Chew + Oriental", "status": "active", "layer": "media_tone", "frequency": "Harian", "readiness": "Siap", "posts": (news_sum.get("top_domains") or {}).get("orientaldaily.com.my", 0) + (news_sum.get("top_domains") or {}).get("sinchew.com.my", 0), "comments": "—", "engagement": "—", "endpoint": "PRN/PRN_N9/crawls/news/ (CrawlMethod=direct_scrape)", "note": "China Press · Sin Chew · Oriental · FMT · BH · HMetro · Utusan · MKini"},
        {"name": "Berita Cina 3 Negeri", "status": "active", "frequency": "On-demand", "readiness": "Siap", "layer": "media_tone", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "PRN/PRN_N9/crawls/chinese_news/", "note": "Google News RSS · NS + Johor + Melaka · crawl_prn_chinese_news.py"},
        {"name": "OpenDOSM — CPI N9", "status": "pending", "frequency": "Bulanan", "readiness": "Manual", "layer": "official", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "https://open.dosm.gov.my/data-catalogue/cpi_state", "note": "Belum auto-parse — masukkan manual"},
        {"name": "MIDA — Pelaburan NS", "status": "pending", "frequency": "Suku tahun", "readiness": "Manual/API", "layer": "official", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "mida.gov.my", "note": "Pending API integration"},
        {"name": "Tarikh Rasmi SPR PRN 2026", "status": "active", "frequency": "Statik", "readiness": "Siap", "layer": "static", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "PRN/_shared/spr/spr_prn_dates_2026.json", "note": f"NS penamaan {ns.get('penamaan_display')} · mengundi {ns.get('mengundi_display')} · Johor {jh.get('mengundi_display')}"},
        {"name": "War Room — Hari Ini", "status": "active", "frequency": "Per regenerate", "readiness": "Siap", "layer": "ops", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "PRN/PRN_N9/reports/war_room/n9_war_room.json", "note": "6 kerusi kritikal · WhatsApp digest · triggers media"},
        {
            "name": "InsightPulse ML — PRN N9 Ensemble",
            "status": "active" if (ml_analytics.get("predictive") or {}).get("status") == "ok" else "pending",
            "frequency": "Per regenerate",
            "readiness": ml_analytics.get("analytics_tier", "pending").title(),
            "layer": "ml",
            "posts": (ml_analytics.get("descriptive") or {}).get("seats_total", 36),
            "comments": (ml_analytics.get("descriptive") or {}).get("competitive_seats", 0),
            "engagement": "—",
            "endpoint": "PRN/PRN_N9/reports/war_room/prototype/data/n9_ml_predictions.json",
            "note": (
                f"SVM+RF+DT ensemble · RF CV "
                f"{((ml_analytics.get('predictive') or {}).get('models', {}).get('random_forest', {}).get('cv_accuracy_mean') or 0) * 100:.0f}% · "
                f"{len(ml_analytics.get('seat_predictions') or [])} DUN · "
                f"GET /api/ml/predict/prn_n9"
            ),
        },
        {
            "name": "Cina Narrative Intel (Johor proxy → NS)",
            "status": "active" if narrative_intel.get("totals") else "pending",
            "frequency": "Hybrid crawl",
            "readiness": "Siap" if narrative_intel.get("totals") else "Jalankan crawl",
            "layer": "media_tone",
            "posts": (narrative_intel.get("totals") or {}).get("records", 0),
            "comments": (narrative_intel.get("totals") or {}).get("comments", 0),
            "engagement": (narrative_intel.get("totals") or {}).get("engagement", 0),
            "endpoint": "Cina_Narative_2026/reports/cina_narrative_analytics.json",
            "note": (
                f"{(narrative_intel.get('totals') or {}).get('records', 0)} dedup · "
                f"PAS-BN {(narrative_intel.get('narrative') or {}).get('pas_bn_mentions', 0)} mention · "
                f"syurga cluster {(narrative_intel.get('narrative') or {}).get('harakat_syurga_cluster', 0)} · "
                f"{narrative_intel.get('crawl_batches', 0)} crawl batch"
            ),
        },
        {"name": "Nota Penganalisis", "status": "manual", "frequency": "Ad hoc", "readiness": "Siap", "layer": "ops", "posts": "—", "comments": "—", "engagement": "—", "endpoint": "internal://analyst-notes", "note": "Briefing EXCO & war room"},
    ]

    projection_data = {
        "bestCase": {
            "label": "Best Case PAS",
            "seats": {"PAS": 8, "Bersatu": 2, "UMNO": 6, "PH": 12, "Lain": 8},
            "summary": "PAS+PN/MN konsolidasi di LBN; PH kehilangan 3–5 kerusi marginal; majoriti tipis PH-BN.",
            "assumptions": ["PAS kekal PN di NS", "Undi Melayu swing 4%", "Turnout muda rendah bandar"],
            "risks": ["Overreach di kerusi Cina-India", "Backlash jika MN tidak stabil"],
        },
        "baseCase": {
            "label": "Base Case",
            "seats": {"PAS": 5, "Bersatu": 2, "UMNO": 8, "PH": 15, "Lain": 6},
            "summary": "PH kekal largest bloc; PN kekal ~5; pertembungan 3 penjuru di 6 kerusi; status quo hampir kekal.",
            "assumptions": ["Split HQ tidak ubah lapangan NS", "Turnout sederhana", "BN bertanding sendiri", f"Tekanan ekonomi persepsi {eco.get('sentiment', {}).get('negativePct', 0)}% (SME crawl)"],
            "risks": ["Kerusi N05/N25 jadi medan utama", "Naratif MB overshadow PRN"],
        },
        "worstCase": {
            "label": "Worst Case PAS",
            "seats": {"PAS": 3, "Bersatu": 1, "UMNO": 10, "PH": 18, "Lain": 4},
            "summary": "PAS solo gagal; pecah undi PN; PH+BN stabil; PN tinggal 3–4 kerusi.",
            "assumptions": ["PAS solo di 8+ kerusi", "Bersatu bertanding bertentangan", "PH mobilisasi bandar"],
            "risks": ["Kehilangan N20/N34", "Naratif kegagalan leadership"],
        },
        "swingImpacts": [
            {"scenario": "Clash PAS–Bersatu", "pasDelta": -2, "pnDelta": -3, "phDelta": 2, "note": "Pecah undi Melayu di 4 kerusi PN sedia ada"},
            {"scenario": "PAS–UMNO kerjasama", "pasDelta": 3, "pnDelta": 2, "phDelta": -4, "note": "Swing FELDA/LBN; PH terancam N05–N08"},
            {"scenario": "Straight fights 3 penjuru", "pasDelta": 1, "pnDelta": -1, "phDelta": 1, "note": "Keputusan sukar di 6 kerusi marginal"},
        ],
        "recommendations": {
            "monitorWeek": [
                f"Penamaan NS {ns.get('penamaan_display', '18 Jul')} ({days_nom_s} hari)",
                "Kemaskini calon & URL socmed post-penamaan",
                "Isyarat calon PAS vs PN — logo & kerusi",
                f"Countdown mengundi {ns.get('mengundi_display', '1 Ogo')} ({days_poll_s} hari)",
            ],
            "crawlerPriority": ["ADUN seed list (73)", "Hashtag #PRNNS #NegeriSembilan", "Refresh SME ekonomi crawl suku tahunan"],
            "deepMonitoring": ["N05 Serting", "N25 Paroi", "N01 Palong", "N13 Sikamat", "N21 Seremban Jaya"],
        },
    }

    rankings = {
        "pertahan": [s for s in seats if s["party2023"] == "PAS"],
        "sasaran": [s for s in seats if s["pasInterest"] == "Sasaran"][:8],
        "risiko": [s for s in seats if s["threeCornerRisk"] == "Tinggi"],
    }

    by_comm = news_sum.get("by_community") or {}
    comm_labels = news_sum.get("community_labels") or {
        "melayu": "Komuniti Melayu", "islam": "Islam / PAS / Harakah", "cina": "Komuniti Cina",
        "india": "Komuniti India / Tamil", "lain": "Lain-lain", "ekonomi": "Ekonomi", "umum": "Umum / PRN",
    }
    community_news = {
        "fetchedAt": news_sum.get("fetched_at"),
        "analyzedAt": news_analyzed.get("analyzed_at"),
        "total": news_sum.get("total_articles") or news_sum.get("total") or 0,
        "totalComments": news_sum.get("total_comments") or 0,
        "rowsAnalyzed": news_analyzed.get("rows_analyzed") or 0,
        "rowsSkipped": news_analyzed.get("rows_skipped") or 0,
        "byCommunity": by_comm,
        "byMethod": news_sum.get("by_crawl_method") or {},
        "labels": comm_labels,
        "directSources": news_sum.get("direct_sources") or [],
        "commentSources": news_sum.get("comment_sources") or [],
        "cost": news_sum.get("cost", "RM0 — Google News RSS percuma"),
        "note": news_analyzed.get("layer_note") or news_sum.get("note", ""),
        "headlines": news_sum.get("community_headlines") or {},
        "topDomains": news_sum.get("top_domains") or {},
        "mediaTone": news_analyzed.get("media_tone") or {},
        "publicVoice": news_analyzed.get("public_voice") or {},
        "communitySentiment": news_analyzed.get("by_community") or {},
        "narrativeAlerts": news_analyzed.get("narrative_alerts") or [],
        "topNegative": news_analyzed.get("top_negative") or [],
        "topPositive": news_analyzed.get("top_positive") or [],
    }

    return {
        "coalitionScenarios": coalition_scenarios,
        "coalitionWatch": coalition_watch,
        "constituencyProfiles": constituency_profiles,
        "socialSentiment": social_sentiment,
        "communityNews": community_news,
        "projectionData": projection_data,
        "dataSources": data_sources,
        "hybridModel": hybrid_model,
        "economicOutlook": economic_outlook,
        "dpiUpdates": dpi_updates,
        "rankings": rankings,
        "mlAnalytics": ml_analytics,
        "narrativeIntel": narrative_intel,
    }


def party_color(party, winner):
    pmap = {"PAS": "#1a7f5a", "Bersatu": "#1e4fa8", "UMNO": "#c8102e", "DAP": "#e84393", "PKR": "#3b82f6", "Amanah": "#f59e0b"}
    wmap = {"PH": "#e84393", "BN": "#c8102e", "PN": "#1a7f5a"}
    return pmap.get(party, wmap.get(winner, "#64748b"))


def generate_html(seats, mock, pas, analytics, adun_social, war_room, prn_dates):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    dpi_updates = mock.get("dpiUpdates") or load_dpi_updates()
    dpi_meta = dpi_updates.get("meta", {})
    ns = prn_dates.get("negeri_sembilan", {})
    jh = prn_dates.get("johor", {})
    days_poll = days_until(ns.get("mengundi"))
    days_nom = days_until(ns.get("penamaan"))
    days_poll_s = str(days_poll) if days_poll is not None else "—"
    days_nom_s = str(days_nom) if days_nom is not None else "—"
    prn_dates_json = json.dumps(prn_dates, ensure_ascii=False, indent=2)
    seats_json = json.dumps(seats, ensure_ascii=False, indent=2)
    analytics_json = json.dumps(analytics, ensure_ascii=False, indent=2)
    adun_social_json = json.dumps(adun_social, ensure_ascii=False, indent=2)
    war_room_json = json.dumps(war_room, ensure_ascii=False, indent=2)
    war_room_js = WAR_ROOM_JS.read_text(encoding="utf-8") if WAR_ROOM_JS.exists() else ""
    mock_blocks = {k: json.dumps(v, ensure_ascii=False, indent=2) for k, v in mock.items() if k != "rankings"}
    eco = mock.get("economicOutlook", {})
    eco_note = f"{eco.get('economicStressPosts', 0):,} posts tekanan ekonomi —"

    html = f"""<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PRN Negeri Sembilan 2026 — Intelligence Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<style>
:root {{
  --bg:#0b0d12; --surface:#141820; --surface-2:#1c2230; --border:rgba(255,255,255,.08);
  --text:#e8eaf0; --muted:#8b90a7; --accent:#3b82f6; --gold:#d4a853;
  --pas:#1a7f5a; --bn:#c8102e; --ph:#e84393; --pn:#1e4fa8;
  --pos:#22c55e; --neg:#ef4444; --warn:#f59e0b; --sidebar:260px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:14px;line-height:1.5}}
h1,h2,h3,.display{{font-family:'Instrument Serif',Georgia,serif;font-weight:400}}
.app{{display:flex;min-height:100vh}}
.sidebar{{width:var(--sidebar);min-width:var(--sidebar);background:var(--surface);border-right:1px solid var(--border);position:fixed;inset:0 auto 0 0;z-index:200;display:flex;flex-direction:column;padding:20px 14px}}
.logo{{margin-bottom:24px;padding:0 6px}}
.logo h2{{font-size:22px;line-height:1.15}}
.logo p{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-top:4px}}
.nav{{flex:1;display:flex;flex-direction:column;gap:3px}}
.nav-item{{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;color:var(--muted);font-size:13px;font-weight:500;cursor:pointer;border:none;background:none;width:100%;text-align:left;transition:.15s}}
.nav-item:hover,.nav-item.active{{background:var(--surface-2);color:var(--text)}}
.nav-item.active{{border-left:3px solid var(--gold);padding-left:9px}}
.nav-item svg{{width:18px;height:18px;flex-shrink:0}}
.sidebar-foot{{border-top:1px solid var(--border);padding-top:14px;font-size:11px;color:var(--muted)}}
.main{{margin-left:var(--sidebar);flex:1;display:flex;flex-direction:column;min-height:100vh}}
.topbar{{position:sticky;top:0;z-index:100;background:rgba(20,24,32,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:16px 24px}}
.topbar-row{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}}
.topbar h1{{font-size:26px}}
.topbar-meta{{font-size:12px;color:var(--muted);margin-top:4px}}
.alert-banner{{margin-top:12px;padding:10px 14px;border-radius:8px;background:rgba(212,168,83,.12);border:1px solid rgba(212,168,83,.35);font-size:12px;display:flex;align-items:center;gap:8px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.chip{{padding:5px 12px;border-radius:999px;border:1px solid var(--border);font-size:11px;color:var(--muted);cursor:pointer;background:var(--surface-2)}}
.chip.active{{border-color:var(--accent);color:var(--text);background:rgba(59,130,246,.15)}}
.topbar-actions{{display:flex;gap:8px;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:600;border:1px solid var(--border);background:var(--surface-2);color:var(--text);cursor:pointer}}
.btn-primary{{background:var(--accent);border-color:var(--accent);color:#fff}}
.btn:hover{{filter:brightness(1.08)}}
.badge{{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:999px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}}
.badge-live{{background:rgba(34,197,94,.15);color:var(--pos)}}
.badge-pending{{background:rgba(245,158,11,.15);color:var(--warn)}}
.badge-risk{{background:rgba(239,68,68,.15);color:var(--neg)}}
.content{{padding:24px;flex:1}}
.section{{display:none;animation:fade .25s ease}}
.section.active{{display:block}}
@keyframes fade{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}}
.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}}
.grid-2{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:20px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px;box-shadow:0 4px 24px rgba(0,0,0,.25)}}
.card-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}}
.card-value{{font-size:28px;font-weight:700;letter-spacing:-.02em}}
.card-sub{{font-size:12px;color:var(--muted);margin-top:6px}}
.section-title{{font-size:20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.section-title span{{font-size:12px;color:var(--muted);font-family:'Inter',sans-serif}}
.sticky-sub{{position:sticky;top:0;z-index:20;background:var(--bg);padding:12px 0;margin-bottom:16px;border-bottom:1px solid var(--border)}}
.skip-link{{position:absolute;left:-9999px;top:auto}}
.skip-link:focus{{left:16px;top:16px;z-index:9999;padding:8px 12px;background:var(--accent);color:#fff;border-radius:8px}}
.nav-item:focus-visible,.tab:focus-visible,.btn:focus-visible,.seat-tile:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.timeline{{display:flex;gap:0;overflow-x:auto;padding:8px 0 16px;margin-bottom:20px}}
.tl-item{{flex:1;min-width:120px;position:relative;padding:0 12px 0 0}}
.tl-item:not(:last-child)::after{{content:'';position:absolute;top:14px;left:calc(100% - 12px);width:24px;height:2px;background:var(--border)}}
.tl-dot{{width:28px;height:28px;border-radius:50%;background:var(--surface-2);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;margin-bottom:8px}}
.tl-dot.done{{border-color:var(--pas);background:rgba(26,127,90,.2)}}
.tl-dot.current{{border-color:var(--gold);background:rgba(212,168,83,.2);box-shadow:0 0 0 4px rgba(212,168,83,.15)}}
.tl-dot.future{{opacity:.6}}
.tl-label{{font-size:11px;font-weight:600}}
.tl-date{{font-size:10px;color:var(--muted)}}
.coalition-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.coal-card{{position:relative;overflow:hidden}}
.coal-card .prob-bar{{height:6px;background:var(--surface-2);border-radius:999px;margin:10px 0;overflow:hidden}}
.coal-card .prob-fill{{height:100%;background:linear-gradient(90deg,var(--gold),var(--accent));border-radius:999px}}
.coal-card .row{{display:flex;justify-content:space-between;font-size:11px;margin-top:6px}}
.coal-card .up{{color:var(--pos)}} .coal-card .dn{{color:var(--neg)}}
.toolbar{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px;align-items:center}}
.toolbar input,.toolbar select{{padding:8px 12px;border-radius:8px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);font-size:13px}}
.table-wrap{{overflow-x:auto;border-radius:12px;border:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border)}}
th{{background:var(--surface-2);color:var(--muted);font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.04em;cursor:pointer;user-select:none;position:sticky;top:0}}
tr:hover td{{background:rgba(255,255,255,.02)}}
.pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600}}
.seat-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:20px}}
.seat-tile{{aspect-ratio:1;border-radius:8px;border:1px solid var(--border);display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:10px;font-weight:700;cursor:pointer;transition:.15s;position:relative}}
.seat-tile:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.35);z-index:5}}
.seat-tile .code{{font-size:12px}}
.seat-tile .maj{{font-size:9px;color:var(--muted);font-weight:500}}
.tooltip{{position:fixed;z-index:9999;max-width:260px;padding:10px 12px;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;font-size:11px;pointer-events:none;opacity:0;transition:opacity .12s;box-shadow:0 12px 32px rgba(0,0,0,.5)}}
.tooltip.show{{opacity:1}}
.tabs{{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:16px;flex-wrap:wrap}}
.tab{{padding:10px 16px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}}
.tab.active{{color:var(--text);border-bottom-color:var(--accent)}}
.tab-panel{{display:none}} .tab-panel.active{{display:block}}
.chart-box{{position:relative;height:280px}}
.chart-box.sm{{height:220px}}
.scenario-matrix{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}
.scenario-card{{border-top:3px solid var(--gold)}}
.scenario-card h4{{font-size:14px;margin-bottom:8px}}
.scenario-card ul{{list-style:none;font-size:11px;color:var(--muted)}}
.scenario-card li{{margin-bottom:4px}}
.note-cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.note-card{{border-left:3px solid var(--accent)}}
.profile-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
.profile-card h4{{font-size:15px;margin-bottom:10px}}
.profile-card dl{{display:grid;grid-template-columns:120px 1fr;gap:6px 10px;font-size:12px}}
.profile-card dt{{color:var(--muted)}}
.rank-list{{list-style:none}}
.rank-list li{{padding:8px 0;border-bottom:1px solid var(--border);font-size:12px;display:flex;justify-content:space-between;gap:8px}}
.map-placeholder{{min-height:240px;background:linear-gradient(135deg,var(--surface-2),var(--surface));border:1px dashed var(--border);border-radius:12px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;text-align:center;padding:24px}}
.source-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
.source-card{{display:flex;flex-direction:column;gap:8px}}
.source-card.hybrid-layer{{border:1px solid var(--gold);background:linear-gradient(135deg,rgba(212,175,55,.08),transparent)}}
.source-card .endpoint{{font-family:monospace;font-size:10px;color:var(--accent);word-break:break-all}}
.source-metrics{{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px}}
.source-metrics span{{font-size:10px;padding:2px 8px;border-radius:999px;background:var(--surface-2);border:1px solid var(--border);color:var(--muted)}}
.source-metrics span strong{{color:var(--text)}}
.hybrid-banner{{margin-bottom:20px;padding:16px;border-radius:12px;border:1px solid var(--gold);background:linear-gradient(135deg,rgba(26,127,90,.12),rgba(212,175,55,.08))}}
.hybrid-layers{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}}
.hybrid-layer-card{{padding:12px;border-radius:10px;background:var(--surface-2);border:1px solid var(--border)}}
.hybrid-layer-card h4{{font-size:13px;margin-bottom:6px}}
.hybrid-totals{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px;font-size:11px;color:var(--muted)}}
.trust-strip{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px}}
.trust-item{{padding:12px;border-radius:10px;background:var(--surface-2);border:1px solid var(--border);text-align:center}}
.trust-item i{{width:18px;height:18px;color:var(--gold);margin-bottom:6px}}
.trust-item strong{{display:block;font-size:11px;margin-bottom:2px}}
.trust-item span{{font-size:10px;color:var(--muted)}}
.exec-briefing{{margin-bottom:16px;padding:20px 22px;border-radius:14px;border:1px solid var(--gold);background:linear-gradient(135deg,rgba(26,127,90,.15),rgba(212,175,55,.1),transparent);position:relative;overflow:hidden}}
.exec-briefing::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--pas),var(--gold),var(--accent))}}
.exec-briefing h3{{font-size:18px;margin-bottom:6px;line-height:1.35}}
.exec-briefing .exec-sub{{font-size:12px;color:var(--muted);margin-bottom:14px}}
.insight-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}
.insight-card{{padding:12px 14px;border-radius:10px;background:rgba(0,0,0,.2);border:1px solid var(--border);border-left:3px solid var(--accent)}}
.insight-card.sev-high{{border-left-color:var(--neg)}}
.insight-card.sev-info{{border-left-color:var(--pos)}}
.insight-card.sev-neutral{{border-left-color:var(--gold)}}
.insight-card strong{{display:block;font-size:12px;margin-bottom:4px}}
.insight-card p{{font-size:11px;color:var(--muted);line-height:1.45;margin:0}}
.hybrid-layer-card.enhanced{{padding:14px;position:relative}}
.hybrid-layer-card .layer-head{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.hybrid-layer-card .layer-tier{{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:999px;background:rgba(212,175,55,.15);color:var(--gold);border:1px solid rgba(212,175,55,.3)}}
.hybrid-layer-card .layer-status{{font-size:9px;font-weight:700;padding:2px 7px;border-radius:999px}}
.layer-status.verified,.layer-status.live{{background:rgba(34,197,94,.15);color:var(--pos)}}
.layer-status.pending{{background:rgba(245,158,11,.15);color:var(--warn)}}
.layer-status.fallback{{background:rgba(100,116,139,.15);color:#94a3b8}}
.layer-big-num{{font-size:32px;font-weight:800;letter-spacing:-.03em;line-height:1;margin:8px 0 4px;font-variant-numeric:tabular-nums}}
.layer-sent-bar{{height:6px;border-radius:999px;background:var(--surface);overflow:hidden;display:flex;margin:8px 0}}
.layer-sent-bar .pos{{background:var(--pos)}} .layer-sent-bar .neu{{background:#64748b}} .layer-sent-bar .neg{{background:var(--neg)}}
.quality-track{{height:4px;background:var(--surface);border-radius:999px;margin-top:8px;overflow:hidden}}
.quality-fill{{height:100%;background:linear-gradient(90deg,var(--pas),var(--gold));border-radius:999px;transition:width 1.2s ease}}
.methodology-box{{margin-top:16px;padding:14px;border-radius:10px;background:var(--surface-2);border:1px dashed var(--border)}}
.methodology-box ul{{margin:8px 0 0;padding-left:18px;font-size:11px;color:var(--muted);line-height:1.6}}
.count-up{{font-variant-numeric:tabular-nums}}
.drawer-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:500;opacity:0;visibility:hidden;transition:.2s}}
.drawer-overlay.open{{opacity:1;visibility:visible}}
.drawer{{position:fixed;top:0;right:0;width:min(420px,92vw);height:100%;background:var(--surface);border-left:1px solid var(--border);z-index:501;transform:translateX(100%);transition:.25s;padding:24px;overflow-y:auto}}
.drawer-overlay.open .drawer{{transform:none}}
.drawer h3{{font-size:22px;margin-bottom:4px}}
.drawer-close{{position:absolute;top:16px;right:16px;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer}}
.narrative-cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}
.narr-card{{border-top:3px solid var(--ph)}}
.eco-hybrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}}
.eco-col{{border-top:3px solid var(--accent)}}
.eco-col.official{{border-top-color:var(--gold);opacity:.92}}
.eco-issue{{display:flex;justify-content:space-between;font-size:12px;padding:6px 0;border-bottom:1px solid var(--border)}}
.eco-headline{{font-size:11px;color:var(--muted);padding:8px 0;border-bottom:1px solid var(--border);line-height:1.45}}
.cat-pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.03em}}
.cat-defend{{background:rgba(26,127,90,.2);color:#4ade80}}
.cat-winnable{{background:rgba(59,130,246,.2);color:#93c5fd}}
.cat-tough{{background:rgba(245,158,11,.2);color:#fbbf24}}
.cat-not_priority{{background:rgba(100,116,139,.2);color:#94a3b8}}
.pred-bar{{height:6px;background:var(--surface-2);border-radius:999px;overflow:hidden;margin-top:4px}}
.pred-fill{{height:100%;background:linear-gradient(90deg,var(--pas),var(--accent));border-radius:999px}}
.analytics-table td{{font-size:11px}}
.tabular{{font-variant-numeric:tabular-nums}}
.se-root .se-facts-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px}}
.se-fact-card{{border-left:3px solid var(--gold);padding:14px}}
.se-filter-tabs{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}}
.se-filter-tabs .se-filter-tab{{cursor:pointer;border:none;background:var(--surface-2)}}
.se-filter-tabs .se-filter-tab.active{{border-color:var(--gold);color:var(--text);background:rgba(212,168,83,.12)}}
.se-cards-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:16px}}
.se-scenario-card{{cursor:pointer;transition:border-color .15s,box-shadow .15s;border-top:2px solid var(--border)}}
.se-scenario-card:hover,.se-scenario-card.se-card-selected{{border-color:var(--gold);box-shadow:0 0 0 1px rgba(212,168,83,.25)}}
.se-card-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.se-code{{font-family:monospace;font-size:12px;font-weight:700;color:var(--gold)}}
.se-card-title{{font-size:14px;font-weight:600;line-height:1.35;margin-bottom:10px}}
.se-metrics-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:11px}}
.se-list-cols{{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:11px}}
.se-list-cols ul{{margin:4px 0 0;padding-left:16px;color:var(--muted);line-height:1.45}}
.se-chips{{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}}
.se-chips .chip{{font-size:10px;padding:3px 8px}}
.se-matrix-wrap{{overflow-x:auto;margin-bottom:16px}}
.se-matrix{{font-size:11px;min-width:720px}}
.se-matrix th{{white-space:nowrap}}
.heat-cell{{text-align:center;font-variant-numeric:tabular-nums;font-weight:600}}
.heat-low{{background:rgba(100,116,139,.15)}}
.heat-mid{{background:rgba(245,158,11,.18)}}
.heat-high{{background:rgba(239,68,68,.2)}}
.heat-good{{background:rgba(34,197,94,.18)}}
.se-row-selected td{{outline:1px solid var(--gold)}}
.se-transition{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--border);font-size:11px}}
.se-trigger{{color:var(--muted);flex:1;min-width:180px}}
.se-monitor-item{{padding:10px 0;border-bottom:1px solid var(--border)}}
.se-importance{{font-size:10px;color:var(--gold);letter-spacing:2px;margin-top:4px}}
.se-why-list{{margin:10px 0 0;padding-left:18px;font-size:13px;color:var(--muted);line-height:1.65}}
.se-summary-card{{border-top:2px solid var(--pas)}}
.se-summary-risk{{border-top-color:var(--neg)}}
.wr-action-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px}}
.wr-action-card{{border-top:3px solid var(--border)}}
.wr-type-digital{{border-top-color:var(--accent)}}
.wr-type-lapangan{{border-top-color:var(--pas)}}
.wr-type-komunikasi{{border-top-color:var(--gold)}}
.wr-type-intel{{border-top-color:#a78bfa}}
.wr-card-defend{{border-top:2px solid #4ade80}}
.wr-card-winnable{{border-top:2px solid var(--accent)}}
.wr-card-tough{{border-top:2px solid var(--warn)}}
.wr-tabs{{margin-top:8px}}
.wr-hari-ini-list{{display:flex;flex-direction:column;gap:10px}}
.wr-hari-row{{display:flex;gap:14px;align-items:flex-start;cursor:pointer;transition:.15s;border-left:3px solid var(--border)}}
.wr-hari-row.wr-row-done{{opacity:.65;border-left-color:var(--pas)}}
.wr-hari-row input{{width:20px;height:20px;margin-top:4px;flex-shrink:0;accent-color:var(--pas)}}
.wr-hari-body{{flex:1;min-width:0}}
.wr-hari-head{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:6px}}
.wr-hari-action{{font-size:13px;line-height:1.5;margin-bottom:6px}}
.wr-hari-meta{{font-size:10px;color:var(--muted)}}
.wr-module-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
.wr-module-chip{{display:flex;align-items:center;gap:6px;padding:8px 10px;border-radius:8px;background:var(--surface-2);border:1px solid var(--border);font-size:10px;line-height:1.3}}
.ml-tier{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}}
.ml-tier-pred{{background:rgba(59,130,246,.2);color:#93c5fd;border:1px solid rgba(59,130,246,.4)}}
.ml-tier-desc{{background:rgba(148,163,184,.15);color:#cbd5e1}}
.ml-tier-presc{{background:rgba(212,168,83,.15);color:var(--gold);border:1px solid rgba(212,168,83,.35)}}
.ml-model-row{{display:flex;flex-wrap:wrap;gap:12px;padding:8px 0;border-bottom:1px solid var(--border);font-size:12px}}
.ml-model-name{{font-weight:600;min-width:120px}}
.ml-comp-high{{color:var(--warn);font-weight:600}}
.ml-comp-mid{{color:var(--accent)}}
.wr-mod-ready{{border-color:rgba(34,197,94,.35)}}
.wr-mod-partial{{border-color:rgba(245,158,11,.35)}}
.wr-mod-planned{{opacity:.75}}
.wr-mod-label{{flex:1}}
@media(max-width:1200px){{.wr-module-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:768px){{.wr-module-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:768px){{.wr-action-grid{{grid-template-columns:1fr}}}}
@media print{{
  .sidebar,.topbar-actions,.menu-toggle,.filterChips,.drawer-overlay,.chip{{display:none!important}}
  .trust-strip{{grid-template-columns:repeat(3,1fr)}}
  .insight-grid{{grid-template-columns:1fr}}
  .main{{margin-left:0!important}}
  .se-cards-grid{{grid-template-columns:1fr 1fr}}
  .chart-box{{height:180px!important}}
}}
@media(max-width:1200px){{.grid-4,.coalition-grid,.scenario-matrix,.narrative-cards,.eco-hybrid,.se-facts-grid,.se-cards-grid,.trust-strip{{grid-template-columns:repeat(2,1fr)}}.seat-grid{{grid-template-columns:repeat(4,1fr)}}}}
@media(max-width:768px){{
  .sidebar{{transform:translateX(-100%);transition:.25s}} .sidebar.open{{transform:none}}
  .main{{margin-left:0}} .grid-4,.grid-3,.grid-2,.coalition-grid,.scenario-matrix,.profile-grid,.source-grid,.note-cards,.narrative-cards,.eco-hybrid,.se-facts-grid,.se-cards-grid{{grid-template-columns:1fr}}
  .seat-grid{{grid-template-columns:repeat(3,1fr)}} .menu-toggle{{display:inline-flex}}
}}
.menu-toggle{{display:none}}
</style>
</head>
<body>
<a class="skip-link" href="#mainContent">Langkau ke kandungan</a>
<div class="app">
<aside class="sidebar" id="sidebar" aria-label="Navigasi utama">
  <div class="logo">
    <h2 class="display">PRN Negeri Sembilan</h2>
    <p>Intelligence Dashboard 2026</p>
  </div>
  <nav class="nav" id="mainNav" role="navigation" aria-label="Seksyen dashboard"></nav>
  <div class="sidebar-foot">
    <div>InsightPulse · War Room</div>
    <div style="margin-top:6px">DUN 36 kerusi · Majoriti 19</div>
  </div>
</aside>
<div class="main">
  <header class="topbar">
    <div class="topbar-row">
      <div>
        <button class="btn menu-toggle" id="menuToggle" aria-label="Menu"><i data-lucide="menu"></i></button>
        <h1 class="display" id="pageTitle">Gambaran Keseluruhan</h1>
        <div class="topbar-meta">PRN Negeri Sembilan 2026 · Briefing dalaman · <span id="lastUpdated">{ts}</span> · <span id="crawlMeta">Socmed master — loading…</span></div>
      </div>
      <div class="topbar-actions">
        <span class="badge badge-live"><i data-lucide="activity" style="width:12px;height:12px"></i> SPR 12 Jun — NS mengundi {ns.get('mengundi_display', '1 Ogo 2026')}</span>
        <button class="btn" onclick="exportMock('csv')"><i data-lucide="download"></i> CSV</button>
        <button class="btn" onclick="exportMock('png')"><i data-lucide="image"></i> PNG</button>
        <button class="btn" onclick="exportMock('pdf')"><i data-lucide="file-text"></i> PDF</button>
      </div>
    </div>
    <div class="alert-banner" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.35)">
      <i data-lucide="calendar-check" style="width:16px;height:16px;color:var(--pos)"></i>
      <span><strong>Keputusan SPR 12 Jun 2026.</strong> PRN Negeri Sembilan: penamaan <strong>{ns.get('penamaan_display', '18 Jul')}</strong> · undi awal <strong>{ns.get('undi_awal_display', '28 Jul')}</strong> · mengundi <strong>{ns.get('mengundi_display', '1 Ogo 2026')}</strong> ({days_poll_s} hari lagi). Johor mengundi {jh.get('mengundi_display', '11 Jul')}.</span>
    </div>
    <div class="chips" id="filterChips">
      <span class="chip active" data-filter="all">Semua Blok</span>
      <span class="chip" data-filter="PH">PH (17)</span>
      <span class="chip" data-filter="BN">BN (14)</span>
      <span class="chip" data-filter="PN">PN (5)</span>
    </div>
  </header>
  <main class="content" id="mainContent" role="main" tabindex="-1"></main>
</div>
</div>
<div class="tooltip" id="tooltip"></div>
<div class="drawer-overlay" id="drawerOverlay">
  <div class="drawer" id="drawer" role="dialog" aria-modal="true">
    <button class="drawer-close" id="drawerClose" aria-label="Tutup"><i data-lucide="x"></i></button>
    <div id="drawerBody"></div>
  </div>
</div>
<script>
// ═══════════════════════════════════════════════════════════════
// MOCK DATA — ganti dengan API live apabila crawler sedia
// ═══════════════════════════════════════════════════════════════

// REPLACE WITH API: /api/prn/n9/seats
const seatData = {seats_json};

// REPLACE WITH API: /api/prn/n9/seat-analytics
const seatAnalytics = {analytics_json};

// REPLACE WITH API: /api/prn/n9/adun-social
const adunSocialCrawl = {adun_social_json};

// REPLACE WITH API: /api/prn/n9/coalition-scenarios
const coalitionScenarios = {mock_blocks['coalitionScenarios']};

// REPLACE WITH API: /api/prn/n9/coalition-watch
const coalitionWatch = {mock_blocks['coalitionWatch']};

// REPLACE WITH API: /api/prn/n9/sentiment
const socialSentiment = {mock_blocks['socialSentiment']};

// REPLACE WITH API: /api/prn/n9/community-news
const communityNews = {mock_blocks['communityNews']};

// REPLACE WITH API: /api/prn/n9/constituencies
const constituencyProfiles = {mock_blocks['constituencyProfiles']};

// REPLACE WITH API: /api/prn/n9/projections
const projectionData = {mock_blocks['projectionData']};

// REPLACE WITH API: /api/prn/n9/economic-outlook
const economicOutlook = {mock_blocks['economicOutlook']};

// REPLACE WITH API: /api/prn/n9/data-sources
const dataSources = {mock_blocks['dataSources']};
const hybridModel = {mock_blocks['hybridModel']};
// REPLACE WITH API: /api/prn/n9/dpi-updates
const dpiUpdates = {mock_blocks['dpiUpdates']};
const mlAnalytics = {mock_blocks['mlAnalytics']};
const narrativeIntel = {mock_blocks['narrativeIntel']};

// War Room — playbook, triggers, briefing, agent queue (Fasa A–E)
const warRoomData = {war_room_json};

// Tarikh rasmi SPR — reference/spr_prn_dates_2026.json
const prnDates = {prn_dates_json};

const META = {{
  totalSeats: 36, majority: 19,
  baseline2023: {{ PH: 17, BN: 14, PN: 5 }},
  prnStatus: "Tarikh SPR disahkan — kempen pre-penamaan",
  prnNS: prnDates.negeri_sembilan || {{}},
  prnJohor: prnDates.johor || {{}},
  daysToPolling: {days_poll if days_poll is not None else 'null'},
  daysToNomination: {days_nom if days_nom is not None else 'null'},
  dpiAsOf: "{dpi_meta.get('dpiAsOf', 'DPI Dec 2025')}",
  rankingAsOf: "{dpi_meta.get('rankingAsOf', '10 Jun 2026')}",
  lastUpdated: "{ts}"
}};

const NAV = [
  {{ id: 'overview', label: 'Gambaran Keseluruhan', icon: 'layout-dashboard' }},
  {{ id: 'seats', label: 'Kerusi DUN', icon: 'grid-3x3' }},
  {{ id: 'analitik', label: 'Analitik & Ramalan', icon: 'bar-chart-2' }},
  {{ id: 'ml-insight', label: 'ML & InsightPulse', icon: 'brain' }},
  {{ id: 'dpi-jentera', label: 'DPI & Jentera', icon: 'users' }},
  {{ id: 'war-room', label: 'Hari Ini', icon: 'calendar-check' }},
  {{ id: 'scenario-engine', label: 'Scenario Engine', icon: 'cpu' }},
  {{ id: 'scenarios', label: 'Senario Pakatan', icon: 'git-branch' }},
  {{ id: 'sentiment', label: 'Sentimen & Naratif', icon: 'message-square' }},
  {{ id: 'profiles', label: 'Profil Kawasan', icon: 'map-pin' }},
  {{ id: 'projections', label: 'Unjuran PRN', icon: 'trending-up' }},
  {{ id: 'sources', label: 'Data & Sumber', icon: 'database' }}
];

const PARTY_COLORS = {{ PH:'#e84393', BN:'#c8102e', PN:'#1a7f5a', PAS:'#1a7f5a', Bersatu:'#1e4fa8', UMNO:'#c8102e', DAP:'#e84393', PKR:'#3b82f6', Amanah:'#f59e0b' }};

let charts = {{}};
let activeSection = 'overview';
let seatSort = {{ key: 'code', asc: true }};
let seatFilter = {{ search: '', bloc: 'all', party: 'all', kategoriPas: 'all' }};

function catClass(k) {{
  return 'cat-' + (k || 'not_priority');
}}

function catLabel(k) {{
  return {{ defend:'Pertahan', winnable:'Boleh Menang', tough:'Sukar', not_priority:'Bukan Fokus' }}[k] || k;
}}

// ─── Render helpers ───
function el(tag, cls, html) {{
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}}

function pct(n, t) {{ return t ? Math.round(n / t * 100) : 0; }}

function mlPct(v) {{
  if (v == null || v === '') return '—';
  return Math.round(Number(v) * 100) + '%';
}}

function mlTierBadge(tier) {{
  const map = {{ descriptive: ['ml-tier-desc','Descriptive'], predictive: ['ml-tier-pred','Predictive'], prescriptive: ['ml-tier-presc','Prescriptive'] }};
  const [cls, label] = map[tier] || map.descriptive;
  return `<span class="ml-tier ${{cls}}">${{label}}</span>`;
}}

function blocOf(seat) {{
  const p = seat.party2023;
  if (['PAS','Bersatu'].includes(p)) return 'PN';
  if (['UMNO','MCA','MIC'].includes(p) || seat.winner2023 === 'BN') return 'BN';
  return 'PH';
}}

function renderNav() {{
  const nav = document.getElementById('mainNav');
  nav.innerHTML = NAV.map(n => `
    <button class="nav-item${{n.id===activeSection?' active':''}}" data-section="${{n.id}}">
      <i data-lucide="${{n.icon}}"></i> ${{n.label}}
    </button>`).join('');
  nav.querySelectorAll('.nav-item').forEach(btn => {{
    btn.addEventListener('click', () => switchSection(btn.dataset.section));
  }});
  lucide.createIcons();
}}

function switchSection(id) {{
  activeSection = id;
  const item = NAV.find(n => n.id === id);
  document.getElementById('pageTitle').textContent = item.label;
  renderNav();
  renderSection();
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

function renderSection() {{
  const c = document.getElementById('mainContent');
  Object.values(charts).forEach(ch => ch.destroy && ch.destroy());
  charts = {{}};
  const fns = {{ overview: renderOverview, seats: renderSeats, analitik: renderAnalitik, 'ml-insight': renderMlInsight, 'dpi-jentera': renderDpiJentera, 'war-room': renderWarRoom, 'scenario-engine': renderScenarioEngine, scenarios: renderScenarios, sentiment: renderSentiment, profiles: renderProfiles, projections: renderProjections, sources: renderSources }};
  c.innerHTML = '';
  const sec = el('section', 'section active');
  sec.id = 'sec-' + activeSection;
  sec.setAttribute('aria-labelledby', 'pageTitle');
  c.appendChild(sec);  // must be in DOM before getElementById inside render fns
  fns[activeSection](sec);
  lucide.createIcons();
}}

function renderOverview(root) {{
  const sm = socialSentiment.meta || {{}};
  const engG = sm.engagementGlobal || {{}};
  const crawled = sm.totalPostsCrawled || sm.masterTotal || 68256;
  root.innerHTML = `
    <div class="grid-3" style="margin-bottom:12px">
      <div class="card" style="border-color:var(--gold);background:linear-gradient(135deg,rgba(212,175,55,.1),transparent)">
        <div class="card-label">Total Posts Crawled</div>
        <div class="card-value">${{crawled.toLocaleString()}}</div>
        <div class="card-sub">${{engG.postRows?.toLocaleString?.() || '—'}} post rows · ${{engG.commentRows?.toLocaleString?.() || '—'}} komen rows · master minggu lepas</div>
      </div>
      <div class="card">
        <div class="card-label">Engagement</div>
        <div class="card-value">${{fmtEng(engG.total)}}</div>
        <div class="card-sub">FB · TikTok · X · News · 6 platform</div>
      </div>
      <div class="card">
        <div class="card-label">PRN Broad (keyword)</div>
        <div class="card-value">${{sm.prnMentions || '—'}}</div>
        <div class="card-sub">Semua negeri PRN · filter luas</div>
      </div>
    </div>
    <div class="grid-4">
      <div class="card"><div class="card-label">Jumlah Kerusi DUN</div><div class="card-value">${{META.totalSeats}}</div><div class="card-sub">N01 – N36</div></div>
      <div class="card"><div class="card-label">Pengundi NS (DPI)</div><div class="card-value">${{seatData.reduce((a,s)=>a+(s.registeredVotersDpi||0),0).toLocaleString()}}</div><div class="card-sub">${{META.dpiAsOf || 'Dec 2025'}}</div></div>
      <div class="card"><div class="card-label">Cula PAS #1</div><div class="card-value">${{(dpiUpdates.highlights?.topCulaPct||[])[0]?.code || 'N03'}}</div><div class="card-sub">${{(dpiUpdates.highlights?.topCulaPct||[])[0]?.culaPct || '24.8'}}% · Sungai Lui</div></div>
      <div class="card"><div class="card-label">PRN Negeri Sembilan</div><div class="card-value" style="font-size:16px;color:var(--pos)">${{META.prnNS.mengundi_display || '1 Ogo 2026'}}</div><div class="card-sub">Penamaan ${{META.prnNS.penamaan_display || '18 Jul'}} · ${{META.daysToPolling != null ? META.daysToPolling + ' hari lagi' : '—'}}</div></div>
    </div>
    <div class="alert-banner" style="margin-bottom:16px">
      <i data-lucide="database" style="width:16px;height:16px;color:var(--accent)"></i>
      <span><strong>Data terkini:</strong> DPI Dec 2025 + Ranking DUN 10 Jun 2026 · <strong>ML ensemble</strong> (36 DUN, tier predictive) · <strong>Cina Narrative Intel</strong> (278 rekod hybrid). Tab <strong>ML & InsightPulse</strong> · <strong>DPI & Jentera</strong> · War Room guna BKC/cula.</span>
    </div>
    <div class="grid-3" style="margin-bottom:16px" id="mlOverviewStrip"></div>
    <h3 class="section-title">Garis Masa Strategik</h3>
    <div class="timeline">
      ${{[
        ['PRN 2023','12 Ogo 2023','done'],
        ['Krisis PAS-Bersatu','9 Jun 2026','done'],
        ['Pembubaran DUN','5 Jun 2026','done'],
        ['Keputusan SPR','12 Jun 2026','done'],
        ['Penamaan Calon NS', META.prnNS.penamaan_display || '18 Jul 2026','current'],
        ['Undi Awal NS', META.prnNS.undi_awal_display || '28 Jul 2026','future'],
        ['Hari Mengundi NS', META.prnNS.mengundi_display || '1 Ogo 2026','future']
      ].map(([l,d,s])=>`<div class="tl-item"><div class="tl-dot ${{s}}"></div><div class="tl-label">${{l}}</div><div class="tl-date">${{d}}</div></div>`).join('')}}
    </div>
    <h3 class="section-title">Coalition Watch <span>Pasca split PAS–Bersatu</span></h3>
    <div class="coalition-grid" id="coalitionWatch"></div>
    <h3 class="section-title">Ekonomi Outlook <span>Hybrid — persepsi SME (live) + rasmi (pending)</span></h3>
    <div class="eco-hybrid" id="ecoHybrid"></div>
    <div class="grid-2">
      <div class="card chart-card"><div class="card-label">Sentimen Tekanan Ekonomi (SME crawl)</div><div class="chart-box sm"><canvas id="chartEcoSent"></canvas></div></div>
      <div class="card chart-card"><div class="card-label">Isu Dominan (frekuensi mention)</div><div class="chart-box sm"><canvas id="chartEcoIssues"></canvas></div></div>
    </div>
    <div class="grid-2">
      <div class="card chart-card"><div class="card-label">Taburan Kerusi PRN 2023</div><div class="chart-box"><canvas id="chartBaseline"></canvas></div></div>
      <div class="card"><div class="card-label">Ringkasan Analisis</div>
        <p style="font-size:13px;color:var(--muted);margin-top:8px;line-height:1.6">
          Negeri Sembilan — medan ujian pasca-split PAS–Bersatu. PH pluraliti (17) · PN 5 kerusi (PAS 3 + Bersatu 2).
          <strong>Data jentera DPI Dec 2025:</strong> N03 Sungai Lui cula 24.8% (#1 NS) — sasaran Boleh Menang;
          N05/N25/N31 Pertahan dengan SKT/BKC dipantau. Senario MN (PAS+BN) — 13 cadangan calon dalam tab DPI.
          Ramalan + sentimen = rule-based / AI tone — bukan polling SPR.
        </p>
      </div>
    </div>`;
  const cw = document.getElementById('coalitionWatch');
  coalitionWatch.forEach(c => {{
    cw.innerHTML += `<div class="card coal-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>${{c.name}}</strong>
        <span class="badge badge-pending">${{c.status}}</span>
      </div>
      <div class="prob-bar"><div class="prob-fill" style="width:${{c.probability*100}}%"></div></div>
      <div style="font-size:11px;color:var(--muted)">Kebarangkalian ${{Math.round(c.probability*100)}}%</div>
      <div class="row"><span class="up">↑ ${{c.upside}}</span></div>
      <div class="row"><span class="dn">↓ ${{c.risk}}</span></div>
    </div>`;
  }});
  const mlStrip = document.getElementById('mlOverviewStrip');
  if (mlStrip) {{
    const ml = mlAnalytics || {{}};
    const pred = ml.predictive || {{}};
    const desc = ml.descriptive || {{}};
    const rf = pred.models?.random_forest || {{}};
    const nar = narrativeIntel || {{}};
    const narT = nar.totals || {{}};
    const narN = nar.narrative || {{}};
    mlStrip.innerHTML = `
      <div class="card" style="border-color:rgba(59,130,246,.35)">
        <div class="card-label">ML Ensemble · PRN N9 ${{mlTierBadge(ml.analytics_tier)}}</div>
        <div class="card-value">${{desc.competitive_seats || '—'}}</div>
        <div class="card-sub">Kerusi competitive · RF CV ${{mlPct(rf.cv_accuracy_mean)}} · mean pasWinProb ${{desc.pas_win_prob?.mean || '—'}}%</div>
      </div>
      <div class="card">
        <div class="card-label">Prescriptive Actions</div>
        <div class="card-value">${{(ml.prescriptive_actions||[]).length}}</div>
        <div class="card-sub">${{(ml.prescriptive_actions||[])[0]?.title || 'Tiada tindakan — regenerate ML'}}</div>
      </div>
      <div class="card" style="border-color:rgba(212,168,83,.35)">
        <div class="card-label">Cina Narrative Intel</div>
        <div class="card-value">${{narT.records || 0}}</div>
        <div class="card-sub">PAS-BN ${{narN.pas_bn_mentions || 0}} · syurga cluster ${{narN.harakat_syurga_cluster || 0}} · 汉字 ${{narN.chinese_script_rows || 0}}</div>
      </div>`;
  }}
  charts.baseline = new Chart(document.getElementById('chartBaseline'), {{
    type: 'doughnut',
    data: {{ labels: ['PH','BN','PN'], datasets: [{{ data: [17,14,5], backgroundColor: ['#e84393','#c8102e','#1a7f5a'] }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
  }});
  renderEconomicOutlook(root);
}}

function renderEconomicOutlook(root) {{
  const e = economicOutlook;
  const s = e.sentiment || {{}};
  const hybrid = document.getElementById('ecoHybrid');
  if (!hybrid) return;
  hybrid.innerHTML = `
    <div class="card eco-col">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <strong>Persepsi Awam — SME Crawl</strong>
        <span class="badge badge-live">${{e.status || 'active'}}</span>
      </div>
      <div class="card-label">Posts tekanan ekonomi</div>
      <div class="card-value" style="font-size:22px">${{(e.economicStressPosts||0).toLocaleString()}}</div>
      <div class="card-sub">Daripada ${{ (e.totalPosts||0).toLocaleString() }} posts · ${{e.crawlWindow||''}}</div>
      <div style="margin-top:12px;font-size:12px">
        <span style="color:var(--neg)">-${{s.negativePct||0}}%</span> ·
        <span style="color:var(--muted)">${{s.neutralPct||0}}%</span> ·
        <span style="color:var(--pos)">+${{s.positivePct||0}}%</span>
      </div>
      <p style="font-size:12px;color:var(--muted);margin-top:12px;line-height:1.55">${{e.analystBrief||''}}</p>
    </div>
    <div class="card eco-col official">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <strong>Konteks Makro — BNM Live</strong>
        <span class="badge ${{(e.officialStatus === 'active') ? 'badge-live' : 'badge-pending'}}">${{e.officialStatus || 'pending'}}</span>
      </div>
      <div class="card-sub" style="margin-bottom:8px">${{e.macroContext?.opr||''}}</div>
      <div class="card-sub" style="margin-bottom:8px">${{e.macroContext?.ringgit||''}}</div>
      <div class="card-sub" style="margin-bottom:12px">${{e.macroContext?.investment||''}}</div>
      <div class="card-label">Headline Berita Ekonomi / PRN</div>
      ${{((e.newsHeadlinesLive && e.newsHeadlinesLive.length) ? e.newsHeadlinesLive : (e.newsHeadlines||[])).slice(0,4).map(h=>`<div class="eco-headline">${{h}}</div>`).join('')}}
      <div class="card-label" style="margin-top:12px">Impak PRN NS</div>
      <p style="font-size:12px;color:var(--muted);line-height:1.55">${{e.prnImpact||''}}</p>
    </div>`;
  if (document.getElementById('chartEcoSent')) {{
    charts.ecoSent = new Chart(document.getElementById('chartEcoSent'), {{
      type: 'doughnut',
      data: {{
        labels: ['Negatif','Neutral','Positif'],
        datasets: [{{ data: [s.negativePct, s.neutralPct, s.positivePct], backgroundColor: ['#ef4444','#94a3b8','#22c55e'] }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }}, tooltip: {{ callbacks: {{ label: ctx => ctx.label + ': ' + ctx.raw + '%' }} }} }} }}
    }});
  }}
  const issues = (e.topIssues||[]).slice(0,6);
  if (document.getElementById('chartEcoIssues') && issues.length) {{
    charts.ecoIssues = new Chart(document.getElementById('chartEcoIssues'), {{
      type: 'bar',
      data: {{
        labels: issues.map(i => i.issue),
        datasets: [{{ label: 'Mentions', data: issues.map(i => i.mentions), backgroundColor: '#3b82f6' }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{ legend: {{ display: false }} }} }}
    }});
  }}
}}

function filteredSeats() {{
  return seatData.filter(s => {{
    const q = seatFilter.search.toLowerCase();
    const matchQ = !q || s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q) || s.winnerName.toLowerCase().includes(q);
    const matchB = seatFilter.bloc === 'all' || blocOf(s) === seatFilter.bloc || s.winner2023 === seatFilter.bloc;
    const matchP = seatFilter.party === 'all' || s.party2023 === seatFilter.party;
    const matchK = seatFilter.kategoriPas === 'all' || s.kategoriPas === seatFilter.kategoriPas;
    return matchQ && matchB && matchP && matchK;
  }}).sort((a,b) => {{
    let va = a[seatSort.key], vb = b[seatSort.key];
    if (seatSort.key === 'majority') {{ va = +va; vb = +vb; }}
    if (va < vb) return seatSort.asc ? -1 : 1;
    if (va > vb) return seatSort.asc ? 1 : -1;
    return 0;
  }});
}}

function renderSeats(root) {{
  const seats = filteredSeats();
  const parties = [...new Set(seatData.map(s => s.party2023))].sort();
  root.innerHTML = `
    <div class="sticky-sub"><h3 class="section-title" style="margin:0">Kerusi DUN Negeri Sembilan <span>36 kerusi · klik tile atau baris untuk detail</span></h3></div>
    <div class="toolbar">
      <input type="search" id="seatSearch" placeholder="Cari kod, kawasan, calon…" value="${{seatFilter.search}}" aria-label="Cari kerusi">
      <select id="seatBloc" aria-label="Tapis blok"><option value="all">Semua Blok</option><option value="PH">PH</option><option value="BN">BN</option><option value="PN">PN</option></select>
      <select id="seatParty" aria-label="Tapis parti"><option value="all">Semua Parti</option>${{parties.map(p=>`<option value="${{p}}">${{p}}</option>`).join('')}}</select>
      <select id="seatKategoriPas" aria-label="Tapis kategori PAS"><option value="all">Semua Kategori PAS</option><option value="defend">Pertahan</option><option value="winnable">Boleh Menang</option><option value="tough">Sukar</option><option value="not_priority">Bukan Fokus</option></select>
      <span style="font-size:12px;color:var(--muted)">${{seats.length}} / 36 kerusi</span>
    </div>
    <div class="seat-grid" id="seatGrid" role="list" aria-label="Grid 36 kerusi DUN"></div>
    <div class="table-wrap"><table id="seatTable" aria-label="Jadual kerusi DUN"><thead><tr>
      <th data-sort="code">Kod</th><th data-sort="name">Kawasan</th><th data-sort="winnerName">Penyandang</th>
      <th data-sort="winner2023">Blok 2023</th><th data-sort="party2023">Parti</th>      <th data-sort="kategoriPas">Kategori PAS</th><th data-sort="pasWinProb">Ramalan PAS</th>
      <th data-sort="majority">Majoriti</th><th data-sort="areaType">Jenis</th>
      <th data-sort="threeCornerRisk">3 Penjuru</th><th>Ramalan</th>
    </tr></thead><tbody></tbody></table></div>`;
  document.getElementById('seatSearch').oninput = e => {{ seatFilter.search = e.target.value; renderSection(); }};
  const sel = document.getElementById('seatBloc');
  sel.value = seatFilter.bloc;
  sel.onchange = e => {{ seatFilter.bloc = e.target.value; renderSection(); }};
  const selP = document.getElementById('seatParty');
  selP.value = seatFilter.party;
  selP.onchange = e => {{ seatFilter.party = e.target.value; renderSection(); }};
  const selK = document.getElementById('seatKategoriPas');
  selK.value = seatFilter.kategoriPas;
  selK.onchange = e => {{ seatFilter.kategoriPas = e.target.value; renderSection(); }};
  const grid = document.getElementById('seatGrid');
  filteredSeats().forEach(s => {{
    const b = blocOf(s);
    const col = PARTY_COLORS[s.party2023] || PARTY_COLORS[b];
    const tile = el('div', 'seat-tile');
    tile.style.background = col + '22';
    tile.style.borderColor = col;
    tile.innerHTML = `<span class="code">${{s.code}}</span><span>${{b}}</span><span class="maj">${{s.majority.toLocaleString()}}</span><span class="cat-pill ${{catClass(s.kategoriPas)}}" style="font-size:8px;margin-top:2px">${{catLabel(s.kategoriPas)}}</span>`;
    tile.dataset.code = s.code;
    tile.setAttribute('role', 'listitem');
    tile.setAttribute('tabindex', '0');
    tile.setAttribute('aria-label', `${{s.code}} ${{s.name}}, ${{s.party2023}}, majoriti ${{s.majority}}`);
    tile.onmouseenter = e => showTip(e, `<strong>${{s.name}}</strong><br>${{s.winnerName}} (${{s.party2023}})<br>Majoriti: ${{s.majority.toLocaleString()}}<br>${{s.strategicNote}}`);
    tile.onmouseleave = hideTip;
    tile.onclick = () => openDrawer(s);
    tile.onkeydown = e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openDrawer(s); }} }};
    grid.appendChild(tile);
  }});
  const tbody = root.querySelector('tbody');
  seats.forEach(s => {{
    const b = blocOf(s);
    tbody.innerHTML += `<tr style="cursor:pointer" data-code="${{s.code}}" tabindex="0">
      <td><strong>${{s.code}}</strong></td><td>${{s.name}}</td><td>${{s.winnerName}}</td>
      <td><span class="pill" style="background:${{PARTY_COLORS[b]||'#64748b'}}33;color:${{PARTY_COLORS[b]||'#64748b'}}">${{s.winner2023}}</span></td>
      <td><span class="pill" style="background:${{PARTY_COLORS[s.party2023]||'#64748b'}}33;color:${{PARTY_COLORS[s.party2023]||'#64748b'}}">${{s.party2023}}</span></td>
      <td>${{s.majority.toLocaleString()}}</td>
      <td><span class="cat-pill ${{catClass(s.kategoriPas)}}">${{catLabel(s.kategoriPas)}}</span></td>
      <td><strong>${{s.pasWinProb}}%</strong><div class="pred-bar"><div class="pred-fill" style="width:${{s.pasWinProb}}%"></div></div></td>
      <td>${{s.areaType}}</td>
      <td>${{s.threeCornerRisk === 'Tinggi' ? '<span class="badge badge-risk">Tinggi</span>' : s.threeCornerRisk}}</td>
      <td style="max-width:160px;font-size:11px">${{s.predictionLabel}}</td>
    </tr>`;
  }});
  tbody.querySelectorAll('tr').forEach(tr => {{
    const open = () => openDrawer(seatData.find(s => s.code === tr.dataset.code));
    tr.onclick = open;
    tr.onkeydown = e => {{ if (e.key === 'Enter') open(); }};
  }});
  root.querySelectorAll('th[data-sort]').forEach(th => th.onclick = () => {{
    const k = th.dataset.sort;
    seatSort = {{ key: k, asc: seatSort.key === k ? !seatSort.asc : true }};
    renderSection();
  }});
}}

function renderAnalitik(root) {{
  const a = seatAnalytics;
  const kp = a.kategoriPas || {{}};
  root.innerHTML = `
    <div class="sticky-sub"><h3 class="section-title" style="margin:0">Analitik Kerusi & Ramalan PRN 2026
      <span>Sumber: PRN2023_NegeriSembilan_v2.xlsx · rule-based model</span></h3></div>
    <div class="alert-banner" style="margin-bottom:16px">
      <i data-lucide="info" style="width:16px;height:16px;color:var(--accent)"></i>
      <span><strong>Nota:</strong> Ramalan = model rule-based (majoriti + kategori PAS + baseline 2023). Bukan polling. Penamaan NS: ${{META.prnNS.penamaan_display || '18 Jul 2026'}}.</span>
    </div>
    <div class="grid-4">
      <div class="card"><div class="card-label">Pertahan PAS</div><div class="card-value" style="color:var(--pas)">${{kp.defend || 0}}</div><div class="card-sub">${{(a.defendSeats||[]).join(', ')}}</div></div>
      <div class="card"><div class="card-label">Boleh Menang</div><div class="card-value" style="color:var(--accent)">${{kp.winnable || 0}}</div><div class="card-sub">${{(a.winnableSeats||[]).join(', ')}}</div></div>
      <div class="card"><div class="card-label">Sukar / Lawan Kuat</div><div class="card-value" style="color:var(--warn)">${{kp.tough || 0}}</div><div class="card-sub">${{(a.toughSeats||[]).join(', ')}}</div></div>
      <div class="card"><div class="card-label">Ramalan PAS ≥50%</div><div class="card-value">${{a.predictedPasWins || 0}}</div><div class="card-sub">kerusi · ${{ (a.predictedPasSeats||[]).join(', ') }}</div></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <strong>Crawl ADUN Seeds — Berita & Media (30 hari)</strong>
        <span class="badge ${{(adunSocialCrawl.total_rows) ? 'badge-live' : 'badge-pending'}}">${{adunSocialCrawl.total_rows ? 'active' : 'pending'}}</span>
      </div>
      <div class="grid-4" style="margin-bottom:0">
        <div><div class="card-label">Kerusi ada mention</div><div class="card-value" style="font-size:20px">${{adunSocialCrawl.seats_crawled || 0}}/36</div></div>
        <div><div class="card-label">Jumlah rows crawl</div><div class="card-value" style="font-size:20px">${{adunSocialCrawl.total_rows || 0}}</div></div>
        <div><div class="card-label">Seeds dengan handle</div><div class="card-value" style="font-size:20px">${{adunSocialCrawl.seeds_with_handles || 0}}</div></div>
        <div><div class="card-label">Media NS</div><div class="card-value" style="font-size:20px">${{adunSocialCrawl.media_mentions || 0}}</div></div>
      </div>
      <p style="font-size:11px;color:var(--muted);margin-top:12px">Sumber: sheet ADUN Terpilih · N03/N09 = zon pertarungan (~50% model)</p>
    </div>
    <div class="grid-2">
      <div class="card chart-card"><div class="card-label">Taburan Kategori PAS</div><div class="chart-box sm"><canvas id="chartKatPas"></canvas></div></div>
      <div class="card chart-card"><div class="card-label">Taburan Margin Kerusi</div><div class="chart-box sm"><canvas id="chartKatMargin"></canvas></div></div>
    </div>
    <div class="grid-2">
      <div class="card chart-card"><div class="card-label">Ramalan Kebarangkalian PAS Menang (%)</div><div class="chart-box"><canvas id="chartPasProb"></canvas></div></div>
      <div class="card"><div class="card-label">Senario PAS — Purata Kerusi (model)</div>
        <div style="font-size:12px;margin-top:10px;line-height:1.8">
          <div><strong>Solo:</strong> ${{Math.round(seatData.filter(s=>s.scenarioPasSolo>=50).length)}} kerusi prob ≥50%</div>
          <div><strong>+ PN:</strong> ${{Math.round(seatData.filter(s=>s.scenarioPasPn>=50).length)}} kerusi prob ≥50%</div>
          <div><strong>+ MN:</strong> ${{Math.round(seatData.filter(s=>s.scenarioPasMn>=50).length)}} kerusi prob ≥50%</div>
          <div style="margin-top:12px;color:var(--muted)">Ultra marginal: ${{(a.ultraMarginal||[]).join(', ') || '—'}}</div>
        </div>
      </div>
    </div>
    <h3 class="section-title">Jadual Analitik Penuh <span>36 kerusi · DPI Dec 2025 + cula/SKT · klik baris untuk detail</span></h3>
    <div class="table-wrap analytics-table"><table><thead><tr>
      <th>Kod</th><th>Kawasan</th><th>Parti 2023</th><th>Majoriti</th><th>Pengundi DPI</th><th>% Melayu</th><th>Cula%</th><th>BKC</th><th>Margin</th><th>Kategori PAS</th>
      <th>Ramalan PAS</th><th>Prediksi</th><th>Solo</th><th>+PN</th><th>+MN</th><th>Jentera</th><th>Pantau</th>
    </tr></thead><tbody id="analyticsBody"></tbody></table></div>`;

  const sorted = [...seatData].sort((x,y) => y.pasWinProb - x.pasWinProb);
  const tbody = document.getElementById('analyticsBody');
  sorted.forEach(s => {{
    const bkc = s.bkcCula != null ? s.bkcCula.toLocaleString() : '—';
    const cula = s.culaPct != null ? s.culaPct + '%' : '—';
    const melayu = s.pctMelayu != null ? s.pctMelayu + '%' : '—';
    const pengundi = s.registeredVotersDpi ? s.registeredVotersDpi.toLocaleString() : '—';
    const jentera = s.jenteraStatus || '—';
    tbody.innerHTML += `<tr style="cursor:pointer" data-code="${{s.code}}" tabindex="0">
      <td><strong>${{s.code}}</strong></td><td>${{s.name}}</td>
      <td><span class="pill" style="background:${{PARTY_COLORS[s.party2023]||'#64748b'}}33">${{s.party2023}}</span></td>
      <td>${{s.majority.toLocaleString()}}</td><td>${{pengundi}}</td><td>${{melayu}}</td><td>${{cula}}</td><td style="color:${{s.bkcCula < 0 ? 'var(--neg)' : 'var(--pos)'}}">${{bkc}}</td>
      <td>${{s.kategoriMarginLabel || s.kategoriMargin}}</td>
      <td><span class="cat-pill ${{catClass(s.kategoriPas)}}">${{catLabel(s.kategoriPas)}}</span></td>
      <td><strong>${{s.pasWinProb}}%</strong></td><td>${{s.predictionLabel}}</td>
      <td>${{s.scenarioPasSolo}}%</td><td>${{s.scenarioPasPn}}%</td><td>${{s.scenarioPasMn}}%</td>
      <td style="font-size:10px;max-width:100px">${{jentera}}</td>
      <td>${{s.priorityMonitoring ? '✓' : '—'}}</td></tr>`;
  }});
  tbody.querySelectorAll('tr').forEach(tr => {{
    const open = () => openDrawer(seatData.find(s => s.code === tr.dataset.code));
    tr.onclick = open; tr.onkeydown = e => {{ if (e.key === 'Enter') open(); }};
  }});

  const km = a.kategoriMargin || {{}};
  charts.katPas = new Chart(document.getElementById('chartKatPas'), {{
    type: 'doughnut',
    data: {{ labels: ['Pertahan','Boleh Menang','Sukar','Bukan Fokus'],
      datasets: [{{ data: [kp.defend||0, kp.winnable||0, kp.tough||0, kp.not_priority||0],
        backgroundColor: ['#1a7f5a','#3b82f6','#f59e0b','#64748b'] }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
  }});
  charts.katMargin = new Chart(document.getElementById('chartKatMargin'), {{
    type: 'bar',
    data: {{ labels: ['Ultra 0-199','Super 200-499','Marginal 500-999','Semi 1K-3K','Selamat 3K+'],
      datasets: [{{ data: [km.ultra_marginal||0, km.super_marginal||0, km.marginal||0, km.semi_safe||0, km.safe||0],
        backgroundColor: '#d4a853' }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
  }});
  charts.pasProb = new Chart(document.getElementById('chartPasProb'), {{
    type: 'bar',
    data: {{
      labels: sorted.map(s => s.code),
      datasets: [{{ label: 'PAS Win %', data: sorted.map(s => s.pasWinProb),
        backgroundColor: sorted.map(s => s.pasWinProb >= 50 ? '#1a7f5a' : s.pasWinProb >= 35 ? '#f59e0b' : '#64748b') }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ max: 100, min: 0 }} }} }}
  }});
}}

function renderScenarios(root) {{
  root.innerHTML = `
    <div class="scenario-matrix" id="scenarioMatrix"></div>
    <div class="grid-2">
      <div class="card chart-card"><div class="card-label">Perbandingan Senario — Anggaran Kerusi PN/PAS</div><div class="chart-box"><canvas id="chartScenarioBar"></canvas></div></div>
      <div class="card chart-card"><div class="card-label">Profil Risiko Senario</div><div class="chart-box"><canvas id="chartScenarioRadar"></canvas></div></div>
    </div>
    <h3 class="section-title">Nota Penganalisis</h3>
    <div class="note-cards" id="analystNotes"></div>`;
  const mx = document.getElementById('scenarioMatrix');
  coalitionScenarios.forEach(sc => {{
    mx.innerHTML += `<div class="card scenario-card">
      <h4>${{sc.name}} <span class="badge badge-pending">${{Math.round(sc.probability*100)}}%</span></h4>
      <ul>
        <li><strong>Kerusi:</strong> ~${{sc.projectedSeats}}</li>
        <li><strong>Peluang:</strong> ${{sc.winChance}}</li>
        <li><strong>Undi Melayu:</strong> ${{sc.malayVoteImpact}}</li>
        <li><strong>Risiko akar umbi:</strong> ${{sc.grassrootsRisk}}</li>
        <li><strong>3 penjuru:</strong> ${{sc.threeCornerRisk}}</li>
        <li><strong>Impak PH/BN:</strong> ${{sc.phBnImpact}}</li>
      </ul>
    </div>`;
  }});
  const notes = document.getElementById('analystNotes');
  coalitionScenarios.forEach(sc => {{
    notes.innerHTML += `<div class="card note-card"><h4 style="font-size:13px;margin-bottom:8px">${{sc.name}}</h4>
      <p style="font-size:11px;margin-bottom:6px"><strong>Kenapa senario ini munasabah:</strong> ${{sc.whyReasonable}}</p>
      <p style="font-size:11px;margin-bottom:6px"><strong>Apa signal yang perlu dipantau:</strong> ${{sc.signals}}</p>
      <p style="font-size:11px"><strong>Apa trigger yang boleh ubah keputusan:</strong> ${{sc.triggers}}</p></div>`;
  }});
  charts.scBar = new Chart(document.getElementById('chartScenarioBar'), {{
    type: 'bar',
    data: {{
      labels: coalitionScenarios.map(s => s.name),
      datasets: [
        {{ label: 'Anggaran kerusi', data: coalitionScenarios.map(s => s.projectedSeats), backgroundColor: '#d4a853' }},
        {{ label: 'Kebarangkalian (×10)', data: coalitionScenarios.map(s => s.probability*10), backgroundColor: '#3b82f6' }}
      ]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
  }});
  charts.scRadar = new Chart(document.getElementById('chartScenarioRadar'), {{
    type: 'radar',
    data: {{
      labels: ['Kerusi','Kebarangkalian','Risiko 3 penjuru','Impak Melayu','Stabiliti'],
      datasets: coalitionScenarios.map((s,i) => ({{
        label: s.name,
        data: [s.projectedSeats/12*10, s.probability*10, s.threeCornerRisk.includes('Tinggi')?8:5, 7-i, 6-i*0.5],
        borderColor: ['#1a7f5a','#3b82f6','#d4a853','#e84393'][i],
        backgroundColor: 'transparent'
      }}))
    }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ r: {{ min: 0, max: 10 }} }} }}
  }});
}}

function renderMlInsight(root) {{
  const ml = mlAnalytics || {{}};
  const pred = ml.predictive || {{}};
  const desc = ml.descriptive || {{}};
  const models = pred.models || {{}};
  const seats = (ml.seat_predictions || []).slice().sort((a, b) => (b.ml_competitive_prob || 0) - (a.ml_competitive_prob || 0));
  const competitive = seats.filter(s => s.ml_competitive_flag);
  const actions = ml.prescriptive_actions || [];
  const nar = narrativeIntel || {{}};
  const narT = nar.totals || {{}};
  const narN = nar.narrative || {{}};
  const narS = nar.sentiment || {{}};
  const notes = nar.n9_campaign_notes || [];
  const modelRows = Object.entries(models).filter(([, s]) => s.cv_accuracy_mean != null).map(([name, s]) => `
    <div class="ml-model-row">
      <span class="ml-model-name">${{name.replace(/_/g, ' ').toUpperCase()}}</span>
      <span>CV Acc <strong>${{mlPct(s.cv_accuracy_mean)}}</strong></span>
      <span>F1 <strong>${{mlPct(s.cv_f1_mean)}}</strong></span>
    </div>`).join('') || '<p class="card-sub">Model belum dilatih — jalankan scripts/build_n9_ml_predictions.py</p>';
  const seatRows = competitive.slice(0, 15).map(s => {{
    const p = Math.round((s.ml_competitive_prob || 0) * 100);
    const cls = p >= 85 ? 'ml-comp-high' : (p >= 60 ? 'ml-comp-mid' : '');
    return `<tr><td><strong>${{s.code}}</strong></td><td>${{s.name}}</td><td>${{catLabel(s.kategoriPas)}}</td><td>${{s.pasWinProb}}%</td><td class="${{cls}}">${{p}}%</td><td>${{s.majority?.toLocaleString?.() || s.majority || '—'}}</td></tr>`;
  }}).join('');
  const actionCards = actions.slice(0, 6).map(a => `
    <div class="card"><div class="card-label">${{a.priority || 'action'}} · ${{a.seat || 'NS'}}</div>
    <strong style="font-size:13px">${{a.title || '—'}}</strong>
    <p class="card-sub" style="margin-top:6px">${{a.detail || a.rationale || ''}}</p></div>`).join('');
  const topCn = (nar.top_chinese || []).slice(0, 5).map(t => `
    <li style="margin-bottom:8px;font-size:12px">${{(t.text || '').slice(0, 140)}}… <span style="color:var(--muted)">eng ${{t.eng || 0}} · ${{t.sent || '—'}}</span></li>`).join('');
  const noteList = notes.map(n => `<li style="margin-bottom:6px;font-size:12px">${{n}}</li>`).join('');
  root.innerHTML = `
    <div class="alert-banner" style="margin-bottom:16px">
      <i data-lucide="brain" style="width:16px;height:16px;color:var(--accent)"></i>
      <span>${{ml.disclaimer || 'Bukan polling SPR.'}} · Generated ${{ml.generated_at ? ml.generated_at.slice(0, 16).replace('T', ' ') : '—'}} · API <code style="font-size:11px">/api/ml/predict/prn_n9</code></span>
    </div>
    <div class="grid-4" style="margin-bottom:16px">
      <div class="card"><div class="card-label">Analytics Tier</div><div style="margin-top:8px">${{mlTierBadge(ml.analytics_tier)}}</div><div class="card-sub">${{ml.label_definition || ''}}</div></div>
      <div class="card"><div class="card-label">DUN Competitive (ML)</div><div class="card-value">${{desc.competitive_seats || competitive.length}}</div><div class="card-sub">dari ${{desc.seats_total || 36}} kerusi · n=${{pred.n_samples || '—'}}</div></div>
      <div class="card"><div class="card-label">Mean pasWinProb</div><div class="card-value">${{desc.pas_win_prob?.mean || '—'}}%</div><div class="card-sub">min ${{desc.pas_win_prob?.min || '—'}} · max ${{desc.pas_win_prob?.max || '—'}}</div></div>
      <div class="card"><div class="card-label">Ensemble Method</div><div class="card-value" style="font-size:16px">${{pred.ensemble?.method || 'mean_probability'}}</div><div class="card-sub">${{Object.keys(models).length}} model · features ${{ (pred.feature_names||[]).length }}</div></div>
    </div>
    <h3 class="section-title">Model Performance <span>SVM · Random Forest · Decision Tree</span></h3>
    <div class="card" style="margin-bottom:20px">${{modelRows}}</div>
    <h3 class="section-title">Kerusi Competitive — ML Ranking <span>ml_competitive_prob ensemble</span></h3>
    <div class="table-wrap" style="margin-bottom:24px"><table><thead><tr><th>Kod</th><th>Nama</th><th>Kategori PAS</th><th>Rule pasWinProb</th><th>ML Prob</th><th>Majoriti 2023</th></tr></thead><tbody>${{seatRows || '<tr><td colspan="6">Tiada data — regenerate ML</td></tr>'}}</tbody></table></div>
    <h3 class="section-title">Prescriptive Actions <span>InsightPulse tier 3</span></h3>
    <div class="grid-2" style="margin-bottom:24px">${{actionCards || '<div class="card"><div class="card-sub">Tiada prescriptive actions</div></div>'}}</div>
    <h3 class="section-title">Cina Narrative Intel <span>Johor proxy → kempen bandar NS</span></h3>
    <div class="grid-4" style="margin-bottom:12px">
      <div class="card"><div class="card-label">Rekod Dedup</div><div class="card-value">${{narT.records || 0}}</div><div class="card-sub">${{narT.posts || 0}} post · ${{narT.comments || 0}} komen</div></div>
      <div class="card"><div class="card-label">PAS–BN Mention</div><div class="card-value">${{narN.pas_bn_mentions || 0}}</div><div class="card-sub">Johor related ${{narN.johor_related || 0}}</div></div>
      <div class="card"><div class="card-label">Syurga / Harakat</div><div class="card-value">${{narN.harakat_syurga_cluster || 0}}</div><div class="card-sub">汉字 posts ${{narN.chinese_script_rows || 0}} · core issue ${{narN.core_issue_pct || 0}}%</div></div>
      <div class="card"><div class="card-label">Sentimen</div><div class="card-value" style="font-size:16px">+${{narS.positive || 0}} / −${{narS.negative || 0}}</div><div class="card-sub">neutral ${{narS.neutral || 0}} · crawl ${{nar.crawl_batches || '—'}} batch</div></div>
    </div>
    <div class="grid-2" style="margin-bottom:20px">
      <div class="card"><div class="card-label">Implikasi Kempen N9</div><ul class="rank-list">${{noteList}}</ul></div>
      <div class="card"><div class="card-label">Top Post Media Cina (Johor)</div><ul class="rank-list">${{topCn || '<li>Tiada</li>'}}</ul></div>
    </div>
    <div class="card chart-card"><div class="card-label">ML Competitive Probability (Top 12)</div><div class="chart-box"><canvas id="chartMlComp"></canvas></div></div>`;
  const top12 = competitive.slice(0, 12);
  if (top12.length && document.getElementById('chartMlComp')) {{
    charts.mlComp = new Chart(document.getElementById('chartMlComp'), {{
      type: 'bar',
      data: {{
        labels: top12.map(s => s.code),
        datasets: [{{
          label: 'ML competitive prob %',
          data: top12.map(s => Math.round((s.ml_competitive_prob || 0) * 100)),
          backgroundColor: top12.map(s => (s.ml_competitive_prob || 0) >= 0.85 ? '#f59e0b' : '#3b82f6'),
        }}],
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true, max: 100 }} }} }},
    }});
  }}
}}

function renderCommunityNews() {{
  const cn = communityNews || {{}};
  const by = cn.byCommunity || {{}};
  const labs = cn.labels || {{}};
  const mt = cn.mediaTone || {{}};
  const pv = cn.publicVoice || {{}};
  const order = ['umum','melayu','islam','cina','india','lain','ekonomi'];
  const pct = (n,t) => t ? Math.round(n/t*100) : 0;
  const toneBar = (tone, label) => {{
    const t = tone.total || 0;
    if (!t) return '';
    return `<div class="card" style="margin-bottom:10px"><div class="card-label">${{label}} (${{t}} baris Tier A)</div>
      <div class="card-sub">+${{pct(tone.positive,t)}}% · ~${{pct(tone.neutral,t)}}% · -${{pct(tone.negative,t)}}% · neg ${{tone.neg_pct||0}}%</div></div>`;
  }};
  const cards = order.filter(k => by[k]).map(k => {{
    const heads = (cn.headlines && cn.headlines[k]) || [];
    const cs = (cn.communitySentiment && cn.communitySentiment[k]) || {{}};
    const negHint = cs.neg_pct != null ? ` · neg ${{cs.neg_pct}}%` : '';
    const list = heads.length ? heads.map(h => `<li><a href="${{h.url||'#'}}" target="_blank" rel="noopener">${{h.text||'—'}}</a> <span style="color:var(--muted);font-size:11px">${{h.domain||''}}</span></li>`).join('') : '<li style="color:var(--muted)">Tiada headline</li>';
    return `<div class="card"><div class="card-label">${{labs[k]||k}} <span style="float:right;font-weight:600;color:var(--accent)">${{by[k]||0}}</span></div><div class="card-sub" style="font-size:11px">${{negHint}}</div><ul class="rank-list" style="margin-top:8px;font-size:12px">${{list}}</ul></div>`;
  }}).join('');
  const alerts = (cn.narrativeAlerts||[]).map(a => `<li><span class="badge badge-pending">${{a.severity||'watch'}}</span> ${{a.message||''}}</li>`).join('');
  const negList = (cn.topNegative||[]).slice(0,3).map(x => `<li>${{x.text||''}} <span style="color:var(--muted)">[${{x.community||''}}]</span></li>`).join('');
  return `
    <h3 class="section-title" style="margin-bottom:12px">Berita Komuniti — Crawl + Smart Analyze (Tier A)</h3>
    <div class="alert-banner" style="margin-bottom:14px">
      <i data-lucide="newspaper" style="width:16px;height:16px;color:var(--accent)"></i>
      <span><strong>${{cn.total||0}} artikel</strong> crawl · <strong>${{cn.rowsAnalyzed||0}}</strong> dianalisis (skip ${{cn.rowsSkipped||0}} bulk RSS) · ${{cn.analyzedAt ? cn.analyzedAt.slice(0,16).replace('T',' ') : 'belum analyze'}}</span>
    </div>
    <div class="grid-2" style="margin-bottom:12px">${{toneBar(mt, 'Media Tone — artikel direct')}}${{toneBar(pv, 'Public Voice — komen pembaca')}}</div>
    ${{alerts ? `<div class="card" style="margin-bottom:14px"><div class="card-label">Alert Naratif Media</div><ul class="rank-list">${{alerts}}</ul></div>` : ''}}
    ${{negList ? `<div class="card" style="margin-bottom:14px"><div class="card-label">Top Negatif (Tier A)</div><ul class="rank-list" style="font-size:12px">${{negList}}</ul></div>` : ''}}
    <p class="card-sub" style="margin-bottom:10px">${{cn.note||''}}</p>
    <div class="grid-2" style="margin-bottom:24px">${{cards || '<div class="card"><div class="card-sub">Jalankan: bash scripts/run_prn_n9_daily.sh</div></div>'}}</div>`;
}}

function renderSentiment(root) {{
  const plat = ['facebook','tiktok','x','media'];
  const labels = {{ facebook:'Facebook', tiktok:'TikTok', x:'X (Twitter)', media:'Portal Berita / Podcast' }};
  const meta = socialSentiment.meta || {{}};
  const otherPlat = meta.otherPlatforms ? Object.entries(meta.otherPlatforms).map(([k,v]) => `${{k}} ${{v}}`).join(' · ') : '';
  const engNS = meta.engagementNS || {{}};
  const engG = meta.engagementGlobal || {{}};
  const crawled = meta.totalPostsCrawled || meta.masterTotal || 68256;
  root.innerHTML = `
    ${{renderCommunityNews()}}
    <div class="grid-4" style="margin-bottom:8px">
      <div class="card" style="border-color:var(--gold)">
        <div class="card-label">Total Posts Crawled</div>
        <div class="card-value">${{crawled.toLocaleString()}}</div>
        <div class="card-sub">${{engG.postRows?.toLocaleString?.() || '—'}} posts · ${{engG.commentRows?.toLocaleString?.() || '—'}} comment rows · master penuh</div>
      </div>
      <div class="card"><div class="card-label">Mention NS (Socmed)</div><div class="card-value">${{meta.totalPosts || 0}}</div><div class="card-sub">${{meta.politicalRows || 0}} berkait politik · ${{engNS.postRows || '—'}} post rows</div></div>
      <div class="card"><div class="card-label">Komen NS (aggregated)</div><div class="card-value">${{(engNS.commentsCount || engNS.comments || 0).toLocaleString()}}</div><div class="card-sub">${{engNS.commentRows || 0}} comment rows di-crawl · 👍 ${{fmtEng(engNS.likes)}}</div></div>
      <div class="card"><div class="card-label">Engagement NS</div><div class="card-value">${{fmtEng(engNS.total)}}</div><div class="card-sub">Global master: ${{fmtEng(engG.total)}} · 👁 ${{fmtEng(engNS.views)}}</div></div>
    </div>
    <div class="grid-4">
      <div class="card"><div class="card-label">Naratif Split vs Solo</div><div class="card-value" style="font-size:18px">${{meta.splitVsSolo || '36 vs 6'}}</div><div class="card-sub">PN vs MN: ${{meta.pnVsMn || '29 vs 12'}} · ${{otherPlat || 'platform lain'}}</div></div>
    </div>
    <p class="card-sub" style="margin:-8px 0 16px;color:var(--muted)">${{meta.dataNote || ''}}</p>
    <div class="tabs" id="sentTabs">${{plat.map((p,i)=>`<div class="tab${{i?'':' active'}}" data-tab="${{p}}">${{labels[p]}}</div>`).join('')}}</div>
    <div id="sentPanels"></div>
    <h3 class="section-title" style="margin-top:24px">Naratif Dominan</h3>
    <div class="narrative-cards">${{socialSentiment.dominantNarratives.map(n=>`
      <div class="card narr-card"><strong>${{n.title}}</strong><div style="margin-top:8px;font-size:12px;color:var(--muted)">Share ~${{n.share}}% · ${{n.sentiment}}</div>
      <span class="badge ${{n.risk==='Tinggi'?'badge-risk':'badge-pending'}}" style="margin-top:8px">${{n.risk}}</span></div>`).join('')}}</div>
    <div class="card chart-card" style="margin-bottom:20px"><div class="card-label">Trend Volume Perbualan NS (anggaran — batch crawl)</div><div class="chart-box"><canvas id="chartVolume"></canvas></div></div>
    <h3 class="section-title">Top Posts NS</h3>
    <div class="table-wrap"><table><thead><tr><th>Platform</th><th>Akaun</th><th>Ringkasan</th><th>Engagement</th><th>Sentimen</th><th>Risiko</th></tr></thead><tbody>
      ${{socialSentiment.topPosts.map(p=>`<tr><td>${{p.platform}}</td><td>${{p.account}}</td><td>${{p.summary}}</td><td>${{p.engagement.toLocaleString()}}</td><td>${{p.sentiment}}</td><td>${{p.risk}}</td></tr>`).join('')}}
    </tbody></table></div>`;
  const panels = document.getElementById('sentPanels');
  plat.forEach((p,i) => {{
    const d = socialSentiment[p];
    const t = d.volume;
    panels.innerHTML += `<div class="tab-panel${{i?'':' active'}}" data-panel="${{p}}">
      <div class="grid-3">
        <div class="card"><div class="card-label">Volume</div><div class="card-value">${{d.volume}}</div></div>
        <div class="card"><div class="card-label">Sentimen</div><div class="card-value" style="font-size:14px">+${{pct(d.positive,t)}}% · ${{pct(d.neutral,t)}}% · -${{pct(d.negative,t)}}%</div></div>
        <div class="card"><div class="card-label">Keywords</div><div class="card-sub">${{d.keywords.join(' · ')}}</div></div>
      </div>
      <div class="grid-2" style="margin-top:14px">
        <div class="card"><div class="card-label">Top Influencer / Media</div><ul class="rank-list">${{d.influencers.map(x=>`<li>${{x}}</li>`).join('')}}</ul></div>
        <div class="card"><div class="card-label">Naratif Utama</div><ul class="rank-list">${{d.narratives.map(x=>`<li>${{x}}</li>`).join('')}}</ul></div>
      </div>
    </div>`;
  }});
  root.querySelectorAll('.tab').forEach(tab => tab.onclick = () => {{
    root.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    root.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    root.querySelector(`.tab-panel[data-panel="${{tab.dataset.tab}}"]`).classList.add('active');
  }});
  charts.vol = new Chart(document.getElementById('chartVolume'), {{
    type: 'line',
    data: {{
      labels: socialSentiment.volumeTrend.map(v => v.date.slice(5)),
      datasets: [{{ label: 'Volume', data: socialSentiment.volumeTrend.map(v => v.volume), borderColor: '#3b82f6', tension: .3, fill: true, backgroundColor: 'rgba(59,130,246,.1)' }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false }}
  }});
}}

function renderDpiJentera(root) {{
  const hl = dpiUpdates.highlights || {{}};
  const mn = dpiUpdates.mnProposals || [];
  const totalVoters = seatData.reduce((a,s) => a + (s.registeredVotersDpi || 0), 0);
  const avgMelayu = seatData.filter(s => s.pctMelayu).reduce((a,s,i,arr) => a + s.pctMelayu / arr.length, 0);
  const topCula = (hl.topCulaPct || [])[0] || {{}};
  const needJentera = seatData.filter(s => s.bkcCula != null && s.bkcCula < -1000).length;
  root.innerHTML = `
    <div class="sticky-sub"><h3 class="section-title" style="margin:0">DPI & Jentera — Data Pengundi & Operasi Lapangan
      <span>${{META.dpiAsOf}} · Ranking ${{META.rankingAsOf}}</span></h3></div>
    <div class="alert-banner" style="margin-bottom:16px">
      <i data-lucide="users" style="width:16px;height:16px;color:var(--accent)"></i>
      <span><strong>Sumber:</strong> Updates_Data DUN ikut ranking.xlsx + Demografi DPI Dec 2025. SKT 51% = sasaran undi minimum. BKC negatif = undi masih perlu dicari dari cula.</span>
    </div>
    <div class="grid-4">
      <div class="card"><div class="card-label">Jumlah Pengundi NS</div><div class="card-value">${{totalVoters.toLocaleString()}}</div><div class="card-sub">DPI Dis 2025 · 36 DUN</div></div>
      <div class="card"><div class="card-label">Purata % Melayu</div><div class="card-value">${{avgMelayu ? avgMelayu.toFixed(1) : '—'}}%</div><div class="card-sub">Across all DUN</div></div>
      <div class="card"><div class="card-label">Cula Tertinggi</div><div class="card-value">${{topCula.code || '—'}}</div><div class="card-sub">${{topCula.culaPct || '—'}}% · ${{topCula.culaPasTotal || '—'}} pengundi</div></div>
      <div class="card"><div class="card-label">Perlu Perkukuh Jentera</div><div class="card-value" style="color:var(--warn)">${{needJentera}}</div><div class="card-sub">BKC cula &lt; −1,000 undi</div></div>
    </div>
    <div class="grid-2" style="margin-bottom:20px">
      <div class="card chart-card"><div class="card-label">Top 8 — % Cula PAS</div><div class="chart-box sm"><canvas id="chartCulaPct"></canvas></div></div>
      <div class="card chart-card"><div class="card-label">Top 8 — Pertumbuhan Pengundi (PRU15→DPI)</div><div class="chart-box sm"><canvas id="chartVoterGrowth"></canvas></div></div>
    </div>
    <h3 class="section-title">Jadual Jentera & Cula (36 DUN) <span>klik baris untuk detail</span></h3>
    <div class="table-wrap analytics-table"><table><thead><tr>
      <th>Kod</th><th>DUN</th><th>Pengundi DPI</th><th>% Melayu</th><th>Cula PAS</th><th>Cula%</th><th>SKT 51%</th><th>BKC Cula</th><th>Markah SLU</th><th>Rank Majoriti</th><th>Status Jentera</th>
    </tr></thead><tbody id="dpiBody"></tbody></table></div>
    <h3 class="section-title" style="margin-top:28px">Cadangan Kerusi PAS + BN (MN) <span>10 Jun 2026 · perbincangan</span></h3>
    <div class="table-wrap"><table><thead><tr><th>#</th><th>Parlimen</th><th>DUN</th><th>Kod</th><th>Bakal Calon</th><th>Catatan</th></tr></thead><tbody id="mnBody"></tbody></table></div>`;

  const dpiSorted = [...seatData].sort((a,b) => (b.culaPct||0) - (a.culaPct||0));
  const db = document.getElementById('dpiBody');
  dpiSorted.forEach(s => {{
    db.innerHTML += `<tr style="cursor:pointer" data-code="${{s.code}}" tabindex="0">
      <td><strong>${{s.code}}</strong></td><td>${{s.name}}</td>
      <td>${{(s.registeredVotersDpi||0).toLocaleString()}}</td>
      <td>${{s.pctMelayu != null ? s.pctMelayu + '%' : '—'}}</td>
      <td>${{s.culaPasTotal != null ? s.culaPasTotal.toLocaleString() : '—'}}</td>
      <td><strong>${{s.culaPct != null ? s.culaPct + '%' : '—'}}</strong></td>
      <td>${{s.skt51 != null ? s.skt51.toLocaleString() : '—'}}</td>
      <td style="color:${{(s.bkcCula||0) < 0 ? 'var(--neg)' : 'var(--pos)'}}">${{s.bkcCula != null ? s.bkcCula.toLocaleString() : '—'}}</td>
      <td>${{s.markahSlu || '—'}}</td>
      <td>${{s.rankingMajoritiPru15 || '—'}}</td>
      <td style="font-size:11px">${{s.jenteraStatus || '—'}}</td></tr>`;
  }});
  db.querySelectorAll('tr').forEach(tr => {{
    const open = () => openDrawer(seatData.find(s => s.code === tr.dataset.code));
    tr.onclick = open; tr.onkeydown = e => {{ if (e.key === 'Enter') open(); }};
  }});

  const mb = document.getElementById('mnBody');
  mn.filter(r => r.dunName && !String(r.dunName).toLowerCase().includes('petunjuk')).forEach(r => {{
    mb.innerHTML += `<tr><td>${{r.bil || '—'}}</td><td>${{r.parlimen || '—'}}</td><td>${{r.dunName}}</td><td><strong>${{r.code || '—'}}</strong></td><td>${{r.calonMn || '—'}}</td><td style="font-size:11px;color:var(--muted)">${{r.catatanMn || '—'}}</td></tr>`;
  }});

  const tc = hl.topCulaPct || [];
  charts.culaPct = new Chart(document.getElementById('chartCulaPct'), {{
    type: 'bar',
    data: {{ labels: tc.map(x => x.code), datasets: [{{ label: '% Cula', data: tc.map(x => x.culaPct), backgroundColor: '#1a7f5a' }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: '%' }} }} }} }}
  }});
  const tg = hl.topVoterGrowth || [];
  charts.voterGrowth = new Chart(document.getElementById('chartVoterGrowth'), {{
    type: 'bar',
    data: {{ labels: tg.map(x => x.code), datasets: [{{ label: '+Pengundi', data: tg.map(x => x.voterDiff), backgroundColor: '#3b82f6' }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
  }});
}}

function renderProfiles(root) {{
  const pertahan = seatData.filter(s => s.party2023 === 'PAS');
  const sasaran = seatData.filter(s => s.pasInterest === 'Sasaran');
  const risiko = seatData.filter(s => s.threeCornerRisk === 'Tinggi');
  root.innerHTML = `
    <div class="grid-3" style="margin-bottom:20px">
      <div class="card"><div class="card-label">Kerusi PAS Pertahan</div><ul class="rank-list">${{pertahan.map(s=>`<li><span>${{s.code}} ${{s.name}}</span><span>${{s.majority.toLocaleString()}}</span></li>`).join('')}}</ul></div>
      <div class="card"><div class="card-label">Kerusi PAS Sasaran</div><ul class="rank-list">${{sasaran.slice(0,8).map(s=>`<li><span>${{s.code}} ${{s.name}}</span><span class="badge badge-pending">${{s.threeCornerRisk}}</span></li>`).join('')}}</ul></div>
      <div class="card"><div class="card-label">Kerusi Risiko Tinggi (3 Penjuru)</div><ul class="rank-list">${{risiko.map(s=>`<li><span>${{s.code}} ${{s.name}}</span><span class="badge badge-risk">Tinggi</span></li>`).join('')}}</ul></div>
    </div>
    <div class="map-placeholder" style="margin-bottom:20px"><div><i data-lucide="map" style="width:32px;height:32px;margin-bottom:8px"></i><br>Peta DUN Negeri Sembilan — placeholder<br><small>Integrasi GeoJSON / Leaflet — REPLACE WITH API: /api/prn/n9/map</small></div></div>
    <h3 class="section-title">Profil Kawasan Keutamaan</h3>
    <div class="profile-grid" id="profileGrid"></div>`;
  const pg = document.getElementById('profileGrid');
  constituencyProfiles.forEach(p => {{
    pg.innerHTML += `<div class="card profile-card">
      <h4>${{p.code}} — ${{p.name}} <span class="badge badge-pending">${{p.priority}}</span></h4>
      <dl>
        <dt>Demografi</dt><dd>${{p.demografi}}</dd>
        <dt>Ekonomi</dt><dd>${{p.ekonomi}}</dd>
        <dt>Tempatan</dt><dd>${{p.tempatan}}</dd>
        <dt>Agama/Identiti</dt><dd>${{p.agamaIdentiti}}</dd>
        <dt>Pengundi atas pagar</dt><dd>${{p.fenceSitters}}</dd>
        <dt>Kekuatan calon</dt><dd>${{p.calonStrength}}</dd>
        ${{p.jenteraStatus ? `<dt>Jentera</dt><dd>${{p.jenteraStatus}} · Cula ${{p.culaPct||'—'}}% · BKC ${{p.bkcCula||'—'}}</dd>` : ''}}
      </dl>
    </div>`;
  }});
}}

function renderProjections(root) {{
  const cases = ['bestCase','baseCase','worstCase'];
  const labels = {{ bestCase:'Best Case PAS', baseCase:'Base Case', worstCase:'Worst Case PAS' }};
  root.innerHTML = `
    <div class="tabs" id="projTabs">${{cases.map((c,i)=>`<div class="tab${{i===1?' active':''}}" data-proj="${{c}}">${{labels[c]}}</div>`).join('')}}</div>
    <div id="projPanels"></div>
    <h3 class="section-title" style="margin-top:24px">Impak Swing</h3>
    <div class="grid-2" style="margin-bottom:16px">
      <div class="card chart-card"><div class="card-label">Visualisasi Impak Swing Kerusi</div><div class="chart-box sm"><canvas id="chartSwing"></canvas></div></div>
      <div class="table-wrap"><table aria-label="Impak swing senario"><thead><tr><th>Senario</th><th>Δ PAS</th><th>Δ PN</th><th>Δ PH</th><th>Nota</th></tr></thead><tbody>
      ${{projectionData.swingImpacts.map(s=>`<tr><td>${{s.scenario}}</td><td style="color:${{s.pasDelta>=0?'var(--pos)':'var(--neg)'}}">${{s.pasDelta>0?'+':''}}${{s.pasDelta}}</td><td>${{s.pnDelta>0?'+':''}}${{s.pnDelta}}</td><td>${{s.phDelta>0?'+':''}}${{s.phDelta}}</td><td style="color:var(--muted)">${{s.note}}</td></tr>`).join('')}}
    </tbody></table></div></div>
    <div class="grid-3">
      <div class="card"><div class="card-label">Pantau Minggu Ini</div><ul class="rank-list">${{projectionData.recommendations.monitorWeek.map(x=>`<li>${{x}}</li>`).join('')}}</ul></div>
      <div class="card"><div class="card-label">Prioriti Crawler</div><ul class="rank-list">${{projectionData.recommendations.crawlerPriority.map(x=>`<li>${{x}}</li>`).join('')}}</ul></div>
      <div class="card"><div class="card-label">Deep Monitoring</div><ul class="rank-list">${{projectionData.recommendations.deepMonitoring.map(x=>`<li><strong>${{x}}</strong></li>`).join('')}}</ul></div>
    </div>`;
  const pp = document.getElementById('projPanels');
  cases.forEach((c,i) => {{
    const d = projectionData[c];
    const seats = d.seats;
    pp.innerHTML += `<div class="tab-panel${{i===1?' active':''}}" data-projpanel="${{c}}">
      <div class="grid-2">
        <div class="card chart-card"><div class="chart-box"><canvas id="chartProj_${{c}}"></canvas></div></div>
        <div class="card"><div class="card-label">${{d.label}}</div><p style="font-size:13px;margin:10px 0">${{d.summary}}</p>
          <p style="font-size:11px;color:var(--muted)"><strong>Andaian:</strong> ${{d.assumptions.join(' · ')}}</p>
          <p style="font-size:11px;color:var(--neg);margin-top:8px"><strong>Risiko:</strong> ${{d.risks.join(' · ')}}</p>
        </div>
      </div>
    </div>`;
  }});
  root.querySelectorAll('.tab').forEach(tab => tab.onclick = () => {{
    root.querySelectorAll('#projTabs .tab').forEach(t => t.classList.remove('active'));
    root.querySelectorAll('[data-projpanel]').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    root.querySelector(`[data-projpanel="${{tab.dataset.proj}}"]`).classList.add('active');
  }});
  cases.forEach(c => {{
    const d = projectionData[c];
    charts['proj_'+c] = new Chart(document.getElementById('chartProj_'+c), {{
      type: 'bar',
      data: {{ labels: Object.keys(d.seats), datasets: [{{ data: Object.values(d.seats), backgroundColor: ['#1a7f5a','#1e4fa8','#c8102e','#e84393','#64748b'] }}] }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: d.label }} }}, scales: {{ y: {{ beginAtZero: true, max: 20 }} }} }}
    }});
  }});
  const sw = projectionData.swingImpacts;
  if (document.getElementById('chartSwing')) {{
    charts.swing = new Chart(document.getElementById('chartSwing'), {{
      type: 'bar',
      data: {{
        labels: sw.map(s => s.scenario),
        datasets: [
          {{ label: 'Δ PAS', data: sw.map(s => s.pasDelta), backgroundColor: '#1a7f5a' }},
          {{ label: 'Δ PN', data: sw.map(s => s.pnDelta), backgroundColor: '#1e4fa8' }},
          {{ label: 'Δ PH', data: sw.map(s => s.phDelta), backgroundColor: '#e84393' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});
  }}
}}

function fmtEng(v) {{
  if (v === '—' || v == null || v === undefined) return '—';
  const n = Number(v);
  if (isNaN(n)) return String(v);
  if (n >= 1e6) return (n/1e6).toFixed(1)+'M';
  if (n >= 1000) return n.toLocaleString();
  return String(n);
}}

function animateCountUp(el, target, duration) {{
  if (!el || target == null || isNaN(Number(target))) return;
  const end = Number(target);
  const start = 0;
  const t0 = performance.now();
  const step = (now) => {{
    const p = Math.min((now - t0) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = Math.round(start + (end - start) * eased);
    el.textContent = val >= 1000 ? val.toLocaleString() : String(val);
    if (p < 1) requestAnimationFrame(step);
  }};
  requestAnimationFrame(step);
}}

function renderHybridLayerCard(l, lm) {{
  const meta = lm || {{}};
  const sampleN = l.id === 'public_voice'
    ? (Number(l.comments) || 0)
    : l.id === 'socmed_master'
      ? (Number(l.crawlGlobal || l.posts) || 0)
      : (Number(l.posts) || 0);
  const hasSentiment = sampleN > 0 && l.negPct != null && !Number.isNaN(Number(l.negPct));
  const neg = hasSentiment ? Number(l.negPct) : null;
  const pos = neg != null ? Math.max(0, 100 - neg - 30) : null;
  const neu = neg != null ? 30 : null;
  const sentBar = hasSentiment ? `
    <div class="layer-sent-bar" title="Anggaran sentimen">
      <div class="pos" style="width:${{pos}}%"></div>
      <div class="neu" style="width:${{neu}}%"></div>
      <div class="neg" style="width:${{neg}}%"></div>
    </div>
    <div style="font-size:10px;color:var(--muted)">Neg ${{neg}}% · Pos ~${{pos}}% · Neutral ~${{neu}}%</div>` : (l.id === 'public_voice' && sampleN === 0 ? `
    <div style="font-size:11px;color:var(--warn);margin:8px 0;padding:8px;border-radius:8px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25)">
      ${{l.emptyNote || 'Pipeline OK — artikel semasa tiada komen pembaca. Bukan ralat crawl.'}}
    </div>` : '');
  const mainMetric = l.id === 'socmed_master'
    ? (l.crawlGlobal || l.posts)
    : l.id === 'public_voice' && sampleN === 0
      ? '—'
      : (l.posts ?? '—');
  const metricLabel = l.id === 'socmed_master' ? 'rows crawl' : l.id === 'public_voice' ? 'komen pembaca' : 'posts';
  return `
    <div class="hybrid-layer-card enhanced">
      <div class="layer-head">
        <h4>${{l.icon || ''}} ${{l.label}}</h4>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          <span class="layer-tier">${{meta.tier || '—'}}</span>
          <span class="layer-status ${{meta.status || 'pending'}}">${{meta.statusLabel || '—'}}</span>
        </div>
      </div>
      <div class="layer-big-num count-up" data-count="${{typeof mainMetric === 'number' ? mainMetric : ''}}">${{typeof mainMetric === 'number' ? mainMetric.toLocaleString() : mainMetric}}</div>
      <div style="font-size:11px;color:var(--muted)">${{metricLabel}} · ${{meta.sample || ''}}</div>
      ${{sentBar}}
      <div class="source-metrics" style="margin-top:10px">
        ${{l.id !== 'socmed_master' ? `<span>Posts <strong>${{l.posts ?? '—'}}</strong></span>` : ''}}
        <span>Komen <strong>${{typeof l.comments === 'number' ? l.comments.toLocaleString() : (l.comments ?? '—')}}</strong></span>
        <span>Engagement <strong>${{fmtEng(l.engagement)}}</strong></span>
      </div>
      <div class="quality-track"><div class="quality-fill" style="width:${{meta.quality || 50}}%"></div></div>
      <div style="font-size:10px;color:var(--muted);margin-top:6px">${{meta.models || l.mode || ''}}</div>
      <div style="font-size:11px;color:var(--muted);margin-top:6px">${{l.desc || ''}}</div>
      <div class="endpoint" style="margin-top:6px">${{l.path || ''}}</div>
    </div>`;
}}

function renderSources(root) {{
  const hm = hybridModel || {{}};
  const cred = hm.credibility || {{}};
  const hero = hm.crawlHero || {{}};
  const layers = hm.layers || [];
  const tot = hm.totals || {{}};
  const layerMetaMap = Object.fromEntries((cred.layerMeta || []).map(m => [m.id, m]));
  const trustItems = (cred.trustStrip || []).map(t => `
    <div class="trust-item">
      <i data-lucide="${{t.icon || 'check'}}"></i>
      <strong>${{t.label}}</strong>
      <span>${{t.sub || ''}}</span>
    </div>`).join('');
  const insightCards = (cred.insights || []).map(i => `
    <div class="insight-card sev-${{i.severity || 'info'}}">
      <strong>${{i.title || ''}}</strong>
      <p>${{i.body || ''}}</p>
    </div>`).join('');
  const layerCards = layers.map(l => renderHybridLayerCard(l, layerMetaMap[l.id]));
  root.innerHTML = `
    <div class="exec-briefing">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px">
        <div>
          <div class="card-label" style="color:var(--gold)">Executive Briefing · InsightPulse Intelligence</div>
          <h3>${{cred.executiveHeadline || 'Pipeline hybrid aktif.'}}</h3>
          <div class="exec-sub">Kemaskini: ${{cred.updatedAt || META.lastUpdated || '—'}} · Metodologi telus · 3 lapisan tidak dicampur</div>
        </div>
        <span class="badge badge-live"><i data-lucide="shield-check" style="width:12px;height:12px"></i> VERIFIED PIPELINE</span>
      </div>
      ${{insightCards ? `<div class="insight-grid">${{insightCards}}</div>` : ''}}
    </div>
    <div class="trust-strip">${{trustItems}}</div>
    <div class="hybrid-banner" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">Crawl Minggu Lepas · PAS-Break Master</div>
          <strong class="count-up" style="font-size:36px;color:var(--gold);font-variant-numeric:tabular-nums" data-count="${{hero.totalPostsCrawled || tot.totalPostsCrawled || 68256}}">${{(hero.totalPostsCrawled || tot.totalPostsCrawled || 68256).toLocaleString()}}</strong>
          <span style="font-size:14px;margin-left:8px">Total Posts Crawled</span>
        </div>
        <div style="text-align:right;font-size:12px;color:var(--muted)">
          <div>${{hero.postRows?.toLocaleString?.() || tot.postRowsGlobal?.toLocaleString?.() || '—'}} post rows · ${{hero.commentRows?.toLocaleString?.() || tot.commentRowsGlobal?.toLocaleString?.() || '—'}} comment rows</div>
          <div>🌍 Engagement: <strong class="count-up" data-count="${{hero.engagementGlobal || tot.engagementGlobal || 0}}">${{fmtEng(hero.engagementGlobal || tot.engagementGlobal)}}</strong></div>
        </div>
      </div>
      <div class="hybrid-totals" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
        <span>🗳 <strong>PRN broad:</strong> ${{hero.prnPosts || tot.prnMentions || '—'}} mention · ⚡ ${{fmtEng(hero.prnEngagement)}}</span>
        <span>📂 <code style="font-size:10px">${{hero.source || 'pas_break_2026/master/'}}</code></span>
      </div>
    </div>
    <div class="hybrid-banner">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <strong style="font-size:16px">🧠 ${{hm.title || 'Hybrid Intelligence Model'}}</strong>
          <div style="font-size:12px;color:var(--muted);margin-top:4px">${{hm.subtitle || '3 lapisan berasingan'}}</div>
        </div>
        <span class="badge badge-live">HYBRID · LIVE</span>
      </div>
      <div class="hybrid-layers">${{layerCards}}</div>
      <div class="hybrid-totals">
        <span>📰 Berita: <strong>${{tot.newsArticles?.toLocaleString?.() || tot.newsArticles || 0}}</strong></span>
        <span>🔗 Direct: <strong>${{tot.directScrape || 0}}</strong></span>
        <span>📡 Google RSS: <strong>${{tot.googleNewsRss || 0}}</strong></span>
        <span>📱 Total Crawled: <strong>${{(tot.totalPostsCrawled || tot.masterRows || 0).toLocaleString()}}</strong></span>
        <span>🌍 Engagement: <strong>${{fmtEng(tot.engagementGlobal)}}</strong></span>
      </div>
      <div class="methodology-box">
        <strong style="font-size:12px">Metodologi & Kepercayaan Data</strong>
        <ul>${{(cred.methodology || []).map(m => `<li>${{m}}</li>`).join('')}}</ul>
      </div>
    </div>
    <h3 class="section-title">Registry Sumber Data <span>InsightPulse · posts · engagement · path</span></h3>
    <div class="source-grid">${{dataSources.map(s=>`
      <div class="card source-card${{String(s.name||'').includes('Hybrid Model')?' hybrid-layer':''}}">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>${{s.name}}</strong>
          <span class="badge ${{s.status==='active'?'badge-live':s.status==='pending'?'badge-pending':'badge-pending'}}">${{s.status}}</span>
        </div>
        <div class="source-metrics">
          <span>Posts <strong>${{s.posts ?? '—'}}</strong></span>
          <span>Komen <strong>${{s.comments ?? '—'}}</strong></span>
          <span>Engagement <strong>${{fmtEng(s.engagement)}}</strong></span>
          ${{s.layer ? `<span>${{s.layer}}</span>` : ''}}
        </div>
        <div style="font-size:12px;color:var(--muted)">${{s.note}}</div>
        <div style="display:flex;gap:12px;font-size:11px;margin-top:4px"><span>Kekerapan: ${{s.frequency}}</span><span>Kesediaan: ${{s.readiness}}</span></div>
        <div class="endpoint">${{s.endpoint}}</div>
      </div>`).join('')}}</div>
    <div class="card" style="margin-top:20px">
      <div class="card-label">Nota Integrasi Hybrid</div>
      <p style="font-size:13px;color:var(--muted);margin-top:8px;line-height:1.6">
        <strong>Lapisan 1 Media Tone</strong> — artikel direct scrape + ML Tier A (jangan campur dengan socmed).<br>
        <strong>Lapisan 2 Public Voice</strong> — komen pembaca Coral/FMT (pending — artikel semasa tiada komen).<br>
        <strong>Lapisan 3 Socmed Master</strong> — FB/TikTok/X filter NS · engagement dari likes+shares+views.<br>
        <strong>Total Posts Crawled</strong> = ${{(tot.totalPostsCrawled || tot.masterRows || 68256).toLocaleString()}} rows (master minggu lepas) · NS fokus ${{(hero.nsPosts || '—')}} mention · ${{(hero.nsComments||0).toLocaleString()}} komen.<br>
        <strong>Folder:</strong> <code>PRN/PRN_N9/</code> (negeri) · <code>pas_break_2026/master/</code> (cross-state).<br>
        <strong>Engagement</strong> = ${{fmtEng(tot.engagementGlobal)}} dari keseluruhan crawl.
      </p>
    </div>`;
  root.querySelectorAll('[data-count]').forEach(el => {{
    const n = el.getAttribute('data-count');
    if (n && !isNaN(Number(n)) && Number(n) > 0) animateCountUp(el, Number(n), 1400);
  }});
  lucide.createIcons();
}}

function showTip(e, html) {{
  const t = document.getElementById('tooltip');
  t.innerHTML = html;
  t.classList.add('show');
  t.style.left = (e.clientX + 12) + 'px';
  t.style.top = (e.clientY + 12) + 'px';
}}
function hideTip() {{ document.getElementById('tooltip').classList.remove('show'); }}

function openDrawer(seat) {{
  document.getElementById('drawerBody').innerHTML = `
    <div style="color:var(--muted);font-size:12px">${{seat.code}} · ${{seat.parlimen}}</div>
    <h3 class="display">${{seat.name}}</h3>
    <div style="margin:16px 0;display:flex;gap:8px;flex-wrap:wrap">
      <span class="pill" style="background:${{PARTY_COLORS[seat.party2023]}}33;color:${{PARTY_COLORS[seat.party2023]}}">${{seat.party2023}}</span>
      <span class="badge badge-pending">${{seat.areaType}}</span>
    </div>
    <dl style="display:grid;grid-template-columns:110px 1fr;gap:8px;font-size:13px">
      <dt style="color:var(--muted)">Penyandang</dt><dd>${{seat.winnerName}}</dd>
      <dt style="color:var(--muted)">Blok 2023</dt><dd>${{seat.winner2023}}</dd>
      <dt style="color:var(--muted)">Majoriti</dt><dd>${{seat.majority.toLocaleString()}} undi</dd>
      <dt style="color:var(--muted)">Undi menang</dt><dd>${{seat.votesWon.toLocaleString()}}</dd>
      <dt style="color:var(--muted)">Pencabar</dt><dd>${{seat.challenger}} (${{seat.challengerParty}})</dd>
      <dt style="color:var(--muted)">Minat PAS</dt><dd>${{seat.pasInterest}}</dd>
      <dt style="color:var(--muted)">3 Penjuru</dt><dd>${{seat.threeCornerRisk}}</dd>
      <dt style="color:var(--muted)">Kategori PAS</dt><dd><span class="cat-pill ${{catClass(seat.kategoriPas)}}">${{catLabel(seat.kategoriPas)}}</span> · ${{seat.kategoriMarginLabel || seat.kategoriMargin}}</dd>
      <dt style="color:var(--muted)">Ramalan PAS</dt><dd><strong>${{seat.pasWinProb}}%</strong> — ${{seat.predictionLabel}} (${{seat.predictionConfidence}})</dd>
      <dt style="color:var(--muted)">Prediksi 2026</dt><dd>${{seat.predictedParty}} (${{seat.predictedBloc}})</dd>
      <dt style="color:var(--muted)">Senario</dt><dd>Solo ${{seat.scenarioPasSolo}}% · PN ${{seat.scenarioPasPn}}% · MN ${{seat.scenarioPasMn}}%</dd>
      <dt style="color:var(--muted)">Pengundi</dt><dd>${{(seat.registeredVotersDpi || seat.registeredVoters || 0).toLocaleString()}} berdaftar (${{seat.registeredVotersDpi ? 'DPI Dec 2025' : 'PRN 2023'}})</dd>
      ${{seat.pctMelayu != null ? `<dt style="color:var(--muted)">Demografi</dt><dd>Melayu ${{seat.pctMelayu}}% · Cina ${{seat.pctCina||0}}% · India ${{seat.pctIndia||0}}%</dd>` : ''}}
      ${{seat.culaPct != null ? `<dt style="color:var(--muted)">Cula PAS</dt><dd>${{seat.culaPasTotal?.toLocaleString() || '—'}} pengundi (${{seat.culaPct}}%) · SKT 51%: ${{seat.skt51?.toLocaleString() || '—'}} · BKC: <span style="color:${{(seat.bkcCula||0)<0?'var(--neg)':'var(--pos)'}}">${{seat.bkcCula?.toLocaleString() || '—'}}</span></dd>` : ''}}
      ${{seat.jenteraStatus ? `<dt style="color:var(--muted)">Jentera</dt><dd>${{seat.jenteraStatus}}${{seat.markahSlu ? ' · SLU: ' + seat.markahSlu : ''}}</dd>` : ''}}
      ${{seat.mnCalon ? `<dt style="color:var(--muted)">Cadangan MN</dt><dd>${{seat.mnCalon}}${{seat.mnCatatan ? ' — ' + seat.mnCatatan : ''}}</dd>` : ''}}
      <dt style="color:var(--muted)">Mention berita</dt><dd>${{seat.newsMentions || 0}} (crawl ADUN seed 30h)</dd>
      ${{seat.socialCrawlHeadlines && seat.socialCrawlHeadlines.length ? `<dt style="color:var(--muted)">Headline</dt><dd style="font-size:12px">${{seat.socialCrawlHeadlines[0]}}</dd>` : ''}}
    </dl>
    <div class="card" style="margin-top:16px;background:var(--surface-2)">
      <div class="card-label">Catatan Strategik</div>
      <p style="font-size:13px;margin-top:6px">${{seat.strategicNote}}</p>
    </div>
    ${{typeof renderDrawerPlaybook === 'function' ? renderDrawerPlaybook(seat) : ''}}`;
  document.getElementById('drawerOverlay').classList.add('open');
  lucide.createIcons();
}}
document.getElementById('drawerClose').onclick = () => closeDrawer();
document.getElementById('drawerOverlay').onclick = e => {{ if (e.target.id === 'drawerOverlay') closeDrawer(); }};
function closeDrawer() {{ document.getElementById('drawerOverlay').classList.remove('open'); document.getElementById('drawerClose').focus(); }}

document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeDrawer();
  if (e.altKey && e.key >= '1' && e.key <= '9') {{
    e.preventDefault();
    switchSection(NAV[+e.key - 1].id);
  }}
}});

document.getElementById('filterChips').querySelectorAll('.chip').forEach(chip => {{
  chip.onclick = () => {{
    document.querySelectorAll('#filterChips .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    seatFilter.bloc = chip.dataset.filter;
    if (activeSection !== 'seats') switchSection('seats');
    else renderSection();
  }};
}});

document.getElementById('menuToggle')?.addEventListener('click', () => document.getElementById('sidebar').classList.toggle('open'));

function exportMock(type) {{
  alert('Export ' + type.toUpperCase() + ' — placeholder visual. Sambung ke API export apabila live.');
}}

// Init
{scenario_engine_js()}
__WAR_ROOM_JS__
(function updateCrawlMeta() {{
  const sm = socialSentiment.meta || {{}};
  const hm = hybridModel.crawlHero || hybridModel.totals || {{}};
  const el = document.getElementById('crawlMeta');
  if (!el) return;
  const n = sm.totalPostsCrawled || sm.masterTotal || hm.totalPostsCrawled || 68256;
  const ns = sm.totalPosts || hm.nsPosts || 0;
  const kom = (sm.engagementNS || {{}}).commentsCount || (sm.engagementNS || {{}}).comments || hm.nsComments || 0;
  el.textContent = `Socmed master ${{n.toLocaleString()}} rows crawled · NS ${{ns}} mention · ${{Number(kom).toLocaleString()}} komen`;
}})();
renderNav();
renderSection();
window.addEventListener('resize', () => Object.values(charts).forEach(c => c.resize && c.resize()));
</script>
</body>
</html>"""
    return html.replace("__WAR_ROOM_JS__", war_room_js)


def main():
    try:
        from n9_dpi_updates import save_json
        save_json()
    except Exception as exc:
        print(f"⚠️ DPI refresh: {exc}")

    py = ROOT / "NEImpulse" / "bin" / "python"
    if not py.exists():
        py = Path(sys.executable)
    for script in ("build_n9_ml_predictions.py", "build_cina_narrative_dashboard.py"):
        sp = ROOT / "scripts" / script
        if not sp.exists():
            continue
        r = subprocess.run([str(py), str(sp)], cwd=str(ROOT), capture_output=True, text=True)
        if r.returncode == 0:
            line = (r.stdout or "").strip().splitlines()[-1] if r.stdout else f"OK — {script}"
            print(line)
        else:
            print(f"⚠️ {script}: {(r.stderr or r.stdout or 'failed').strip()[:200]}")

    seats, pas, analytics = load_data()
    economic_outlook = extract_economic_outlook()
    adun_social = load_adun_social_summary()
    prn_dates = load_prn_dates()
    war_room = build_war_room_payload(seats, find_latest_pas_master())
    save_war_room(war_room)
    mock = build_mock_data(seats, pas, economic_outlook)
    html = generate_html(seats, mock, pas, analytics, adun_social, war_room, prn_dates)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    OUT_COPY.parent.mkdir(parents=True, exist_ok=True)
    OUT_COPY.write_text(html, encoding="utf-8")
    print(f"Generated: {OUT}")
    print(f"Copy:      {OUT_COPY}")
    wr = war_room.get("summary", {})
    ml = mock.get("mlAnalytics") or {}
    nar = mock.get("narrativeIntel") or {}
    rf_acc = ((ml.get("predictive") or {}).get("models") or {}).get("random_forest", {}).get("cv_accuracy_mean")
    rf_s = f"{rf_acc:.0%}" if rf_acc else "—"
    print(
        f"Seats: {len(seats)} | PAS defend: {analytics.get('kategoriPas',{}).get('defend',0)} | "
        f"Predicted PAS wins: {analytics.get('predictedPasWins',0)} | ML tier: {ml.get('analytics_tier','—')} RF CV {rf_s} | "
        f"Narrative: {(nar.get('totals') or {}).get('records', 0)} rows | "
        f"War Room actions: {wr.get('total_actions',0)} | Triggers: {wr.get('triggers_active',0)} | "
        f"Size: {OUT.stat().st_size // 1024} KB"
    )


if __name__ == "__main__":
    main()
