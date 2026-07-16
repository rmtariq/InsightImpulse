"""Build payload for 4-page executive action report."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from components.metrics import compute_overview_kpis
from utils.action_engine import build_action_candidates, recommend
from utils.reporting.labels import (
    CLASSIFICATION,
    EVIDENCE_BM,
    ISSUE_BM,
    ORG_NAME,
    PRIORITY_LABELS,
    REPORT_VERSION,
    STATUS_META,
    UNCLASSIFIED,
    normalize_issue,
)
from utils.reporting.report_validation import (
    data_reliability,
    issue_trend,
    location_display,
    sentiment_counts,
)

# Tindakan khusus — elak cadangan kabur
SPECIFIC_ACTIONS: dict[str, dict[str, str]] = {
    "SME and Business": {
        "tindakan": (
            "Semak bantuan SME yang masih aktif dan terbitkan satu infografik BM–Mandarin "
            "mengandungi syarat kelayakan, pautan permohonan dan nombor pegawai untuk dihubungi."
        ),
        "hasil": "Satu infografik, satu FAQ dan senarai pegawai untuk dihubungi.",
        "pasukan": "Ekonomi dan Komunikasi",
        "kpi": "Panduan diterbitkan; jumlah pertanyaan direkod; sentimen dipantau 24 jam selepas.",
    },
    "Cost of Living": {
        "tindakan": "Sahkan senarai bantuan kos sara hidup aktif dan edar helaian BM–Mandarin ringkas ke saluran komuniti.",
        "hasil": "Helaian fakta disahkan + saluran aduan jelas.",
        "pasukan": "Dasar dan Komunikasi",
        "kpi": "Helaian diedar; aduan direkod dalam 48 jam.",
    },
    "Chinese Education": {
        "tindakan": "Sahkan peruntukan dan dasar pendidikan Cina; sediakan jawapan BM–Mandarin untuk soalan komuniti.",
        "hasil": "Nota fakta rasmi + sesi dialog jika perlu.",
        "pasukan": "Dasar dan Komunikasi",
        "kpi": "Nota fakta diterbit; sentimen isu dipantau 72 jam.",
    },
    "Water Supply": {
        "tindakan": "Sahkan status bekalan air dengan agensi berkaitan dan keluarkan kemas kini perkhidmatan yang boleh disahkan.",
        "hasil": "Kenyataan perkhidmatan + garis masa pemulihan.",
        "pasukan": "Operasi Tempatan",
        "kpi": "Kemas kini diterbit; aduan lokasi direkod.",
    },
}


def _data_period(sub: pd.DataFrame) -> str:
    if sub.empty or "published_at" not in sub.columns:
        return "—"
    d = pd.to_datetime(sub["published_at"], errors="coerce").dropna()
    if d.empty:
        return "—"
    return f"{d.min():%d %b %Y} — {d.max():%d %b %Y}"


def _management_status(sub: pd.DataFrame, p1: int, misinfo: int, high_risk: int) -> dict[str, str]:
    sc = sentiment_counts(sub)
    neg = sc["pct_negative"]
    if high_risk >= 3 or misinfo >= 2 or (p1 >= 2 and neg > 40):
        code = "MERAH"
    elif p1 >= 1 or high_risk >= 1 or misinfo >= 1 or neg > 35:
        code = "JINGGA"
    elif neg > 25 or high_risk > 0:
        code = "KUNING"
    else:
        code = "HIJAU"
    meta = STATUS_META[code]
    parts = []
    if p1:
        parts.append(f"{p1} tindakan P1")
    if high_risk:
        parts.append(f"{high_risk} risiko tinggi/kritikal")
    if misinfo:
        parts.append(f"{misinfo} dakwaan perlu disahkan")
    reason = " dan ".join(parts) if parts else "tiada isu keutamaan kritikal"
    sentence = f"Status {code} ({meta['label']}) kerana {reason}."
    return {"code": code, "label": meta["label"], "color": meta["color"], "sentence": sentence}


def _issue_interpretation(issue_bm: str, neg_pct: float, loc: str) -> str:
    templates = {
        "Kos Sara Hidup": f"Perbincangan tertumpu harga barang dan kemampuan isi rumah, dengan sentimen negatif {neg_pct:.0f}% di {loc}.",
        "SME dan Perniagaan": f"Peniaga menyatakan maklumat bantuan dan promosi perniagaan tempatan tidak jelas ({neg_pct:.0f}% negatif).",
        "Pendidikan Cina": f"Isu peruntukan dan dasar pendidikan Cina — sentimen negatif {neg_pct:.0f}%.",
    }
    return templates.get(issue_bm, f"{issue_bm} — {neg_pct:.0f}% sentimen negatif; lokasi utama {loc}.")


def _top5_issues(sub: pd.DataFrame) -> list[dict[str, Any]]:
    if sub.empty or "issue_cluster" not in sub.columns:
        return []
    work = sub.copy()
    work["_issue_bm"] = work["issue_cluster"].apply(normalize_issue)
    ranked = []
    for ic, grp in work.groupby("_issue_bm"):
        if ic == UNCLASSIFIED:
            continue
        loc = "—"
        if "constituency" in grp.columns:
            vc = grp["constituency"].astype(str).value_counts()
            loc = str(vc.index[0]) if len(vc) else "—"
        neg = (grp["sentiment"].astype(str).str.lower() == "negative").mean() * 100 if "sentiment" in grp.columns else 0
        eng = int(grp["engagement_total"].sum()) if "engagement_total" in grp.columns else 0
        tr = issue_trend(grp)
        ranked.append({
            "issue": ic,
            "location": loc if loc not in ("nan", "") else "Lokasi perlu disahkan",
            "count": len(grp),
            "neg_pct": round(neg, 1),
            "engagement": eng,
            "trend": tr["label"],
            "trend_detail": tr["detail"],
            "why": _issue_interpretation(ic, neg, loc),
            "priority": PRIORITY_LABELS[1] if neg >= 50 else PRIORITY_LABELS[2] if neg >= 35 else PRIORITY_LABELS[3],
        })
    ranked.sort(key=lambda x: (x["neg_pct"] * 0.4 + x["count"] * 0.3 + x["engagement"] * 0.0001), reverse=True)
    for i, r in enumerate(ranked[:5], 1):
        r["rank"] = i
    return ranked[:5]


def _action_board(sub: pd.DataFrame, top_issues: list[dict]) -> list[dict[str, str]]:
    actions_df = build_action_candidates(sub)
    rows: list[dict[str, str]] = []
    seen_issues: set[str] = set()

    def _add(row_data: dict[str, str]) -> None:
        if len(rows) >= 6:
            return
        key = row_data.get("issue_key", "")
        if key in seen_issues:
            return
        seen_issues.add(key)
        rows.append(row_data)

    for i, act in enumerate(actions_df.head(8).itertuples() if not actions_df.empty else []):
        ic_raw = str(getattr(act, "issue_cluster", ""))
        if normalize_issue(ic_raw) == UNCLASSIFIED:
            continue
        ic_bm = normalize_issue(ic_raw)
        prio = PRIORITY_LABELS[1] if i < 2 else PRIORITY_LABELS[2] if i < 4 else PRIORITY_LABELS[3]
        loc = str(getattr(act, "location", "") or getattr(act, "dun", "") or "—")
        spec = SPECIFIC_ACTIONS.get(ic_raw, {})
        tindakan = spec.get("tindakan") or str(getattr(act, "recommended_action", ""))
        if len(tindakan) < 40:
            _, tindakan, _ = recommend(ic_raw, float(getattr(act, "negative_percentage", 0)),
                                       False, str(getattr(act, "risk_level", "Low")))
        ev = str(getattr(act, "evidence_status", ""))
        ev_bm = EVIDENCE_BM["needs_more"] if "Perlu" in ev else EVIDENCE_BM["partial"]
        _add({
            "priority": prio,
            "issue_location": f"{ic_bm} — {loc}",
            "issue_key": ic_bm,
            "what_happened": str(getattr(act, "detected_narrative", ""))[:180],
            "action": tindakan[:280],
            "output": spec.get("hasil", "Satu output boleh diukur dan diedar kepada komuniti."),
            "team": spec.get("pasukan", str(getattr(act, "responsible_team", "Komunikasi"))),
            "deadline": "Dalam 24 jam" if "P1" in prio else "Dalam 48 jam" if "P2" in prio else "Dalam 7 hari",
            "evidence": ev_bm,
            "kpi": spec.get("kpi", "Sentimen isu dipantau 24–72 jam selepas tindakan."),
            "status": "Baharu",
        })

    for ti in top_issues:
        if len(rows) >= 6:
            break
        if ti["issue"] in seen_issues:
            continue
        spec = _spec_for_issue(ti["issue"])
        _add({
            "priority": ti["priority"],
            "issue_location": f"{ti['issue']} — {ti['location']}",
            "issue_key": ti["issue"],
            "what_happened": ti["why"],
            "action": spec.get("tindakan", f"Pantau dan sediakan penjelasan berdasarkan fakta untuk {ti['issue']}."),
            "output": spec.get("hasil", "Nota fakta atau kemas kini perkhidmatan."),
            "team": spec.get("pasukan", "Komunikasi"),
            "deadline": "Dalam 48 jam",
            "evidence": EVIDENCE_BM["needs_more"],
            "kpi": spec.get("kpi", "Isipadu dan sentimen dipantau."),
            "status": "Baharu",
        })
    return rows[:6]


def _spec_for_issue(issue_bm: str) -> dict[str, str]:
    for eng, bm in ISSUE_BM.items():
        if bm == issue_bm:
            return SPECIFIC_ACTIONS.get(eng, {})
    return SPECIFIC_ACTIONS.get(issue_bm, {})


def _exec_bullets(sub: pd.DataFrame, top5: list, status: dict, reliability: dict, actions: list) -> dict[str, list[str]]:
    k = compute_overview_kpis(sub)
    happening = []
    if top5:
        happening.append(f"Isu utama: {top5[0]['issue']} ({top5[0]['count']} hantaran, {top5[0]['neg_pct']}% negatif).")
    happening.append(f"Jumlah {k['total_posts']:,} hantaran dengan {k['total_engagement']:,} interaksi direkod.")
    if reliability.get("warning"):
        happening.append(reliability["warning"][:120])
    happening = happening[:3]

    important = []
    if k["high_risk"]:
        important.append(f"{k['high_risk']} naratif berisiko tinggi atau kritikal memerlukan semakan.")
    if k["misinfo"]:
        important.append(f"{k['misinfo']} dakwaan maklumat salah disyaki — pengesahan wajib.")
    if top5:
        important.append(f"Trend {top5[0]['issue']}: {top5[0]['trend']}.")
    important = important[:3] or ["Tiada isu kritikal melepasi ambang semasa."]

    decisions = []
    for a in actions:
        if "P1" in a.get("priority", ""):
            decisions.append(f"{a['issue_location']}: {a['action'][:100]}…")
        if len(decisions) >= 3:
            break
    if not decisions:
        decisions = ["Teruskan pemantauan harian.", "Jadualkan semakan data classifier jika Belum Diklasifikasikan >15%.", "Edar ringkasan ini kepada pasukan Communications."]
    return {"happening": happening[:3], "important": important[:3], "decisions": decisions[:3]}


def _top_risks(sub: pd.DataFrame) -> list[dict[str, str]]:
    if sub.empty or "risk_level" not in sub.columns:
        return []
    hi = sub[sub["risk_level"].astype(str).isin(["High", "Critical"])].copy()
    if hi.empty:
        return []
    hi = hi.sort_values("engagement_total", ascending=False) if "engagement_total" in hi.columns else hi
    out = []
    for _, r in hi.head(3).iterrows():
        loc, _, ver = location_display(r)
        out.append({
            "reason": f"Risiko {r.get('risk_level')} — {normalize_issue(r.get('issue_cluster', ''))}",
            "source": str(r.get("platform", "")),
            "location": loc,
            "evidence": EVIDENCE_BM["needs_more"] if r.get("misinformation_flag") else EVIDENCE_BM["partial"],
            "approval": "Legal/Management" if str(r.get("risk_level")) == "Critical" else "Communications",
            "url": str(r.get("source_url", "") or ""),
        })
    return out


def _claims(sub: pd.DataFrame) -> list[dict[str, str]]:
    if sub.empty or "misinformation_flag" not in sub.columns:
        return []
    m = sub[sub["misinformation_flag"] == True]  # noqa: E712
    out = []
    for _, r in m.head(5).iterrows():
        out.append({
            "summary": str(r.get("post_text", ""))[:150],
            "url": str(r.get("source_url", "") or "—"),
            "evidence_needed": "Sahkan dengan min. 2 sumber bebas",
            "officer": "Fact Checking",
            "deadline": (datetime.now() + timedelta(hours=12)).strftime("%d %b %Y, %H:%M"),
        })
    return out


def build_executive_payload(
    df: pd.DataFrame,
    state: str,
    meta: dict[str, str],
    *,
    chart_dir=None,
) -> dict[str, Any]:
    sub = df[df["state"].astype(str) == state].copy() if "state" in df.columns else df.copy()
    if "published_at" in sub.columns:
        sub["published_at"] = pd.to_datetime(sub["published_at"], errors="coerce")
    ts = datetime.now()
    k = compute_overview_kpis(sub)
    sc = sentiment_counts(sub)
    reliability = data_reliability(sub)
    top5 = _top5_issues(sub)
    actions = _action_board(sub, top5)
    p1_count = sum(1 for a in actions if "P1" in a.get("priority", ""))
    status = _management_status(sub, p1_count, k["misinfo"], k["high_risk"])
    bullets = _exec_bullets(sub, top5, status, reliability, actions)

    charts = {}
    if chart_dir is not None:
        from utils.reporting.executive_charts import generate_executive_charts
        charts = generate_executive_charts(sub, chart_dir, sc, _data_period(sub))

    return {
        "report_type": "executive",
        "version": REPORT_VERSION,
        "classification": CLASSIFICATION,
        "org": ORG_NAME,
        "state": state,
        "state_short": meta.get("short", ""),
        "title": "Laporan Tindakan Eksekutif",
        "subtitle": f"Pemantauan Naratif Berbahasa Cina — PRN {state}",
        "generated_at": ts.strftime("%d %B %Y, %H:%M"),
        "generated_at_file": ts.strftime("%Y%m%d_%H%M%S"),
        "data_period": _data_period(sub),
        "data_updated": ts.strftime("%d %B %Y, %H:%M"),
        "record_count": len(sub),
        "kpis": {
            "Jumlah Hantaran": f"{k['total_posts']:,}",
            "Jumlah Interaksi": f"{k['total_engagement']:,}",
            "Sentimen Positif": f"{sc['pct_positive']}%",
            "Sentimen Neutral": f"{sc['pct_neutral']}%",
            "Sentimen Negatif": f"{sc['pct_negative']}%",
            "Risiko Tinggi atau Kritikal": str(k["high_risk"]),
            "Maklumat Salah Disyaki": str(k["misinfo"]),
            "Sumber Aktif": str(k["active_sources"]),
        },
        "sentiment": sc,
        "status": status,
        "bullets": bullets,
        "top5_issues": top5,
        "action_board": actions,
        "top_risks": _top_risks(sub),
        "claims": _claims(sub),
        "reliability": reliability,
        "timeline": [
            ("0–4 Jam", "Assign pasukan; sahkan sumber, lokasi dan bukti yang tiada."),
            ("4–12 Jam", "Jalankan semakan fakta; hubungi agensi; kumpul bukti."),
            ("12–18 Jam", "Sediakan respons/tindakan; kelulusan Policy/Legal/Management jika perlu."),
            ("18–24 Jam", "Terbit/laksana; pantau reaksi."),
            ("48–72 Jam", "Banding isipadu & sentimen; tutup, pantau atau escalate."),
        ],
        "next_report": {
            "datetime": (ts + timedelta(days=1)).strftime("%d %B %Y, 09:00"),
            "open_p1": p1_count,
            "open_verify": len(_claims(sub)),
            "team": "Social Listening / Communications",
        },
        "charts": charts,
        "signoff": ["Disediakan oleh", "Disemak oleh", "Diluluskan oleh", "Tarikh"],
    }
