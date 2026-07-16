#!/usr/bin/env python3
"""Standalone Negeri Sembilan Chinese & Indian narrative dashboard (HTML + JSON)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "n9_chinese_narrative_dashboard"
CSV = DASH / "data/prn_chinese_narrative_posts_3negeri.csv"
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
OUT_HTML = OUT_DIR / "naratif_cina_india_johor_n9_dashboard.html"
OUT_JSON = OUT_DIR / "naratif_cina_india_johor_n9_analytics.json"
MYT = timezone(timedelta(hours=8))

STATES = ["Negeri Sembilan"]

if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def _rebuild_dataset() -> pd.DataFrame:
    from utils.build_dataset import build_dataset  # noqa: WPS433

    return build_dataset()


def _load_df(rebuild: bool) -> pd.DataFrame:
    if rebuild or not CSV.exists():
        print("🔨 Bina semula dataset (termasuk Harakat crawls)…")
        return _rebuild_dataset()
    return pd.read_csv(CSV, low_memory=False)


def _is_chinese(row: pd.Series) -> bool:
    from utils.community import infer_community  # noqa: WPS433

    if str(row.get("crawl_community") or "").lower() == "india":
        return False
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
    if str(row.get("crawl_pipeline") or "") == "harakat_issue_20260705":
        text_l = text.lower()
        if re.search(r"harakat|syurga|shawn loh|罗盛年|天堂|伊党|国阵", text_l):
            return True
    return False


def _is_indian(row: pd.Series) -> bool:
    return str(row.get("crawl_community") or "").lower() == "india"


def _neg_pct(df: pd.DataFrame) -> int:
    if df.empty or "sentiment" not in df.columns:
        return 0
    return int(round((df["sentiment"].astype(str).str.lower() == "negative").mean() * 100))


def _top_issues(df: pd.DataFrame, limit: int = 5) -> List[List[Any]]:
    from utils.keyword_classifier import classify_issue  # noqa: WPS433

    if df.empty:
        return []
    clusters: Counter[str] = Counter()
    for _, row in df.iterrows():
        text = str(row.get("post_text") or "")
        ic = str(row.get("issue_cluster") or "").strip()
        clusters[classify_issue(text, ic)] += 1
    total = sum(clusters.values()) or 1
    return [[name, int(round(c / total * 100))] for name, c in clusters.most_common(limit)]


def _theme_hits(df: pd.DataFrame) -> Dict[str, int]:
    text = df.get("post_text", pd.Series(dtype=str)).fillna("").astype(str)
    themes = {
        "ph_dap": r"\bph\b|dap|行动党|希盟|pakatan harapan",
        "pas_pn": r"\bpas\b|伊党|parti islam|\bpn\b|perikatan|国盟",
        "mn_bn": r"\bmn\b|muafakat|国阵|barisan|umno|巫统|巫伊",
        "boycott": r"boikot|boycott|不投票|弃权|tak.?nak.?undi",
        "harakat": r"harakat|harakak|syurga|tak bau|天堂|shawn loh|罗盛年",
        "cost_of_living": r"kos sara hidup|cost of living|生活费|通胀",
    }
    out: Dict[str, int] = {}
    for key, pat in themes.items():
        out[key] = int(text.str.contains(pat, case=False, na=False, regex=True).sum())
    return out


def _samples(df: pd.DataFrame, n: int = 5) -> List[Dict[str, str]]:
    if df.empty:
        return []
    work = df.copy()
    if "engagement_total" in work.columns:
        work = work.sort_values("engagement_total", ascending=False)
    out: List[Dict[str, str]] = []
    for _, row in work.head(n).iterrows():
        text = str(row.get("post_text") or "")[:260]
        if not text.strip():
            continue
        sent = str(row.get("sentiment") or "neutral").lower()
        plat = str(row.get("platform") or "media")
        loc = str(row.get("constituency") or row.get("state") or "")
        out.append({"text": text, "sent": sent, "meta": f"{loc} · {plat}"})
    return out


def _state_bundle(state: str, df: pd.DataFrame) -> Dict[str, Any]:
    sub = df[df["state"].astype(str) == state] if "state" in df.columns else pd.DataFrame()
    chinese = sub[sub.apply(_is_chinese, axis=1)] if not sub.empty else pd.DataFrame()
    indian = sub[sub.apply(_is_indian, axis=1)] if not sub.empty else pd.DataFrame()
    label = "N9" if state == "Negeri Sembilan" else state
    return {
        "label": label,
        "state": state,
        "chinese": {
            "posts": len(chinese),
            "neg_pct": _neg_pct(chinese),
            "issues": _top_issues(chinese),
            "themes": _theme_hits(chinese),
            "samples": _samples(chinese),
        },
        "indian": {
            "posts": len(indian),
            "neg_pct": _neg_pct(indian),
            "issues": _top_issues(indian),
            "themes": _theme_hits(indian),
            "samples": _samples(indian),
        },
    }


def build(rebuild: bool = False) -> Dict[str, Any]:
    df = _load_df(rebuild)
    focus = df[df["state"].isin(STATES)] if "state" in df.columns else df
    harakat_rows = int((focus.get("crawl_pipeline", pd.Series(dtype=str)) == "harakat_issue_20260705").sum())
    payload = {
        "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "source_csv": str(CSV.relative_to(ROOT)),
        "total_rows_all": len(df),
        "total_rows_johor_n9": len(focus),
        "harakat_rows_merged": harakat_rows,
        "states": {},
    }
    for state in STATES:
        bundle = _state_bundle(state, focus)
        key = "N9" if state == "Negeri Sembilan" else state
        payload["states"][key] = bundle
        print(
            f"  {key}: Cina {bundle['chinese']['posts']} · "
            f"India {bundle['indian']['posts']} · Harakat theme hits "
            f"{bundle['chinese']['themes'].get('harakat', 0)}"
        )
    return payload


def _issue_bars(issues: List[List[Any]]) -> str:
    if not issues:
        return "<p class='muted'>Tiada data isu.</p>"
    return "".join(
        f"<div class='issue-row'><span>{name}</span><div class='bar'><span style='width:{pct}%'></span></div>"
        f"<strong>{pct}%</strong></div>"
        for name, pct in issues
    )


def _sample_list(samples: List[Dict[str, str]]) -> str:
    if not samples:
        return "<li class='muted'>Tiada sampel.</li>"
    return "".join(
        f"<li><span class='tag {s.get('sent','neu')}'>{s.get('sent','?')}</span>"
        f"{s.get('text','')}<br/><small>{s.get('meta','')}</small></li>"
        for s in samples
    )


def _theme_table(themes: Dict[str, int]) -> str:
    labels = {
        "ph_dap": "PH / DAP",
        "pas_pn": "PAS / PN",
        "mn_bn": "MN / BN (巫伊)",
        "boycott": "Boikot / abstain",
        "harakat": "Harakat / syurga",
        "cost_of_living": "Kos sara hidup",
    }
    return "".join(
        f"<tr><td>{labels.get(k, k)}</td><td><strong>{v}</strong></td></tr>"
        for k, v in themes.items()
    )


def render_html(data: Dict[str, Any]) -> str:
    states = data.get("states", {})
    n9 = states.get("N9", {})

    def kpi_block(st: Dict[str, Any], comm: str) -> str:
        c = st.get(comm, {})
        return f"""
        <div class="kpi-grid">
          <div class="kpi"><label>Posts</label><strong>{c.get('posts', 0)}</strong></div>
          <div class="kpi"><label>Negatif</label><strong>{c.get('neg_pct', 0)}%</strong></div>
        </div>
        <h4>Isu utama</h4>
        {_issue_bars(c.get('issues', []))}
        <h4>Tema politik</h4>
        <table class="mini">{_theme_table(c.get('themes', {}))}</table>
        <h4>Sampel</h4>
        <ul class="samples">{_sample_list(c.get('samples', []))}</ul>
        """

    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Naratif Cina & India · Negeri Sembilan</title>
  <style>
    :root {{
      --bg:#0b1220; --card:#151f32; --border:#2a3650; --text:#e8edf5; --muted:#93a4bd;
      --rose:#fb7185; --purple:#c084fc; --blue:#60a5fa; --green:#34d399; --amber:#fbbf24;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family: system-ui, sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
    .wrap {{ max-width:1200px; margin:0 auto; padding:24px 16px 48px; }}
    h1 {{ font-size:1.55rem; }}
    .sub {{ color:var(--muted); margin:6px 0 20px; font-size:0.9rem; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }}
    .pill {{ background:var(--card); border:1px solid var(--border); border-radius:999px; padding:6px 12px; font-size:0.78rem; }}
    .state-panel {{ background:var(--card); border:1px solid var(--border); border-radius:14px; overflow:hidden; }}
    .state-head {{ padding:16px 18px; border-bottom:1px solid var(--border); }}
    .state-head.n9 {{ border-top:4px solid var(--green); }}
    .comm-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--border); }}
    @media (max-width:700px) {{ .comm-grid {{ grid-template-columns:1fr; }} }}
    .comm {{ background:var(--card); padding:16px; }}
    .comm.chinese h3 {{ color:var(--rose); }}
    .comm.indian h3 {{ color:var(--purple); }}
    .kpi-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:10px 0; }}
    .kpi {{ background:#0b1220; border:1px solid var(--border); border-radius:8px; padding:10px; }}
    .kpi label {{ font-size:0.65rem; color:var(--muted); text-transform:uppercase; }}
    .kpi strong {{ font-size:1.4rem; }}
    h4 {{ font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin:14px 0 8px; }}
    .issue-row {{ display:grid; grid-template-columns:120px 1fr 40px; gap:8px; align-items:center; font-size:0.82rem; margin-bottom:6px; }}
    .bar {{ height:8px; background:#0b1220; border-radius:4px; overflow:hidden; }}
    .bar span {{ display:block; height:100%; background:linear-gradient(90deg,var(--green),var(--blue)); }}
    table.mini {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
    table.mini td {{ border:1px solid var(--border); padding:6px 8px; }}
    ul.samples {{ padding-left:16px; font-size:0.84rem; }}
    ul.samples li {{ margin-bottom:10px; }}
    .tag {{ font-size:0.62rem; padding:2px 6px; border-radius:4px; background:#334155; margin-right:6px; text-transform:uppercase; }}
    .tag.negative {{ background:rgba(251,113,133,.2); color:#fecdd3; }}
    .tag.positive {{ background:rgba(52,211,153,.2); color:#bbf7d0; }}
    .muted {{ color:var(--muted); }}
    .insight {{ background:rgba(52,211,153,.08); border:1px solid rgba(52,211,153,.25); border-radius:10px; padding:14px; margin-top:16px; font-size:0.88rem; }}
    footer {{ margin-top:24px; color:var(--muted); font-size:0.75rem; }}
  </style>
</head>
<body>
<div class="wrap">
  <h1>Naratif Cina & India · Negeri Sembilan</h1>
  <p class="sub">Fokus N9 sahaja · Data percuma (Google News RSS, Tamil RSS, China Press) + crawl Harakat · Bukan polling SPR</p>
  <div class="meta">
    <span class="pill">Dijana: {data.get('generated_at','')}</span>
    <span class="pill">N9 rows: {data.get('total_rows_johor_n9', 0):,}</span>
    <span class="pill">Harakat merged: {data.get('harakat_rows_merged', 0)}</span>
    <span class="pill">Sumber: {data.get('source_csv','')}</span>
  </div>

  <div class="insight">
    <strong>Ringkasan profesional (N9):</strong>
    Komuniti Cina — kos hidup, SME & perkhidmatan PBT (Seremban/Nilai).
    Komuniti India — SJKT & pekerjaan lebih dominan.
    Risiko utama = <em>soft abstention</em> jika perkhidmatan tidak dijawab dengan fakta.
  </div>

  <div style="margin-top:16px">
    <div class="state-panel">
      <div class="state-head n9"><h2>Negeri Sembilan · 36 DUN</h2><p class="muted">Base PH kuat · SJKT & pekerjaan India · bandar Cina Seremban/Nilai</p></div>
      <div class="comm-grid">
        <div class="comm chinese"><h3>🇨🇳 Komuniti Cina</h3>{kpi_block(n9, 'chinese')}</div>
        <div class="comm indian"><h3>🇮🇳 Komuniti India</h3>{kpi_block(n9, 'indian')}</div>
      </div>
    </div>
  </div>

  <footer>
    InsightPulse · N9 only · Refresh: <code>NEImpulse/bin/python scripts/analyze_naratif_agentic.py --no-llm</code>
  </footer>
</div>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Rebuild combined CSV first")
    args = parser.parse_args()

    print("📊 Standalone Negeri Sembilan Cina/India dashboard…")
    data = build(rebuild=args.rebuild)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    print(f"✅ HTML: {OUT_HTML}")
    print(f"✅ JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())