#!/usr/bin/env python3
"""Build Cina Narrative Johor campaign dashboard from project crawls."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CRAWL_DIR = ROOT / "data/projects/political/Cina_Narative_2026/crawls"
OUT_DIR = ROOT / "data/projects/political/Cina_Narative_2026/reports"
OUT_HTML = OUT_DIR / "cina_narrative_johor_dashboard.html"
OUT_JSON = OUT_DIR / "cina_narrative_analytics.json"

JOHOR_CN_SEATS = [
    {"code": "N12", "name": "Bentayan", "note": "Muar · PH kubu · Cina ~36%"},
    {"code": "N13", "name": "Simpang Jeram", "note": "Muar · PH kubu"},
    {"code": "N23", "name": "Penggaram", "note": "Batu Pahat · PH kubu · bandar Cina"},
    {"code": "N41", "name": "Puteri Wangsa", "note": "JB · bandar"},
    {"code": "N45", "name": "Stulang", "note": "JB · Cina majoriti"},
    {"code": "N48", "name": "Skudai", "note": "JB · Cina majoriti"},
    {"code": "N51", "name": "Bukit Batu", "note": "Kulai · PH kubu"},
    {"code": "N52", "name": "Senai", "note": "Kulai · PH kubu"},
]


def has_chinese(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(s)))


def load_crawls() -> pd.DataFrame:
    files = sorted(CRAWL_DIR.glob("*.csv"))
    if not files:
        return pd.DataFrame()
    parts = [pd.read_csv(f, low_memory=False) for f in files]
    df = pd.concat(parts, ignore_index=True)
    if "ID" in df.columns:
        df = df.drop_duplicates(subset=["ID"], keep="first")
    for c in ("likes", "shares", "comments_count", "views", "total_engagement"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def analyze(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"empty": True}

    text = df.get("Text", pd.Series(dtype=str)).fillna("")
    posts = df[df["Type"].str.lower() == "post"] if "Type" in df.columns else df
    comments = df[df["Type"].str.lower() == "comment"] if "Type" in df.columns else pd.DataFrame()

    cn_mask = text.apply(has_chinese)
    johor_mask = text.str.contains(
        r"johor|柔佛|新山|士古来|skudai|stulang|muar|batu pahat|kulai|麻坡|峇株",
        case=False, na=False, regex=True,
    )
    pas_bn_mask = text.str.contains(
        r"pas|伊党|umno|国阵|barisan|巫统|巫伊",
        case=False, na=False, regex=True,
    )
    harakat_mask = text.str.contains(
        r"harakat|syurga|tak bau|天堂|shawn loh|罗盛年",
        case=False, na=False, regex=True,
    )
    dap_mask = text.str.contains(
        r"\b(dap|ph|pakatan|行动党|希盟|张念群)\b",
        case=False, na=False, regex=True,
    )

    sentiment = df["sentiment_label"].value_counts().to_dict() if "sentiment_label" in df.columns else {}
    platform = df["Platform"].value_counts().to_dict() if "Platform" in df.columns else {}

    return {
        "generated_at": datetime.now().isoformat(),
        "totals": {
            "records": len(df),
            "posts": len(posts),
            "comments": len(comments),
            "likes": int(df.get("likes", pd.Series([0])).sum()),
            "shares": int(df.get("shares", pd.Series([0])).sum()),
            "views": int(df.get("views", pd.Series([0])).sum()),
            "engagement": int(df.get("total_engagement", pd.Series([0])).sum()),
        },
        "platform": platform,
        "sentiment": sentiment,
        "narrative": {
            "chinese_script_rows": int(cn_mask.sum()),
            "johor_related": int(johor_mask.sum()),
            "pas_bn_mentions": int(pas_bn_mask.sum()),
            "harakat_syurga_cluster": int(harakat_mask.sum()),
            "dap_ph_mentions": int(dap_mask.sum()),
            "core_issue_pct": round(int(harakat_mask.sum()) / max(len(df), 1) * 100, 1),
        },
        "insights": {
            "chinese_cares_syurga": int(cn_mask.sum() & harakat_mask.sum()) > 0,
            "chinese_focus_pas_bn": int((cn_mask & pas_bn_mask & johor_mask).sum()) > int((cn_mask & harakat_mask).sum()),
            "malay_backlash_syurga": int(
                df[harakat_mask & (df["Type"].str.lower() == "comment")].shape[0]
            ) if "Type" in df.columns else 0,
        },
        "top_chinese": [
            {"text": str(r["Text"])[:200], "eng": int(r.get("total_engagement", 0)), "sent": r.get("sentiment_label", "?")}
            for _, r in df[cn_mask].nlargest(5, "total_engagement").iterrows()
        ] if cn_mask.any() and "total_engagement" in df.columns else [],
    }


def render_html(stats: dict) -> str:
    t = stats.get("totals", {})
    n = stats.get("narrative", {})
    sent = stats.get("sentiment", {})
    plat = stats.get("platform", {})
    neg = sent.get("negative", 0)
    neu = sent.get("neutral", 0)
    pos = sent.get("positive", 0)
    total_sent = max(neg + neu + pos, 1)

    seats_rows = "".join(
        f"<tr><td><strong>{s['code']}</strong></td><td>{s['name']}</td><td>{s['note']}</td>"
        f"<td>Pertahan PH / rebut DAP</td><td>Muafakat 1-vs-1 · fokus kos hidup & perkhidmatan</td></tr>"
        for s in JOHOR_CN_SEATS
    )

    top_cn = stats.get("top_chinese", [])
    top_cn_html = "".join(
        f"<li><span class='tag'>{x.get('sent','?')}</span> eng {x.get('eng',0)} — {x.get('text','')}</li>"
        for x in top_cn
    ) or "<li>Tiada kandungan 汉字 mencukupi — jalankan Crawl 4A–4C.</li>"

    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Cina Narrative · Johor PRN · PAS/PN Campaign Intel</title>
  <style>
    :root {{
      --bg:#0f172a; --card:#1e293b; --border:#334155; --text:#e2e8f0; --muted:#94a3b8;
      --green:#10b981; --red:#ef4444; --amber:#f59e0b; --blue:#3b82f6; --purple:#a855f7;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family: system-ui, sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px 48px; }}
    h1 {{ font-size:1.5rem; margin-bottom:4px; }}
    .sub {{ color:var(--muted); font-size:0.9rem; margin-bottom:20px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:20px; }}
    .kpi {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; }}
    .kpi label {{ font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }}
    .kpi strong {{ display:block; font-size:1.6rem; margin-top:4px; }}
    .panel {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:18px; margin-bottom:16px; }}
    .panel h2 {{ font-size:1rem; margin-bottom:10px; color:var(--blue); }}
    .panel h3 {{ font-size:0.85rem; color:var(--muted); margin:12px 0 6px; text-transform:uppercase; letter-spacing:.05em; }}
    .bar {{ height:8px; background:#334155; border-radius:4px; overflow:hidden; margin:4px 0 10px; }}
    .bar span {{ display:block; height:100%; }}
    .tag {{ font-size:0.65rem; padding:2px 6px; border-radius:4px; background:#334155; margin-right:6px; }}
    ul {{ padding-left:18px; }}
    li {{ margin-bottom:8px; font-size:0.9rem; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
    th, td {{ border:1px solid var(--border); padding:8px; text-align:left; }}
    th {{ background:#0f172a; color:var(--muted); }}
    .do {{ border-left:3px solid var(--green); padding-left:12px; margin:8px 0; }}
    .dont {{ border-left:3px solid var(--red); padding-left:12px; margin:8px 0; }}
    .warn {{ background:rgba(245,158,11,.12); border:1px solid rgba(245,158,11,.35); border-radius:8px; padding:12px; margin-top:10px; font-size:0.88rem; }}
    code {{ background:#0f172a; padding:2px 6px; border-radius:4px; font-size:0.8rem; }}
  </style>
</head>
<body>
<div class="wrap">
  <h1>🇲🇾 Cina Narrative · Johor PRN 2026</h1>
  <p class="sub">Chinese_Response_Narative_Issues · PAS/PN Campaign Intel · InsightPulse<br/>
  Dijana: {stats.get('generated_at', '')[:19].replace('T',' ')} · Bukan polling SPR</p>

  <div class="grid">
    <div class="kpi"><label>Post</label><strong>{t.get('posts',0)}</strong></div>
    <div class="kpi"><label>Komen</label><strong>{t.get('comments',0)}</strong></div>
    <div class="kpi"><label>Engagement</label><strong>{t.get('engagement',0):,}</strong></div>
    <div class="kpi"><label>Views</label><strong>{t.get('views',0):,}</strong></div>
    <div class="kpi"><label>汉字 Content</label><strong>{n.get('chinese_script_rows',0)}</strong></div>
    <div class="kpi"><label>Johor-related</label><strong>{n.get('johor_related',0)}</strong></div>
  </div>

  <div class="panel">
    <h2>📊 Sentiment & Platform</h2>
    <p>Neg {neg} ({neg/total_sent*100:.0f}%) · Neutral {neu} ({neu/total_sent*100:.0f}%) · Pos {pos} ({pos/total_sent*100:.0f}%)</p>
    <p style="margin-top:8px;color:var(--muted)">Platform: {', '.join(f"{k} {v}" for k,v in plat.items())}</p>
    <div class="warn">
      <strong>Isu teras (Harakat/syurga):</strong> {n.get('harakat_syurga_cluster',0)} rekod ({n.get('core_issue_pct',0)}% dataset).
      Komuniti Cina <strong>belum ambil kisah</strong> isu syurga — fokus media Cina = ketelusan PAS–BN Johor.
    </div>
  </div>

  <div class="panel">
    <h2>🎯 Kesimpulan Naratif (Crawl 1–3 + analitik)</h2>
    <ul>
      <li><strong>Komuniti Cina ambil kisah?</strong> Isu syurga/Harakat → <strong>tidak</strong> (0 komen Cina). Isu PAS–BN Johor → <strong>ya, sederhana</strong> (Sin Chew 星洲, soal ketelusan).</li>
      <li><strong>Kepercayaan PAS (Cina):</strong> Skeptikal — tiada sokongan organik; risiko bila PAS naik pentas dengan MCA/BN tanpa penjelasan.</li>
      <li><strong>DAP/PH:</strong> Bertahan (Anwar jelaskan DAP pro-Melayu); guna isu “adakah kerjasama PAS–BN sebenar?” untuk kecohkan Cina.</li>
      <li><strong>BN/UMNO:</strong> Tersepit — dikritik Cina bila benarkan PAS; dikritik Melayu bila “halalkan” undi BN.</li>
      <li><strong>PAS (Melayu X):</strong> Kenyataan syurga viral tapi komen <strong>negatif</strong> — “penyamun”, “haji bodoh”.</li>
    </ul>
    <h3>Top kandungan 汉字</h3>
    <ul>{top_cn_html}</ul>
  </div>

  <div class="panel">
    <h2>🗳️ Strategi Kempen: Pastikan PAS + PN Menang Johor</h2>
    <p style="margin-bottom:12px">Baseline 2022: BN 40 · PH 12 · PN 3. Majoriti = 29. <strong>Muafakat 1-vs-1</strong> = pulangan maksimum lawan PH.</p>

    <h3>Lane A — Pengundi Melayu (56 kerusi)</h3>
    <div class="do"><strong>DO:</strong> Muafakat PN+BN · elak 3 penjuru · fokus kos hidup · disiplin undi (tanpa retorik syurga/heaven).</div>
    <div class="dont"><strong>DON'T:</strong> Ulang kenyataan “tak bau syurga” — ammo untuk lawan &amp; alienasi pengundi sederhana.</div>

    <h3>Lane B — Komuniti Cina (8 DUN bandar kritikal)</h3>
    <div class="do"><strong>DO:</strong> Jelaskan kerjasama PAS–BN = <em>estabil + anti-pecah undi</em> · kos hidup · perkhidmatan bandar · Shawn Loh / Pusat Khidmat Non-Muslim (fakta, bukan teologi).</div>
    <div class="dont"><strong>DON'T:</strong> Debate agama/syurga dengan komuniti Cina · biarkan DAP frame “PAS–BN rahsia” tanpa jawapan.</div>
    <div class="do"><strong>Naratif balas (CN):</strong> 国阵与伊党合作是为了州选稳定，不是秘密交易 — 聚焦民生、经济、治安。</div>

    <h3>Lane C — DAP/PH kubu bandar (pertahan + stretch)</h3>
    <table>
      <thead><tr><th>DUN</th><th>Nama</th><th>Profil</th><th>Risiko PH</th><th>Taktik Muafakat</th></tr></thead>
      <tbody>{seats_rows}</tbody>
    </table>
    <p style="margin-top:10px;font-size:0.85rem;color:var(--muted)">
      PH kekal ~13 kerusi jika muafakat gagal → PN untung split. <strong>Elak 3 penjuru</strong> di kerusi Melayu majoriti.
    </p>
  </div>

  <div class="panel">
    <h2>📡 Crawl 4 — Media Cina + FB (NEXT)</h2>
    <p>Jalankan 6 crawl dari <code>CRAWL_4_JOHOR_CN_FB.txt</code> — kemudian refresh dashboard:</p>
    <pre style="background:#0f172a;padding:12px;border-radius:8px;font-size:0.78rem;overflow:auto;margin-top:8px">NEImpulse/bin/python scripts/build_cina_narrative_dashboard.py</pre>
    <ol style="margin-top:10px;padding-left:20px;font-size:0.88rem">
      <li><strong>4A</strong> Sin Chew / China Press Johor (News)</li>
      <li><strong>4B</strong> 巫伊 / PAS–BN Johor (News + X)</li>
      <li><strong>4C</strong> FB group komuniti Cina JB/Skudai/Muar</li>
      <li><strong>4D</strong> Proxy pengundi Cina Johor</li>
      <li><strong>4E</strong> Isu respons syurga/Harakat/Shawn Loh</li>
      <li><strong>4F</strong> TikTok/IG muda Cina Johor</li>
    </ol>
  </div>

  <p style="color:var(--muted);font-size:0.75rem;margin-top:24px">
    InsightPulse · data/projects/political/Cina_Narative_2026 · Crawl dir: {CRAWL_DIR.name}/
  </p>
</div>
</body>
</html>"""


def main() -> int:
    df = load_crawls()
    stats = analyze(df)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_HTML.write_text(render_html(stats), encoding="utf-8")
    print(f"OK — records={stats.get('totals',{}).get('records',0)}")
    print(f"HTML: {OUT_HTML}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
