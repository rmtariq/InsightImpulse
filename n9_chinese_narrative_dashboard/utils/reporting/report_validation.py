"""Data validation for executive reports."""
from __future__ import annotations

from typing import Any

import pandas as pd

from utils.reporting.labels import UNCLASSIFIED, normalize_issue


def sentiment_counts(df: pd.DataFrame) -> dict[str, Any]:
    n = len(df) if df is not None and not df.empty else 0
    if n == 0:
        return {
            "positive": 0, "neutral": 0, "negative": 0, "unknown": 0,
            "labelled": 0, "total": 0,
            "pct_positive": 0.0, "pct_neutral": 0.0, "pct_negative": 0.0, "pct_unknown": 0.0,
            "pct_sum": 0.0, "valid": True, "warning": "",
        }
    sent = df["sentiment"].astype(str).str.lower().str.strip() if "sentiment" in df.columns else pd.Series(dtype=str)
    pos = int((sent == "positive").sum())
    neu = int((sent == "neutral").sum())
    neg = int((sent == "negative").sum())
    labelled = pos + neu + neg
    unknown = n - labelled
    denom = max(labelled, 1)
    pp = round(pos / denom * 100, 1)
    pn = round(neu / denom * 100, 1)
    pg = round(neg / denom * 100, 1)
    pu = round(unknown / max(n, 1) * 100, 1)
    pct_sum = round(pp + pn + pg, 1)
    valid = 99.0 <= pct_sum <= 100.1 if labelled else True
    warning = ""
    if unknown:
        warning = f"Sentimen dilabel: {labelled:,} daripada {n:,} hantaran ({unknown:,} belum dilabel)."
    if not valid:
        warning += " Amaran: taburan sentimen tidak menjumlah ~100% — semak data."
    return {
        "positive": pos, "neutral": neu, "negative": neg, "unknown": unknown,
        "labelled": labelled, "total": n,
        "pct_positive": pp, "pct_neutral": pn, "pct_negative": pg, "pct_unknown": pu,
        "pct_sum": pct_sum, "valid": valid, "warning": warning.strip(),
    }


def issue_trend(grp: pd.DataFrame) -> dict[str, Any]:
    if grp.empty or "published_at" not in grp.columns:
        return {"label": "Data Tidak Mencukupi", "detail": "", "neg_early": None, "neg_late": None}
    s = grp.dropna(subset=["published_at"]).sort_values("published_at")
    if len(s) < 8:
        return {"label": "Data Tidak Mencukupi", "detail": "", "neg_early": None, "neg_late": None}
    mid = s["published_at"].iloc[len(s) // 2]
    early = s[s["published_at"] < mid]
    late = s[s["published_at"] >= mid]
    if early.empty or late.empty or "sentiment" not in s.columns:
        return {"label": "Stabil", "detail": "", "neg_early": None, "neg_late": None}
    e_neg = (early["sentiment"].astype(str).str.lower() == "negative").mean() * 100
    l_neg = (late["sentiment"].astype(str).str.lower() == "negative").mean() * 100
    diff = round(l_neg - e_neg, 1)
    rel = round((diff / e_neg * 100) if e_neg else 0, 1)
    if diff > 3:
        label = "Meningkat"
        detail = (
            f"Sentimen negatif naik daripada {e_neg:.1f}% kepada {l_neg:.1f}%, "
            f"peningkatan {abs(diff)} mata peratusan ({abs(rel):.1f}% relatif)."
        )
    elif diff < -3:
        label = "Menurun"
        detail = (
            f"Sentimen negatif turun daripada {e_neg:.1f}% kepada {l_neg:.1f}%, "
            f"penurunan {abs(diff)} mata peratusan ({abs(rel):.1f}% relatif)."
        )
    else:
        label = "Stabil"
        detail = f"Sentimen negatif relatif stabil ({e_neg:.1f}% → {l_neg:.1f}%)."
    return {"label": label, "detail": detail, "neg_early": round(e_neg, 1), "neg_late": round(l_neg, 1)}


def location_display(row: pd.Series) -> tuple[str, str, str]:
    """Return (display_location, confidence_note, verification)."""
    loc = str(row.get("constituency") or row.get("district") or "").strip()
    dun = str(row.get("dun_code") or "").strip()
    if loc and loc.lower() not in ("nan", "none", ""):
        return loc, "", "Disahkan" if dun else "Perlu disahkan"
    if dun and dun.lower() not in ("nan", "none"):
        return dun, "Lokasi perlu disahkan.", "Perlu disahkan"
    return "—", "Lokasi perlu disahkan.", "Belum disahkan"


def data_reliability(df: pd.DataFrame) -> dict[str, Any]:
    n = len(df) if df is not None and not df.empty else 0
    if n == 0:
        return {"status": "Rendah", "rows": [], "has_sample": False, "warning": "Tiada data."}
    rows = []
    missing_url = 0
    unverified_loc = 0
    unknown_sent = sentiment_counts(df)["unknown"]
    unclassified = 0
    sample = 0
    if "source_url" in df.columns:
        missing_url = int(df["source_url"].astype(str).str.strip().isin(["", "nan", "None"]).sum())
    if "issue_cluster" in df.columns:
        unclassified = int(df["issue_cluster"].apply(normalize_issue).eq(UNCLASSIFIED).sum())
    if "data_source" in df.columns:
        sample = int(df["data_source"].astype(str).str.lower().str.contains("sample|synthetic|simul", na=False).sum())
    elif "post_id" in df.columns:
        sample = int(df["post_id"].astype(str).str.startswith("SAMPLE").sum())

    for label, val in [
        ("Jumlah rekod", n),
        ("URL tiada", missing_url),
        ("Lokasi belum disahkan", unverified_loc),
        ("Sentimen belum dilabel", unknown_sent),
        ("Belum Diklasifikasikan", unclassified),
        ("Rekod simulasi/contoh", sample),
    ]:
        rows.append([label, str(val)])

    pct_uncl = unclassified / max(n, 1) * 100
    status = "Tinggi"
    if sample > 0 or pct_uncl > 15 or unknown_sent > n * 0.1:
        status = "Rendah" if sample > n * 0.2 else "Sederhana"
    warning = ""
    if sample:
        warning = "Laporan ini mengandungi data simulasi dan tidak boleh dianggap sebagai gambaran sebenar sentimen awam."
    elif pct_uncl > 15:
        warning = (
            "Sebahagian besar rekod masih belum diklasifikasikan. "
            "Dapatan isu perlu ditafsir dengan berhati-hati sehingga proses semakan selesai."
        )
    return {"status": status, "rows": rows, "has_sample": sample > 0, "warning": warning, "pct_unclassified": round(pct_uncl, 1)}
