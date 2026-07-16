"""
Unified data ingest for InsightPulse — social crawl + upload + external feeds.
Supports structured, semi-structured, and unstructured inputs per analysis type.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
UPLOADS_DIR = ROOT / "data" / "uploads"
TEMPLATES_DIR = ROOT / "data" / "templates"
FEEDS_DIR = ROOT / "data" / "feeds"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ANALYSIS_TYPES: Dict[str, Dict[str, Any]] = {
    "social_listening": {
        "label": "Social Listening",
        "icon": "headphones",
        "description": "Monitor public conversation, sentiment, and narrative trends.",
        "recommended_sources": ["social_crawl"],
        "dashboard": "sentiment_overview",
    },
    "sme_insights": {
        "label": "SME Insights",
        "icon": "shop",
        "description": "PMKS market pressure, cashflow signals, and sector outlook.",
        "recommended_sources": ["social_crawl", "upload", "feed"],
        "dashboard": "portfolio_intelligence",
    },
    "issue_detection": {
        "label": "Issue Detection",
        "icon": "alert",
        "description": "Detect hotspots, complaints, and emerging crisis signals.",
        "recommended_sources": ["social_crawl", "upload"],
        "dashboard": "issue_ops",
    },
    "competitor_analysis": {
        "label": "Competitor Analysis",
        "icon": "search",
        "description": "Compare share of voice, positioning, and engagement.",
        "recommended_sources": ["social_crawl", "feed"],
        "dashboard": "competitive_intel",
    },
    "product_intelligence": {
        "label": "Product Intelligence",
        "icon": "box",
        "description": "Product demand, complaints, and feature-gap signals.",
        "recommended_sources": ["social_crawl", "upload"],
        "dashboard": "product_intel",
    },
    "market_research": {
        "label": "Market Research",
        "icon": "chart",
        "description": "Segment demand, supply pressure, and market direction.",
        "recommended_sources": ["social_crawl", "feed", "upload"],
        "dashboard": "market_research",
    },
    "brand_monitoring": {
        "label": "Brand Monitoring",
        "icon": "shield",
        "description": "Brand health, reputation risk, and response priorities.",
        "recommended_sources": ["social_crawl", "feed"],
        "dashboard": "brand_health",
    },
    "portfolio_intelligence": {
        "label": "Portfolio Intelligence",
        "icon": "bank",
        "description": "EWS watchlist, borrower signals, and financing advisory.",
        "recommended_sources": ["social_crawl", "upload", "feed", "hybrid"],
        "dashboard": "smebank_portfolio",
    },
    "field_operations": {
        "label": "Field Operations / Cula",
        "icon": "map",
        "description": "Field reports, DUN coverage, door-to-door and cula metrics.",
        "recommended_sources": ["upload", "social_crawl"],
        "dashboard": "war_room_field",
    },
    "economy_outlook": {
        "label": "Policy & Economy Outlook",
        "icon": "globe",
        "description": "Macro indicators, sector outlook, and policy impact.",
        "recommended_sources": ["feed", "social_crawl", "hybrid"],
        "dashboard": "economy_industry",
    },
    "public_complaint": {
        "label": "Public Complaint Monitor",
        "icon": "megaphone",
        "description": "Agency complaint logs, public sentiment, and dispatch priorities.",
        "recommended_sources": ["social_crawl", "upload"],
        "dashboard": "agency_complaint",
    },
}

DATASET_TYPES = {
    "field_cula": {
        "label": "Field Report (Cula / Lapangan)",
        "template": "TEMPLATE_cula_field.csv",
        "required_any": [["dun", "DUN"], ["rumah", "houses", "doors"], ["cula", "CULA"]],
    },
    "borrower_list": {
        "label": "Borrower / Portfolio List",
        "template": "TEMPLATE_borrower_smebank.csv",
        "required_any": [["borrower", "peminjam", "company", "nama"]],
    },
    "complaint_log": {
        "label": "Complaint / Aduan Log",
        "template": "TEMPLATE_complaint_agency.csv",
        "required_any": [["complaint", "aduan", "issue", "text"]],
    },
    "economic_csv": {
        "label": "Economic / Indicator CSV",
        "template": "TEMPLATE_economic_indicator.csv",
        "required_any": [["indicator", "series", "value", "date"]],
    },
    "generic_csv": {
        "label": "Generic CSV / Excel (Save As CSV)",
        "template": None,
        "required_any": [],
    },
}

FEED_SOURCES = {
    "bnm": {
        "label": "Bank Negara Malaysia",
        "description": "OPR, NPL, SME lending indicators",
        "file": "bnm_indicators.json",
    },
    "bursa": {
        "label": "Bursa Malaysia",
        "description": "Sector index and market sentiment proxy",
        "file": "bursa_sectors.json",
    },
    "dosm": {
        "label": "DOSM",
        "description": "CPI, retail sales, employment, PMI",
        "file": "dosm_indicators.json",
    },
}


def list_analysis_types() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in ANALYSIS_TYPES.items()]


def list_templates() -> List[Dict[str, Any]]:
    out = []
    for key, meta in DATASET_TYPES.items():
        tpl = meta.get("template")
        out.append({
            "id": key,
            "label": meta["label"],
            "template": tpl,
            "download_url": f"/api/data/templates/{key}" if tpl else None,
        })
    return out


def list_feeds() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in FEED_SOURCES.items()]


def template_path(template_id: str) -> Path:
    meta = DATASET_TYPES.get(template_id)
    if not meta or not meta.get("template"):
        raise ValueError(f"Unknown template: {template_id}")
    path = TEMPLATES_DIR / meta["template"]
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path


def _normalize_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _read_csv_rows(path: Path, limit: int = 50000) -> tuple[List[str], List[Dict[str, str]]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append({k: (v or "").strip() for k, v in row.items()})
        return fields, rows


def detect_dataset_type(fields: List[str]) -> str:
    norm = {_normalize_col(c): c for c in fields}
    keys = set(norm.keys())
    for dtype, meta in DATASET_TYPES.items():
        if dtype == "generic_csv":
            continue
        for group in meta.get("required_any", []):
            if any(_normalize_col(g) in keys for g in group):
                return dtype
    if any(k in keys for k in ("text", "content", "body", "message")):
        return "generic_csv"
    return "generic_csv"


async def save_upload(file_content: bytes, filename: str, dataset_type: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    upload_id = uuid.uuid4().hex[:12]
    ext = Path(filename).suffix.lower() or ".csv"
    if ext not in (".csv", ".json", ".xlsx", ".xls"):
        ext = ".csv"
    dest_dir = UPLOADS_DIR / upload_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"source{ext}"
    dest.write_bytes(file_content)

    meta: Dict[str, Any] = {
        "upload_id": upload_id,
        "filename": filename,
        "path": str(dest),
        "dataset_type": dataset_type,
        "project_id": project_id,
        "uploaded_at": datetime.now().isoformat(),
        "rows": 0,
        "columns": [],
        "detected_type": dataset_type,
    }

    if ext == ".csv":
        fields, rows = _read_csv_rows(dest)
        detected = detect_dataset_type(fields) if dataset_type == "generic_csv" else dataset_type
        meta.update({
            "rows": len(rows),
            "columns": fields,
            "detected_type": detected,
            "preview": rows[:5],
        })
        summary = summarize_upload(dest, detected, fields, rows)
        meta["summary"] = summary
        (dest_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        if project_id:
            try:
                from backend.storage.project_registry import ensure_project_dirs
                proj_uploads = ensure_project_dirs(project_id)["root"] / "uploads"
                proj_uploads.mkdir(exist_ok=True)
                shutil.copy2(dest, proj_uploads / f"{upload_id}_{filename}")
            except Exception:
                pass

    return meta


def load_feed_data(feed_ids: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"feeds": [], "sector_outlook": [], "macro": {}}
    for fid in feed_ids:
        spec = FEED_SOURCES.get(fid)
        if not spec:
            continue
        fpath = FEEDS_DIR / spec["file"]
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        out["feeds"].append({"id": fid, "label": spec["label"], "data": data})
        if fid == "bursa" and "sectors" in data:
            out["sector_outlook"].extend(data["sectors"])
        if fid == "bnm" and "indicators" in data:
            out["macro"].update(data["indicators"])
        if fid == "dosm" and "indicators" in data:
            out["macro"].update(data["indicators"])
    return out


def summarize_upload(path: Path, dataset_type: str, fields: List[str], rows: List[Dict[str, str]]) -> Dict[str, Any]:
    norm_map = {_normalize_col(c): c for c in fields}

    def col(*names: str) -> Optional[str]:
        for n in names:
            k = _normalize_col(n)
            if k in norm_map:
                return norm_map[k]
        return None

    summary: Dict[str, Any] = {"dataset_type": dataset_type, "row_count": len(rows), "columns": fields}

    if dataset_type == "field_cula":
        dun_c = col("dun", "DUN", "kod_dun")
        rumah_c = col("rumah", "houses", "doors", "rumah_dilawati")
        cula_c = col("cula", "CULA", "contacts")
        duns = set()
        total_rumah = total_cula = 0
        for r in rows:
            if dun_c and r.get(dun_c):
                duns.add(r[dun_c].strip().upper())
            if rumah_c:
                try:
                    total_rumah += int(float(re.sub(r"[^\d.]", "", r.get(rumah_c, "0") or "0")))
                except ValueError:
                    pass
            if cula_c:
                try:
                    total_cula += int(float(re.sub(r"[^\d.]", "", r.get(cula_c, "0") or "0")))
                except ValueError:
                    pass
        summary.update({
            "dun_count": len(duns),
            "total_rumah": total_rumah,
            "total_cula": total_cula,
            "strategic_action": "Review DUN coverage gaps and redeploy field teams where cula/rumah ratio is low.",
            "tactical_action": "Validate top 5 DUN rows with lowest coverage within 24 hours.",
        })

    elif dataset_type == "borrower_list":
        name_c = col("borrower", "peminjam", "company", "nama", "name")
        sector_c = col("sector", "sektor", "industry")
        risk_c = col("risk", "status", "tier")
        high = medium = 0
        sectors: Dict[str, int] = {}
        for r in rows:
            if sector_c and r.get(sector_c):
                s = r[sector_c]
                sectors[s] = sectors.get(s, 0) + 1
            if risk_c:
                rv = (r.get(risk_c) or "").upper()
                if "HIGH" in rv or rv in ("H", "3"):
                    high += 1
                elif "MED" in rv or rv in ("M", "2"):
                    medium += 1
        summary.update({
            "borrower_count": len(rows),
            "high_risk": high,
            "medium_risk": medium,
            "sectors": sectors,
            "strategic_action": "Prioritise sector exposure review for top 3 sectors by borrower count.",
            "tactical_action": f"Contact {high} HIGH-risk accounts within 24–72 hours.",
        })

    elif dataset_type == "complaint_log":
        text_c = col("complaint", "aduan", "issue", "text", "description")
        area_c = col("area", "kawasan", "location", "lokasi")
        areas: Dict[str, int] = {}
        for r in rows:
            if area_c and r.get(area_c):
                a = r[area_c]
                areas[a] = areas.get(a, 0) + 1
        summary.update({
            "complaint_count": len(rows),
            "top_areas": sorted(areas.items(), key=lambda x: -x[1])[:5],
            "strategic_action": "Deploy resources to top complaint hotspots this week.",
            "tactical_action": "Assign case owners for unresolved high-severity complaints within 48 hours.",
        })

    else:
        text_c = col("text", "content", "body", "message", "Text")
        summary.update({
            "has_text_column": bool(text_c),
            "strategic_action": "Use text column for sentiment and narrative analysis if present.",
            "tactical_action": "Validate data quality and re-upload with standard template if mapping fails.",
        })
        if text_c and rows:
            summary["sample_texts"] = [r.get(text_c, "")[:120] for r in rows[:3] if r.get(text_c)]

    return summary


def build_unified_insights(
    analysis_type: str,
    data_source_mode: str,
    upload_summaries: List[Dict[str, Any]],
    feed_bundle: Dict[str, Any],
    crawl_result: Optional[Dict[str, Any]] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    at = ANALYSIS_TYPES.get(analysis_type, ANALYSIS_TYPES["social_listening"])
    key_insights: List[str] = []
    recommendations: List[str] = []

    key_insights.append(f"Analysis type: {at['label']}")
    key_insights.append(f"Data source mode: {data_source_mode.replace('_', ' ').title()}")

    for u in upload_summaries:
        s = u.get("summary") or {}
        key_insights.append(f"Upload {u.get('filename')}: {s.get('row_count', 0)} rows ({s.get('dataset_type', 'unknown')})")
        if s.get("total_cula") is not None:
            key_insights.append(f"Field ops total: {s.get('total_cula', 0)} cula · {s.get('total_rumah', 0)} rumah · {s.get('dun_count', 0)} DUN")
        if s.get("borrower_count") is not None:
            key_insights.append(f"Portfolio upload: {s.get('borrower_count', 0)} borrowers · {s.get('high_risk', 0)} HIGH · {s.get('medium_risk', 0)} MEDIUM")
        if s.get("complaint_count") is not None:
            key_insights.append(f"Complaint log: {s.get('complaint_count', 0)} records")
        if s.get("strategic_action"):
            recommendations.append(s["strategic_action"])
        if s.get("tactical_action"):
            recommendations.append(s["tactical_action"])

    if feed_bundle.get("feeds"):
        key_insights.append(f"External feeds attached: {', '.join(f['label'] for f in feed_bundle['feeds'])}")
        for sec in feed_bundle.get("sector_outlook", [])[:4]:
            key_insights.append(f"Sector {sec.get('name')}: {sec.get('status')} — {sec.get('note', '')}")
        recommendations.append("Cross-check sector outlook with social sentiment before financing or policy decisions.")

    if crawl_result:
        td = crawl_result.get("total_data_points") or crawl_result.get("summary", {}).get("total_records")
        if td:
            key_insights.append(f"Social crawl records analysed: {td:,}")

    if analysis_type == "portfolio_intelligence":
        recommendations.append("Activate EWS watchlist review for HIGH accounts within 24 hours.")
    elif analysis_type == "field_operations":
        recommendations.append("Sync field upload with war room dashboard and DUN drawer within the same day.")
    elif analysis_type == "economy_outlook":
        recommendations.append("Brief EXCO using macro feeds + industry traffic-light outlook.")

    ml_analytics: Dict[str, Any] = {}
    try:
        from backend.ml.predictive_engine import run_ml_analysis

        ml_analytics = run_ml_analysis(
            analysis_type=analysis_type,
            upload_summaries=upload_summaries,
            project_id=project_id,
        )
        if ml_analytics.get("success"):
            tier = ml_analytics.get("analytics_tier", "descriptive")
            key_insights.append(f"ML analytics tier: {tier}")
            if ml_analytics.get("predictive", {}).get("models"):
                for mname, mstats in ml_analytics["predictive"]["models"].items():
                    if mstats.get("cv_accuracy_mean") is not None:
                        key_insights.append(
                            f"ML {mname}: CV accuracy {mstats['cv_accuracy_mean']:.0%} · F1 {mstats.get('cv_f1_mean', 0):.0%}"
                        )
            for act in (ml_analytics.get("prescriptive_actions") or [])[:3]:
                recommendations.append(f"[ML {act.get('urgency', 'action').upper()}] {act.get('title')}")
    except Exception as exc:
        ml_analytics = {"success": False, "error": str(exc)}

    return {
        "analysis_type": analysis_type,
        "data_source_mode": data_source_mode,
        "analysis_type_label": at["label"],
        "recommended_dashboard": at["dashboard"],
        "upload_summaries": upload_summaries,
        "feed_bundle": feed_bundle,
        "key_insights": key_insights,
        "recommendations": list(dict.fromkeys(recommendations)),
        "crawl_result": crawl_result,
        "ml_analytics": ml_analytics,
        "unified": True,
    }


def load_upload_meta(upload_id: str) -> Optional[Dict[str, Any]]:
    meta_path = UPLOADS_DIR / upload_id / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return None
