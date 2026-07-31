"""
InsightPulse Predictive Analytics Engine
========================================
Descriptive → Predictive (SVM, Random Forest, Decision Tree) → Prescriptive

Domains: PRN seat competition, portfolio EWS, field cula, complaint hotspots.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

MIN_ROWS_PREDICTIVE = 25
MIN_ROWS_PRESCRIPTIVE = 40
MIN_POSITIVE_CLASS = 3

PRN_N9_SEATS_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/seats/n9_seats_analytics.json"
PRN_N9_SOCMED_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/socmed_by_dun_N9.json"
PRN_N9_ML_OUTPUT = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_ml_predictions.json"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _normalize_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _read_csv_rows(path: Path, limit: int = 50000) -> Tuple[List[str], List[Dict[str, str]]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append({k: (v or "").strip() for k, v in row.items()})
        return fields, rows


def load_upload_rows(upload_meta: Dict[str, Any]) -> List[Dict[str, str]]:
    path = upload_meta.get("path")
    if not path or not Path(path).exists():
        return []
    _, rows = _read_csv_rows(Path(path))
    return rows


def _sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


def _train_classifiers(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
) -> Dict[str, Any]:
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.svm import SVC
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import accuracy_score, f1_score

    n = len(y)
    pos = int(y.sum())
    neg = n - pos
    if pos < MIN_POSITIVE_CLASS or neg < MIN_POSITIVE_CLASS:
        return {
            "status": "insufficient_labels",
            "message": f"Need ≥{MIN_POSITIVE_CLASS} samples per class (got pos={pos}, neg={neg})",
            "n_samples": n,
        }

    cv_folds = min(5, pos, neg)
    if cv_folds < 2:
        cv_folds = 2

    models = {
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", CalibratedClassifierCV(SVC(kernel="rbf", class_weight="balanced"), cv=cv_folds)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=120, max_depth=5, min_samples_leaf=2,
            class_weight="balanced", random_state=42,
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=4, min_samples_leaf=2, class_weight="balanced", random_state=42,
        ),
    }

    results: Dict[str, Any] = {
        "status": "ok",
        "n_samples": n,
        "n_positive": pos,
        "n_negative": neg,
        "feature_names": feature_names,
        "models": {},
        "ensemble": {},
    }

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    probs_by_model: Dict[str, np.ndarray] = {}

    for name, model in models.items():
        try:
            cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy").tolist()
            cv_f1 = cross_val_score(model, X, y, cv=cv, scoring="f1").tolist()
            model.fit(X, y)
            pred = model.predict(X)
            train_acc = float(accuracy_score(y, pred))
            train_f1 = float(f1_score(y, pred, zero_division=0))
            if hasattr(model, "predict_proba"):
                prob = model.predict_proba(X)[:, 1]
            elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("clf"), "predict_proba"):
                prob = model.predict_proba(X)[:, 1]
            else:
                prob = pred.astype(float)
            probs_by_model[name] = prob

            importances = None
            clf = model.named_steps["clf"] if hasattr(model, "named_steps") else model
            if hasattr(clf, "feature_importances_"):
                imp = clf.feature_importances_
                importances = sorted(
                    zip(feature_names, [round(float(x), 4) for x in imp]),
                    key=lambda t: -t[1],
                )[:8]

            results["models"][name] = {
                "cv_accuracy_mean": round(float(np.mean(cv_acc)), 3),
                "cv_accuracy_std": round(float(np.std(cv_acc)), 3),
                "cv_f1_mean": round(float(np.mean(cv_f1)), 3),
                "train_accuracy": round(train_acc, 3),
                "train_f1": round(train_f1, 3),
                "top_features": importances,
            }
        except Exception as exc:
            results["models"][name] = {"error": str(exc)}

    if probs_by_model:
        stack = np.vstack(list(probs_by_model.values()))
        ensemble_prob = stack.mean(axis=0)
        results["ensemble"]["method"] = "mean_probability"
        results["ensemble"]["probabilities"] = [round(float(p), 4) for p in ensemble_prob]
        results["ensemble"]["predictions"] = [int(p >= 0.5) for p in ensemble_prob]

    return results


def _descriptive_stats(values: List[float], label: str) -> Dict[str, Any]:
    if not values:
        return {"label": label, "count": 0}
    arr = np.array(values, dtype=float)
    return {
        "label": label,
        "count": len(values),
        "mean": round(float(arr.mean()), 3),
        "std": round(float(arr.std()), 3),
        "min": round(float(arr.min()), 3),
        "max": round(float(arr.max()), 3),
        "median": round(float(np.median(arr)), 3),
    }


def _build_prescriptive(
    domain: str,
    items: List[Dict[str, Any]],
    tier: str,
) -> List[Dict[str, Any]]:
    """Rank prescriptive actions from scored items."""
    ranked = sorted(items, key=lambda x: -x.get("score", 0))
    actions: List[Dict[str, Any]] = []
    for i, it in enumerate(ranked[:8]):
        urgency = "immediate" if it.get("score", 0) >= 0.75 else "72h" if it.get("score", 0) >= 0.55 else "monitor"
        actions.append({
            "rank": i + 1,
            "urgency": urgency,
            "domain": domain,
            "title": it.get("title", "Review item"),
            "detail": it.get("detail", ""),
            "entity": it.get("entity"),
            "score": round(float(it.get("score", 0)), 3),
            "ml_support": it.get("ml_support", "ensemble"),
        })
    if tier != "prescriptive" and actions:
        return actions[:5]
    return actions


def _prn_seat_features(seat: dict, soc: Optional[dict]) -> Tuple[List[float], str]:
    dpi = seat.get("dpi") or {}
    age = dpi.get("age") or {}
    youth = _safe_float(age.get("18_20")) + _safe_float(age.get("21_25")) + _safe_float(age.get("26_40"))
    voters = _safe_float(dpi.get("registeredVotersDpi") or seat.get("registeredVoters"), 1)
    youth_pct = (youth / voters * 100) if voters else 0.0

    soc = soc or {}
    lean = soc.get("lean") or {}

    code = seat.get("code") or "?"
    features = [
        min(_safe_float(seat.get("majority")), 15000) / 15000.0,
        _safe_float(dpi.get("pctMelayu") or seat.get("pctMelayu"), 55) / 100.0,
        _safe_float(dpi.get("pctCina"), 30) / 100.0,
        _safe_float(dpi.get("pctIndia"), 5) / 100.0,
        youth_pct / 100.0,
        min(_safe_float(dpi.get("culaPct")), 25) / 25.0,
        np.tanh(_safe_float(dpi.get("bkcModal")) / 5000.0),
        min(_safe_float(seat.get("newsMentions")), 50) / 50.0,
        _safe_float(soc.get("neg_pct")) / 100.0,
        min(_safe_float(soc.get("mentions_total")), 100) / 100.0,
        min(_safe_float(soc.get("engagement_total")), 5000) / 5000.0,
        _safe_float(lean.get("menentang")) / 100.0,
        _safe_float(seat.get("scenarioPasPn"), 20) / 100.0,
    ]
    feature_names = [
        "majority_norm", "pct_melayu", "pct_cina", "pct_india", "youth_pct",
        "cula_pct", "bkc_modal", "news_mentions", "socmed_neg_pct",
        "socmed_mentions", "socmed_engagement", "socmed_oppose_lean",
        "scenario_pas_pn",
    ]
    return features, code


def _prn_competitive_label(seat: dict) -> int:
    kp = (seat.get("kategoriPas") or "").lower()
    if kp in ("defend", "winnable", "tough"):
        return 1
    if _safe_float(seat.get("pasWinProb")) >= 35:
        return 1
    return 0


def run_prn_n9_ml(
    seats_path: Optional[Path] = None,
    socmed_path: Optional[Path] = None,
    write_output: bool = True,
) -> Dict[str, Any]:
    seats_path = seats_path or PRN_N9_SEATS_JSON
    socmed_path = socmed_path or PRN_N9_SOCMED_JSON

    if not seats_path.exists():
        return {"success": False, "error": f"Seats file not found: {seats_path}"}

    payload = json.loads(seats_path.read_text(encoding="utf-8"))
    seats = payload.get("seats") or []
    socmed = {}
    if socmed_path.exists():
        soc_data = json.loads(socmed_path.read_text(encoding="utf-8"))
        socmed = soc_data.get("byDun") or {}

    X_list: List[List[float]] = []
    y_list: List[int] = []
    codes: List[str] = []
    seat_meta: List[Dict[str, Any]] = []

    for seat in seats:
        code = (seat.get("code") or "").upper()
        soc = socmed.get(code)
        feats, _ = _prn_seat_features(seat, soc)
        X_list.append(feats)
        y_list.append(_prn_competitive_label(seat))
        codes.append(code)
        seat_meta.append({
            "code": code,
            "name": seat.get("name"),
            "kategoriPas": seat.get("kategoriPas"),
            "pasWinProb": seat.get("pasWinProb"),
            "majority": seat.get("majority"),
        })

    feature_names = [
        "majority_norm", "pct_melayu", "pct_cina", "pct_india", "youth_pct",
        "cula_pct", "bkc_modal", "news_mentions", "socmed_neg_pct",
        "socmed_mentions", "socmed_engagement", "socmed_oppose_lean",
        "scenario_pas_pn",
    ]

    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)

    descriptive = {
        "seats_total": len(seats),
        "competitive_seats": int(y.sum()),
        "pas_win_prob": _descriptive_stats([_safe_float(s.get("pasWinProb")) for s in seats], "pasWinProb"),
        "majority": _descriptive_stats([_safe_float(s.get("majority")) for s in seats], "majority2023"),
        "socmed_neg_pct": _descriptive_stats(
            [_safe_float((socmed.get(c) or {}).get("neg_pct")) for c in codes if socmed.get(c)],
            "socmed_neg_pct",
        ),
    }

    tier = "descriptive"
    ml_result: Dict[str, Any] = {"status": "skipped", "reason": "sklearn unavailable"}
    if _sklearn_available() and len(seats) >= MIN_ROWS_PREDICTIVE:
        tier = "predictive"
        ml_result = _train_classifiers(X, y, feature_names)
    elif _sklearn_available():
        tier = "predictive"
        ml_result = _train_classifiers(X, y, feature_names)

    seat_predictions: List[Dict[str, Any]] = []
    prescriptive_items: List[Dict[str, Any]] = []

    if ml_result.get("status") == "ok" and ml_result.get("ensemble", {}).get("probabilities"):
        probs = ml_result["ensemble"]["probs"] if "probs" in ml_result["ensemble"] else ml_result["ensemble"]["probabilities"]
        for i, code in enumerate(codes):
            prob = probs[i]
            meta = seat_meta[i]
            seat_predictions.append({
                **meta,
                "ml_competitive_prob": prob,
                "ml_competitive_flag": int(prob >= 0.5),
                "rule_pas_prob": meta.get("pasWinProb"),
            })
            if prob >= 0.45:
                prescriptive_items.append({
                    "entity": code,
                    "score": prob,
                    "title": f"Gerakkan jentera & digital ke {code} · {meta.get('name')}",
                    "detail": (
                        f"ML ensemble {prob:.0%} competitive · kategori {meta.get('kategoriPas')} · "
                        f"majoriti {meta.get('majority')} · rule pasWinProb {meta.get('pasWinProb')}%"
                    ),
                    "ml_support": "svm+random_forest+decision_tree",
                })

        if len(seats) >= MIN_ROWS_PRESCRIPTIVE:
            tier = "prescriptive"

    seat_predictions.sort(key=lambda x: -x.get("ml_competitive_prob", 0))

    result = {
        "success": True,
        "domain": "prn_n9_seat_competition",
        "generated_at": datetime.now().isoformat(),
        "analytics_tier": tier,
        "label_definition": "competitive seat = kategoriPas defend/winnable/tough OR pasWinProb≥35",
        "disclaimer": "Bukan polling SPR. Model tabular hibrid — 36 DUN, guna CV. Sahkan dengan lapangan.",
        "descriptive": descriptive,
        "predictive": ml_result,
        "seat_predictions": seat_predictions,
        "prescriptive_actions": _build_prescriptive("prn_n9", prescriptive_items, tier),
        "model_summary": {
            "algorithms": ["SVM (RBF)", "Random Forest", "Decision Tree"],
            "ensemble": "mean probability",
            "n_features": len(feature_names),
        },
    }

    if write_output:
        PRN_N9_ML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        PRN_N9_ML_OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        result["output_path"] = str(PRN_N9_ML_OUTPUT)

    return result


def run_portfolio_ml(rows: List[Dict[str, str]], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    if not rows:
        return {"success": False, "error": "No borrower rows"}

    fields = fields or list(rows[0].keys())
    norm_map = {_normalize_col(c): c for c in fields}

    def col(*names: str) -> Optional[str]:
        for n in names:
            k = _normalize_col(n)
            if k in norm_map:
                return norm_map[k]
        return None

    sector_c = col("sector", "sektor", "industry")
    risk_c = col("risk", "status", "tier", "ews")
    loan_c = col("loan_amount", "loan", "pinjaman", "amount")

    sectors = sorted({(r.get(sector_c) or "unknown").strip() for r in rows if sector_c})
    sector_idx = {s: i for i, s in enumerate(sectors)}

    X_list: List[List[float]] = []
    y_list: List[int] = []
    names: List[str] = []

    for r in rows:
        sector = (r.get(sector_c) or "unknown").strip() if sector_c else "unknown"
        one_hot = [0.0] * max(len(sectors), 1)
        if sector in sector_idx:
            one_hot[sector_idx[sector]] = 1.0
        loan = min(_safe_float(r.get(loan_c) if loan_c else 0), 2_000_000) / 2_000_000.0
        X_list.append(one_hot + [loan])

        label = 0
        if risk_c:
            rv = (r.get(risk_c) or "").upper()
            if "HIGH" in rv or rv in ("H", "3", "RED"):
                label = 1
            elif "MED" in rv or rv in ("M", "2", "AMBER"):
                label = 0
        y_list.append(label)
        names.append(r.get(col("borrower", "peminjam", "company", "nama", "name")) or "?")

    feature_names = [f"sector_{s}" for s in sectors] + ["loan_norm"]
    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)

    high_count = int(y.sum())
    descriptive = {
        "borrower_count": len(rows),
        "high_risk_labeled": high_count,
        "sectors": {s: sum(1 for r in rows if sector_c and (r.get(sector_c) or "").strip() == s) for s in sectors},
    }

    tier = "descriptive"
    ml_result: Dict[str, Any] = {"status": "skipped"}
    if _sklearn_available() and high_count >= MIN_POSITIVE_CLASS and (len(rows) - high_count) >= MIN_POSITIVE_CLASS:
        tier = "predictive" if len(rows) < MIN_ROWS_PRESCRIPTIVE else "prescriptive"
        ml_result = _train_classifiers(X, y, feature_names)

    predictions: List[Dict[str, Any]] = []
    prescriptive_items: List[Dict[str, Any]] = []
    if ml_result.get("status") == "ok" and ml_result.get("ensemble", {}).get("probabilities"):
        probs = ml_result["ensemble"]["probabilities"]
        for i, name in enumerate(names):
            prob = probs[i]
            predictions.append({"borrower": name, "ml_high_risk_prob": prob, "ml_flag": int(prob >= 0.5)})
            if prob >= 0.5:
                prescriptive_items.append({
                    "entity": name,
                    "score": prob,
                    "title": f"EWS: Hubungi {name} dalam 24–72 jam",
                    "detail": f"ML ensemble {prob:.0%} HIGH risk · semak cashflow & sector exposure",
                    "ml_support": "portfolio_ensemble",
                })
        predictions.sort(key=lambda x: -x["ml_high_risk_prob"])

    return {
        "success": True,
        "domain": "portfolio_ews",
        "analytics_tier": tier,
        "descriptive": descriptive,
        "predictive": ml_result,
        "borrower_predictions": predictions,
        "prescriptive_actions": _build_prescriptive("portfolio", prescriptive_items, tier),
    }


def run_field_cula_ml(rows: List[Dict[str, str]], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    if not rows:
        return {"success": False, "error": "No field rows"}

    fields = fields or list(rows[0].keys())
    norm_map = {_normalize_col(c): c for c in fields}

    def col(*names: str) -> Optional[str]:
        for n in names:
            k = _normalize_col(n)
            if k in norm_map:
                return norm_map[k]
        return None

    dun_c = col("dun", "DUN", "kod_dun")
    rumah_c = col("rumah", "houses", "doors")
    cula_c = col("cula", "CULA", "contacts")

    by_dun: Dict[str, Dict[str, float]] = {}
    for r in rows:
        dun = (r.get(dun_c) or "?").strip().upper() if dun_c else "?"
        rumah = _safe_float(r.get(rumah_c) if rumah_c else 0)
        cula = _safe_float(r.get(cula_c) if cula_c else 0)
        if dun not in by_dun:
            by_dun[dun] = {"rumah": 0.0, "cula": 0.0, "rows": 0}
        by_dun[dun]["rumah"] += rumah
        by_dun[dun]["cula"] += cula
        by_dun[dun]["rows"] += 1

    duns = sorted(by_dun.keys())
    ratios = []
    for d in duns:
        rumah = by_dun[d]["rumah"] or 1.0
        ratios.append(by_dun[d]["cula"] / rumah)

    descriptive = {
        "dun_count": len(duns),
        "total_rumah": sum(v["rumah"] for v in by_dun.values()),
        "total_cula": sum(v["cula"] for v in by_dun.values()),
        "cula_ratio": _descriptive_stats(ratios, "cula_per_rumah"),
    }

    prescriptive_items = []
    for d in duns:
        rumah = by_dun[d]["rumah"] or 1.0
        ratio = by_dun[d]["cula"] / rumah
        if ratio < 0.15 and by_dun[d]["rumah"] >= 50:
            prescriptive_items.append({
                "entity": d,
                "score": 1.0 - ratio,
                "title": f"Redeploy field team ke {d}",
                "detail": f"Cula/rumah {ratio:.1%} — below 15% threshold",
                "ml_support": "rule_threshold",
            })

    return {
        "success": True,
        "domain": "field_cula",
        "analytics_tier": "prescriptive" if prescriptive_items else "descriptive",
        "descriptive": descriptive,
        "by_dun": by_dun,
        "prescriptive_actions": _build_prescriptive("field_cula", prescriptive_items, "prescriptive"),
    }


def run_ml_analysis(
    analysis_type: str,
    upload_summaries: Optional[List[Dict[str, Any]]] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Route ML pipeline by analysis type and available data."""
    upload_summaries = upload_summaries or []

    if analysis_type == "field_operations":
        for u in upload_summaries:
            if u.get("detected_type") == "field_cula" or u.get("dataset_type") == "field_cula":
                rows = load_upload_rows(u)
                return run_field_cula_ml(rows, u.get("columns"))

    if analysis_type in ("portfolio_intelligence", "sme_insights"):
        for u in upload_summaries:
            if u.get("detected_type") == "borrower_list" or u.get("dataset_type") == "borrower_list":
                rows = load_upload_rows(u)
                out = run_portfolio_ml(rows, u.get("columns"))
                out["analysis_type"] = analysis_type
                return out

    if analysis_type in ("social_listening", "issue_detection") and project_id:
        pid = (project_id or "").upper()
        if "PRN" in pid or "N9" in pid:
            return run_prn_n9_ml(write_output=False)

    if analysis_type == "field_operations" and project_id:
        pid = (project_id or "").upper()
        if "PRN" in pid or "N9" in pid:
            return run_prn_n9_ml(write_output=False)

    return {
        "success": True,
        "domain": "generic",
        "analytics_tier": "descriptive",
        "message": "ML predictive layer requires upload data or PRN N9 project context",
        "prescriptive_actions": [],
    }
