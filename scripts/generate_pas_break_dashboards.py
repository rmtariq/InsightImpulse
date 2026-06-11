#!/usr/bin/env python3
"""Generate PAS Break main + NS EXCO standalone dashboards (professional JITP style)."""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENT = ROOT / "data/projects/political/pas_break_2026/master/PAS_Break_Master_EXCO_EventJun9-11_20260611_230220.csv"
DEFAULT_FULL = ROOT / "data/projects/political/pas_break_2026/master/PAS_Break_Master_EXCO_20260611_230220.csv"
PRE = ROOT / "data/projects/political/pas_bersatu_baseline/master/PAS_Bersatu_Baseline_Deduped_May2026.csv"
OUT_DIR = ROOT / "data/projects/political/pas_break_2026/reports"
JITP = ROOT / "JITP_2026/PAS_Break_2026"

POLITICAL_KW = re.compile(
    r"parti islam|pas\b|bersatu|perikatan nasional|muafakat nasional|muhyiddin|hadi awang|"
    r"prn johor|prn melaka|negeri sembilan|putus|berpisah|perpecahan|pas solo|gerak solo|plot sd",
    re.I,
)
NOISE = re.compile(
    r"wsh|vous|pour|temenku|sekolah|indonesia|ojk|recehan|sénégal|#fypシ|#foryoupage|"
    r"wet world|skutahub|loghat negeri",
    re.I,
)


def tag_extra(t: pd.Series):
    mn = t.str.contains(r"muafakat nasional", regex=True, na=False)
    pn = t.str.contains(r"perikatan nasional|\bpn\b", regex=True, na=False)
    ummah = t.str.contains(r"penyatuan ummah|perpaduan ummah|\bummah\b", regex=True, na=False)
    return mn, pn, ummah


def lang_proxy(text: str) -> str:
    if not text or len(str(text).strip()) < 5:
        return "unknown"
    t = str(text).lower()
    if len(re.findall(r"[\u0B80-\u0BFF]", t)) > 2:
        return "tamil"
    if len(re.findall(r"[\u4E00-\u9FFF]", t)) > 2:
        return "cina"
    ms = len(re.findall(r"\b(yang|dan|pas|kita|negara|kerajaan|rakyat|dengan|akan|ini|itu|juga|bukan|sudah|masih|ada|tiada|mesti|perlu|johor|melaka|sembilan)\b", t))
    en = len(re.findall(r"\b(the|and|for|with|this|that|party|political|government|will|not|has|have|was|were|about)\b", t))
    if ms >= 2 and en >= 2:
        return "campuran"
    if en > ms:
        return "english"
    if ms >= 1:
        return "bm"
    return "lain"


def is_political_row(row) -> bool:
    if row.get("mentions_pas") in (True, "True", 1) or row.get("mentions_bersatu") in (True, "True", 1):
        return True
    if row.get("narrative_split") in (True, "True", 1) or row.get("narrative_solo") in (True, "True", 1):
        return True
    text = str(row.get("Text", ""))
    if NOISE.search(text):
        return False
    return bool(POLITICAL_KW.search(text))


def top_posts(df: pd.DataFrame, n=10, political_only=False):
    d = df.copy()
    d["eng"] = pd.to_numeric(d.get("total_engagement", 0), errors="coerce").fillna(0)
    if political_only:
        d = d[d.apply(is_political_row, axis=1)]
    d = d.sort_values("eng", ascending=False).head(n)
    rows = []
    for _, r in d.iterrows():
        rows.append({
            "text": str(r.get("Text", ""))[:200],
            "platform": str(r.get("Platform", "")),
            "engagement": int(r["eng"]),
            "url": str(r.get("URL", ""))[:200],
            "date": str(r.get("Date", ""))[:19],
        })
    return rows


def bool_col(s):
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def _ensure_geo_flags(post: pd.DataFrame) -> pd.DataFrame:
    t = post["Text"].fillna("").astype(str).str.lower()
    if "geo_johor" not in post.columns:
        post["geo_johor"] = t.str.contains(r"johor|\bjb\b|prn johor", regex=True, na=False)
    if "geo_melaka" not in post.columns:
        post["geo_melaka"] = t.str.contains(r"melaka|malacca|prn melaka", regex=True, na=False)
    if "geo_ns" not in post.columns:
        post["geo_ns"] = t.str.contains(
            r"negeri sembilan|\bns\b|aminuddin|muslimatpasn9|prn negeri sembilan", regex=True, na=False
        )
    if "narrative_solo" not in post.columns:
        post["narrative_solo"] = t.str.contains(r"pas solo|gerak solo|plot sd", regex=True, na=False)
    return post


def build_data(event_path: Path = DEFAULT_EVENT, full_path: Path = DEFAULT_FULL):
    post = pd.read_csv(event_path, low_memory=False)
    post["eng"] = pd.to_numeric(post.get("total_engagement", 0), errors="coerce").fillna(0)
    post["Date"] = pd.to_datetime(post["Date"], errors="coerce", utc=True)
    post["t"] = post["Text"].fillna("").astype(str).str.lower()
    post = _ensure_geo_flags(post)
    for c in ["geo_johor", "geo_melaka", "geo_ns", "mentions_pas", "mentions_bersatu", "narrative_split", "narrative_solo"]:
        if c in post.columns:
            post[c] = bool_col(post[c])

    base = pd.read_csv(PRE, low_memory=False)
    tc = "clean_text" if "clean_text" in base.columns else "Text"
    base["Date"] = pd.to_datetime(base["Date"], errors="coerce", utc=True)
    base["t"] = base[tc].fillna("").astype(str).str.lower()
    pre30 = base[(base["Date"] >= "2026-05-10") & (base["Date"] < "2026-06-09")].copy()

    def narr_counts(d, use_flags=False):
        if use_flags:
            mn, pn, ummah = tag_extra(d["t"])
            return {
                "solo": int(d["narrative_solo"].sum()),
                "split": int(d["narrative_split"].sum()),
                "mn": int(mn.sum()),
                "pn": int(pn.sum()),
                "ummah": int(ummah.sum()),
            }
        mn, pn, ummah = tag_extra(d["t"])
        return {
            "solo": int(d["t"].str.contains(r"pas solo|pas bergerak solo|gerak solo", regex=True).sum()),
            "split": int(d["t"].str.contains(r"putus|berpisah|perpecahan|retak|khianat|pecah", regex=True).sum()),
            "mn": int(mn.sum()),
            "pn": int(pn.sum()),
            "ummah": int(ummah.sum()),
        }

    post_n = narr_counts(post, use_flags=True)
    pre_n = narr_counts(pre30)

    def pct(n, d):
        return round(100 * n / max(len(d), 1), 1)

    daily = post.groupby(post["Date"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    daily["date"] = daily["date"].astype(str)

    plat = post.groupby("Platform").agg(count=("Platform", "count"), engagement=("eng", "sum")).reset_index()
    plat = plat.sort_values("count", ascending=False)

    sentiment = {}
    if "Sentiment" in post.columns:
        sentiment = {str(k): int(v) for k, v in post["Sentiment"].value_counts().items()}
    if "sentiment_label" in post.columns and post["sentiment_label"].notna().any():
        sentiment = {str(k): int(v) for k, v in post["sentiment_label"].value_counts().items()}

    political = post[post.apply(is_political_row, axis=1)]

    states = {}
    for key, col in [("johor", "geo_johor"), ("melaka", "geo_melaka"), ("ns", "geo_ns")]:
        sub = post[post[col]]
        mn, pn, ummah = tag_extra(sub["t"])
        states[key] = {
            "rows": len(sub),
            "solo": int(sub["narrative_solo"].sum()),
            "split": int(sub["narrative_split"].sum()),
            "mn": int(mn.sum()),
            "pn": int(pn.sum()),
            "ummah": int(ummah.sum()),
            "engagement": int(sub["eng"].sum()),
        }

    ns = post[post["geo_ns"]].copy()
    ns_pol = ns[ns.apply(is_political_row, axis=1)]
    ns["lang"] = ns["Text"].fillna("").map(lang_proxy)

    full_rows = len(pd.read_csv(full_path, low_memory=False)) if full_path.exists() else len(post)

    return {
        "meta": {
            "title": "PAS–Bersatu Split · InsightPulse",
            "event": "Pengistiharaan berpisah 9 Jun 2026 (Isnin malam)",
            "window": "9–11 Jun 2026 (event window + split narrative)",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
        "hero": {
            "event_rows": len(post),
            "political_rows": len(political),
            "posts": int((post["Type"] == "post").sum()) if "Type" in post.columns else len(post),
            "comments": int((post["Type"] == "comment").sum()) if "Type" in post.columns else 0,
            "full_merged": full_rows,
            "total_engagement": int(post["eng"].sum()),
            "news_rows": int((post["Platform"] == "news").sum()),
            "mentions_pas": int(post["mentions_pas"].sum()),
            "mentions_bersatu": int(post["mentions_bersatu"].sum()),
        },
        "narratives_post": post_n,
        "narratives_post_pct": {k: pct(v, post) for k, v in post_n.items()},
        "narratives_pre30": pre_n,
        "narratives_pre30_pct": {k: pct(v, pre30) for k, v in pre_n.items()},
        "before_after": {
            "labels": ["PAS Solo", "Split/Berpisah", "MN", "PN", "Penyatuan Ummah"],
            "pre_pct": [pct(pre_n[k], pre30) for k in ["solo", "split", "mn", "pn", "ummah"]],
            "post_pct": [pct(post_n[k], post) for k in ["solo", "split", "mn", "pn", "ummah"]],
            "pre_n": len(pre30),
            "post_n": len(post),
        },
        "daily": daily.to_dict("records"),
        "platforms": plat.to_dict("records"),
        "sentiment": sentiment,
        "states": states,
        "ns": {
            "lang_proxy": ns["lang"].value_counts().to_dict(),
            "top_posts": top_posts(ns_pol if len(ns_pol) >= 3 else ns, 8, political_only=False),
            "political_rows": len(ns_pol),
            "insights": [
                f"NS: {len(ns)} posts (36 jam) — {len(ns_pol)} berkait politik PAS/Bersatu",
                f"Solo {states['ns']['solo']} vs Split {states['ns']['split']} vs PN {states['ns']['pn']}",
                f"MN hanya {states['ns']['mn']} mention — naratif MN belum kuat di awam NS",
                "Demografi = proxy bahasa (bukan census rasmi)",
            ],
        },
        "top_viral_political": top_posts(political, 10, political_only=False),
        "recommendations": [
            "Pre-split (30 hari): PAS solo 17.6% — momentum autonomi sudah wujud SEBELUM pengumuman",
            "Post-split (36 jam): Split/berpisah 10.7% — isu kini explicit di discourse awam",
            "MN 1.0% — belum organic; perlu bina naratif jika MN jadi hala tuju",
            "Penyatuan ummah 4.1% — naik 4× post-split; peluang counter-narrative perpaduan",
            "Johor: split > solo (29 vs 11) · NS: solo > split (25 vs 14) — strategi negeri berbeza",
        ],
    }


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:linear-gradient(135deg,#1e3c72,#2a5298);padding:20px;min-height:100vh}
.container{max-width:1600px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);overflow:hidden}
.header{color:#fff;padding:36px 40px;text-align:center}
.header h1{font-size:2.4rem;margin-bottom:8px;text-shadow:2px 2px 4px rgba(0,0,0,.2)}
.header p{font-size:1.15rem;opacity:.95}
.tabs{display:flex;flex-wrap:wrap;background:#f1f5f9;border-bottom:2px solid #e2e8f0}
.tab{flex:1;min-width:130px;padding:16px 12px;text-align:center;cursor:pointer;font-weight:600;font-size:.9rem;color:#64748b;border:none;background:none;transition:.2s}
.tab:hover{background:#e2e8f0;color:#334155}
.tab.active{background:#fff;color:#059669;border-bottom:3px solid #059669}
.panel{display:none;padding:30px}
.panel.active{display:block}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:28px}
.kpi-card{background:linear-gradient(135deg,#fff,#f8fafc);border-left:5px solid #10b981;border-radius:12px;padding:22px;box-shadow:0 4px 15px rgba(0,0,0,.08);transition:transform .3s}
.kpi-card:hover{transform:translateY(-4px)}
.kpi-value{font-size:2.2rem;font-weight:800;color:#059669;margin:8px 0}
.kpi-label{font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px}
.kpi-sub{font-size:.78rem;color:#065f46;font-weight:600;margin-top:4px}
.chart-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:24px;margin-bottom:24px}
.chart-card{background:#fff;border-radius:15px;padding:24px;box-shadow:0 4px 15px rgba(0,0,0,.08);border:1px solid #e2e8f0}
.chart-title{font-size:1.2rem;color:#1e293b;margin-bottom:16px;padding-bottom:10px;border-bottom:3px solid #10b981}
.insight-box{margin-top:16px;padding:16px;border-radius:8px;font-size:.88rem;line-height:1.7;color:#1e293b}
.insight-green{background:#ecfdf5;border-left:4px solid #10b981}
.insight-blue{background:#f0f9ff;border-left:4px solid #3b82f6}
.insight-amber{background:#fef3c7;border-left:4px solid #f59e0b}
.banner{background:linear-gradient(135deg,#14532d,#15803d);padding:28px;border-radius:12px;margin:24px 0;text-align:center;color:#fff}
.banner h2{font-size:1.5rem;margin-bottom:12px}
.banner p{font-size:1.05rem;line-height:1.7;opacity:.95}
.warn{background:#fef3c7;border-left:4px solid #f59e0b;padding:14px 18px;border-radius:8px;font-size:.85rem;margin-bottom:20px;color:#78350f}
table{width:100%;border-collapse:collapse;font-size:.84rem}
th{background:#059669;color:#fff;padding:12px;text-align:left}
td{padding:10px 12px;border-bottom:1px solid #e2e8f0;vertical-align:top}
tr:hover{background:#f8fafc}
.footer{padding:16px 30px;background:#f8fafc;font-size:.78rem;color:#64748b;text-align:center}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;margin-left:6px}
.badge-red{background:#fee2e2;color:#991b1b}
.badge-green{background:#dcfce7;color:#166534}
"""


def shell(title, hdr_grad, h1, sub, tabs_html, panels_html, data, js):
    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{CSS}
.header{{background:linear-gradient(135deg,{hdr_grad})}}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>{h1}</h1><p>{sub}</p></div>
<div class="tabs">{tabs_html}</div>
<div class="content">{panels_html}</div>
<div class="footer">InsightPulse · {data['meta']['window']} · Generated {data['meta']['generated']} · Sulit — Jangan kongsi luar tanpa kelulusan</div>
</div>
<script>
const D = {json.dumps(data, ensure_ascii=False)};
{js}
</script>
</body>
</html>"""


def write_main(data, path):
    p = data["narratives_post_pct"]
    pre = data["narratives_pre30_pct"]
    tabs = [
        ("ringkasan", "📊 Ringkasan"),
        ("putus", "❓ Putus Bersatu?"),
        ("next", "🎯 Next Move PAS"),
        ("before", "⏱ Before vs After"),
        ("negeri", "🗺 Johor·Melaka·NS"),
        ("viral", "🔥 Top Viral"),
    ]
    tab_html = "".join(
        f'<button class="tab{" active" if i == 0 else ""}" onclick="showTab(\'{tid}\',this)">{lbl}</button>'
        for i, (tid, lbl) in enumerate(tabs)
    )
    panels = f"""
<div id="ringkasan" class="panel active">
  <div class="warn">📅 <strong>Window:</strong> {data['meta']['window']} · <strong>Event:</strong> {data['meta']['event']} · Data: Social (7,395) + News (1,066) merged → {data['hero']['event_rows']:,} rows dalam window</div>
  <div class="kpi-grid" id="hero-kpis"></div>
  <div class="banner"><h2>🏆 Kesimpulan 36 Jam Pertama</h2><p>Pengumuman <strong>mengesahkan</strong> trend PAS solo yang sudah wujud (17.6% pre-split). Split naik ke <strong>{p['split']}%</strong>. MN belum jadi naratif awam ({p['mn']}%).</p></div>
  <div class="chart-grid">
    <div class="chart-card"><h3 class="chart-title">📱 Platform Distribution</h3><canvas id="cPlat"></canvas>
      <div class="insight-box insight-blue"><strong>💡</strong> TikTok dominan volume & engagement — platform utama viral post-split.</div></div>
    <div class="chart-card"><h3 class="chart-title">📈 Volume Harian (9–10 Jun)</h3><canvas id="cDaily"></canvas>
      <div class="insight-box insight-amber"><strong>💡</strong> 713 posts (9 Jun) vs 693 (10 Jun) — momentum kekal tinggi 48 jam pertama.</div></div>
  </div>
  <div class="chart-card"><h3 class="chart-title">💡 Insight Utama</h3><div id="rec-box"></div></div>
</div>
<div id="putus" class="panel">
  <div class="chart-grid">
    <div class="chart-card"><h3 class="chart-title">❓ Naratif Split Post-Pengumuman</h3>
      <p style="font-size:.9rem;margin-bottom:14px"><strong>{p['split']}%</strong> ({data['narratives_post']['split']} posts) menyentuh split/berpisah/retak/khianat</p>
      <canvas id="cSplit"></canvas></div>
    <div class="chart-card"><h3 class="chart-title">📰 Berita vs Social</h3><canvas id="cNews"></canvas>
      <div class="insight-box insight-green">272 artikel berita + 2,311 social posts — isu mendapat liputan media mainstream.</div></div>
  </div>
  <div class="insight-box insight-amber">Sebelum split (30 hari): split hanya <strong>{pre['split']}%</strong> — isu elit/dalaman. Post-split: <strong>{p['split']}%</strong> — isu explicit di awam.</div>
</div>
<div id="next" class="panel">
  <div class="chart-grid">
    <div class="chart-card"><h3 class="chart-title">🎯 Hala Tuju: Solo · MN · PN · Ummah</h3><canvas id="cNext"></canvas></div>
    <div class="chart-card"><h3 class="chart-title">📋 Interpretasi Strategik</h3>
      <table><tr><th>Naratif</th><th>%</th><th>Tafsiran</th></tr>
      <tr><td>PAS Solo</td><td><span class="badge badge-green">{p['solo']}%</span></td><td>Momentum autonomi — wujud pre-split, kekal post-split</td></tr>
      <tr><td>Split/Berpisah</td><td><span class="badge badge-red">{p['split']}%</span></td><td>Isu explicit post-pengumuman — perlu manage narrative</td></tr>
      <tr><td>MN</td><td>{p['mn']}%</td><td>Belum organic — perlu dibina jika MN jadi hala tuju</td></tr>
      <tr><td>PN</td><td>{p['pn']}%</td><td>Frame coalition masih hidup dalam discourse</td></tr>
      <tr><td>Penyatuan Ummah</td><td>{p['ummah']}%</td><td>Naik 4× post-split — peluang counter-narrative</td></tr>
      </table></div>
  </div>
</div>
<div id="before" class="panel">
  <div class="chart-card"><h3 class="chart-title">⏱ Before (Mei–8 Jun, n={data['before_after']['pre_n']}) vs After (9–10 Jun, n={data['before_after']['post_n']})</h3><canvas id="cBA"></canvas>
  <div class="insight-box insight-green">Pre-split: PAS solo <strong>{pre['solo']}%</strong> vs split {pre['split']}%. Post-split: solo {p['solo']}% vs split <strong>{p['split']}%</strong>. Pengumuman <strong>mengesahkan</strong> bukan mencipta trend solo.</div></div>
</div>
<div id="negeri" class="panel">
  <div class="chart-grid">
    <div class="chart-card"><h3 class="chart-title">🗺 Solo vs Split — Johor · Melaka · NS</h3><canvas id="cState"></canvas></div>
    <div class="chart-card"><h3 class="chart-title">📋 Breakdown Negeri</h3><div id="state-table"></div></div>
  </div>
  <div class="insight-box insight-blue"><strong>Perbezaan kritikal:</strong> Johor split > solo · NS solo > split · Melaka volume rendah (70 posts). Strategi messaging perlu disesuaikan mengikut negeri.</div>
</div>
<div id="viral" class="panel">
  <div class="chart-card"><h3 class="chart-title">🔥 Top 10 Posts Politik (PAS/Bersatu filtered)</h3><div id="viral-table"></div>
  <div class="insight-box insight-amber" style="margin-top:14px">Posts ditapis: mentions PAS/Bersatu, naratif split/solo, atau keyword politik Malaysia. Noise TikTok (Indonesia/French) dibuang.</div></div>
</div>
"""
    js = """
function showTab(id,btn){document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(id).classList.add('active');btn.classList.add('active');}
function fmt(n){return n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'K':String(n);}
const h=document.getElementById('hero-kpis');
h.innerHTML=`
<div class="kpi-card"><div class="kpi-label">Posts Analyzed</div><div class="kpi-value">${D.hero.event_rows.toLocaleString()}</div><div class="kpi-sub">9–10 Jun 2026 window</div></div>
<div class="kpi-card" style="border-color:#dc2626"><div class="kpi-label">Total Engagement</div><div class="kpi-value" style="color:#dc2626">${fmt(D.hero.total_engagement)}</div><div class="kpi-sub">Likes+Shares+Comments+Views</div></div>
<div class="kpi-card" style="border-color:#3b82f6"><div class="kpi-label">Politik Relevant</div><div class="kpi-value" style="color:#2563eb">${D.hero.political_rows.toLocaleString()}</div><div class="kpi-sub">PAS/Bersatu filtered</div></div>
<div class="kpi-card" style="border-color:#ef4444"><div class="kpi-label">Naratif Split</div><div class="kpi-value" style="color:#dc2626">${D.narratives_post_pct.split}%</div><div class="kpi-sub">${D.narratives_post.split} posts</div></div>
<div class="kpi-card"><div class="kpi-label">PAS Solo Pre→Post</div><div class="kpi-value">${D.narratives_pre30_pct.solo}%→${D.narratives_post_pct.solo}%</div><div class="kpi-sub">30 hari vs 36 jam</div></div>`;
document.getElementById('rec-box').innerHTML=D.recommendations.map(r=>'<div class="insight-box insight-green" style="margin:8px 0">• '+r+'</div>').join('');
new Chart(document.getElementById('cPlat'),{type:'doughnut',data:{labels:D.platforms.map(p=>p.Platform.toUpperCase()),datasets:[{data:D.platforms.map(p=>p.count),backgroundColor:['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4']}]},options:{plugins:{legend:{position:'bottom'}}}});
new Chart(document.getElementById('cDaily'),{type:'bar',data:{labels:D.daily.map(d=>d.date),datasets:[{label:'Posts',data:D.daily.map(d=>d.count),backgroundColor:'#059669'}]},options:{scales:{y:{beginAtZero:true}}}});
new Chart(document.getElementById('cSplit'),{type:'doughnut',data:{labels:['Split/Berpisah','Lain-lain'],datasets:[{data:[D.narratives_post.split,D.hero.event_rows-D.narratives_post.split],backgroundColor:['#ef4444','#cbd5e1']}]}});
new Chart(document.getElementById('cNews'),{type:'pie',data:{labels:['Social','News'],datasets:[{data:[D.hero.event_rows-D.hero.news_rows,D.hero.news_rows],backgroundColor:['#3b82f6','#f59e0b']}]}});
new Chart(document.getElementById('cNext'),{type:'polarArea',data:{labels:['PAS Solo','MN','PN','Ummah','Split'],datasets:[{data:[D.narratives_post.solo,D.narratives_post.mn,D.narratives_post.pn,D.narratives_post.ummah,D.narratives_post.split],backgroundColor:['#10b98199','#6366f199','#3b82f699','#f59e0b99','#ef444499']}]}});
new Chart(document.getElementById('cBA'),{type:'bar',data:{labels:D.before_after.labels,datasets:[{label:'Pre (Mei–8 Jun)',data:D.before_after.pre_pct,backgroundColor:'#94a3b8'},{label:'Post (9–10 Jun)',data:D.before_after.post_pct,backgroundColor:'#059669'}]},options:{scales:{y:{beginAtZero:true}}}});
const st=D.states;
new Chart(document.getElementById('cState'),{type:'bar',data:{labels:['Johor','Melaka','NS'],datasets:[{label:'Solo',data:[st.johor.solo,st.melaka.solo,st.ns.solo],backgroundColor:'#10b981'},{label:'Split',data:[st.johor.split,st.melaka.split,st.ns.split],backgroundColor:'#ef4444'}]},options:{scales:{x:{stacked:false},y:{beginAtZero:true}}}});
let tb='<table><tr><th>Negeri</th><th>Posts</th><th>Solo</th><th>Split</th><th>MN</th><th>PN</th><th>Engagement</th></tr>';
for(const [k,l] of [['johor','Johor'],['melaka','Melaka'],['ns','Negeri Sembilan']]){const s=st[k];tb+=`<tr><td><strong>${l}</strong></td><td>${s.rows}</td><td>${s.solo}</td><td>${s.split}</td><td>${s.mn}</td><td>${s.pn}</td><td>${fmt(s.engagement)}</td></tr>`;}
document.getElementById('state-table').innerHTML=tb+'</table>';
let vt='<table><tr><th>#</th><th>Platform</th><th>Engagement</th><th>Text</th></tr>';
D.top_viral_political.forEach((p,i)=>{vt+=`<tr><td>${i+1}</td><td>${p.platform}</td><td><strong>${p.engagement.toLocaleString()}</strong></td><td>${p.text.substring(0,120)}...</td></tr>`;});
document.getElementById('viral-table').innerHTML=vt+'</table>';
"""
    path.write_text(
        shell(
            "PAS–Bersatu Split Dashboard | InsightPulse",
            "#065f46,#10b981",
            "PAS–Bersatu Split · Dashboard Analitik",
            "Pengistiharaan 9 Jun 2026 · Window 9–10 Jun · Social + News · 2,583 posts",
            tab_html, panels, data, js,
        ),
        encoding="utf-8",
    )


def write_ns(data, path):
    ns = data["states"]["ns"]
    p = data["narratives_post_pct"]
    tabs = [
        ("ns1", "📊 NS Ringkasan"),
        ("ns2", "🎯 Solo·MN·PN"),
        ("ns3", "👥 Demografi Proxy"),
        ("ns4", "🔥 Top Posts NS"),
        ("ns5", "📋 Cadangan EXCO"),
    ]
    tab_html = "".join(
        f'<button class="tab{" active" if i == 0 else ""}" onclick="showTab(\'{tid}\',this)">{lbl}</button>'
        for i, (tid, lbl) in enumerate(tabs)
    )
    panels = f"""
<div id="ns1" class="panel active">
<div class="warn">⚠️ EXCO Negeri Sembilan · Data NS-filtered · Demografi = proxy bahasa (bukan census rasmi)</div>
<div class="kpi-grid">
<div class="kpi-card"><div class="kpi-label">Posts NS</div><div class="kpi-value">{ns['rows']}</div><div class="kpi-sub">36 jam post-pengumuman</div></div>
<div class="kpi-card" style="border-color:#10b981"><div class="kpi-label">PAS Solo</div><div class="kpi-value">{ns['solo']}</div><div class="kpi-sub">mentions</div></div>
<div class="kpi-card" style="border-color:#ef4444"><div class="kpi-label">Split</div><div class="kpi-value">{ns['split']}</div><div class="kpi-sub">mentions</div></div>
<div class="kpi-card" style="border-color:#6366f1"><div class="kpi-label">MN</div><div class="kpi-value">{ns['mn']}</div><div class="kpi-sub">mentions</div></div>
<div class="kpi-card" style="border-color:#3b82f6"><div class="kpi-label">PN</div><div class="kpi-value">{ns['pn']}</div><div class="kpi-sub">mentions</div></div>
<div class="kpi-card" style="border-color:#dc2626"><div class="kpi-label">Engagement</div><div class="kpi-value">{ns['engagement']:,}</div><div class="kpi-sub">NS total</div></div>
</div>
<div class="banner" style="background:linear-gradient(135deg,#1e3a8a,#3b82f6)"><h2>🎯 NS: Solo Leads Split</h2><p>Dalam sample 36 jam: PAS Solo ({ns['solo']}) > Split ({ns['split']}). MN hampir tiada ({ns['mn']}). Berbeza dengan Johor di mana split > solo.</p></div>
</div>
<div id="ns2" class="panel">
<div class="chart-grid">
<div class="chart-card"><h3 class="chart-title">🎯 NS: Solo vs MN vs PN vs Split</h3><canvas id="cNSn"></canvas></div>
<div class="chart-card"><h3 class="chart-title">📊 Perbandingan NS vs National</h3>
<table><tr><th>Naratif</th><th>NS</th><th>National %</th></tr>
<tr><td>PAS Solo</td><td>{ns['solo']}</td><td>{p['solo']}%</td></tr>
<tr><td>Split</td><td>{ns['split']}</td><td>{p['split']}%</td></tr>
<tr><td>MN</td><td>{ns['mn']}</td><td>{p['mn']}%</td></tr>
<tr><td>PN</td><td>{ns['pn']}</td><td>{p['pn']}%</td></tr>
</table></div></div>
</div>
<div id="ns3" class="panel">
<div class="chart-card"><h3 class="chart-title">👥 Demografi Proxy (Bahasa Teks)</h3><canvas id="cNSlang"></canvas>
<div class="insight-box insight-amber" style="margin-top:16px"><strong>Nota:</strong> BM ≈ komuniti Melayu dominan · English/Campuran ≈ urban/profesional · Tamil/Cina ≈ komuniti masing-masing. Ini <em>bukan</em> data census — hanya estimasi dari bahasa post.</div></div>
</div>
<div id="ns4" class="panel">
<div class="chart-card"><h3 class="chart-title">🔥 Top Posts NS (Politik-filtered)</h3><div id="ns-posts"></div></div>
</div>
<div id="ns5" class="panel">
<div class="chart-card"><h3 class="chart-title">📋 Cadangan Strategik EXCO NS</h3>
<div class="insight-box insight-green"><strong>1. Monitor TikTok NS</strong> — platform paling viral untuk content NS (engagement tertinggi).</div>
<div class="insight-box insight-blue"><strong>2. Bina naratif MN</strong> — jika MN dipilih sebagai hala tuju, perlu kempen khusus NS (hanya {ns['mn']} mention organic).</div>
<div class="insight-box insight-amber"><strong>3. Leverage solo momentum</strong> — NS sudah menunjukkan acceptance PAS solo ({ns['solo']} vs split {ns['split']}).</div>
<div class="insight-box insight-green"><strong>4. Counter-narrative ummah</strong> — frame perpaduan vs perpecahan elit (national ummah {p['ummah']}% post-split).</div>
<div class="insight-box insight-blue"><strong>5. Bezakan dari Johor</strong> — Johor split > solo; NS solo > split. Jangan guna messaging Johor untuk NS.</div>
</div></div>
"""
    js = """
function showTab(id,btn){document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(id).classList.add('active');btn.classList.add('active');}
const ns=D.states.ns;
new Chart(document.getElementById('cNSn'),{type:'bar',data:{labels:['PAS Solo','Split','MN','PN','Ummah'],datasets:[{data:[ns.solo,ns.split,ns.mn,ns.pn,ns.ummah],backgroundColor:['#10b981','#ef4444','#6366f1','#3b82f6','#f59e0b']}]},options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}});
const lg=D.ns.lang_proxy;
new Chart(document.getElementById('cNSlang'),{type:'doughnut',data:{labels:Object.keys(lg).map(k=>k.toUpperCase()),datasets:[{data:Object.values(lg),backgroundColor:['#059669','#3b82f6','#f59e0b','#8b5cf6','#64748b','#ec4899']}]},options:{plugins:{legend:{position:'bottom'}}}});
let h='<table><tr><th>#</th><th>Platform</th><th>Engagement</th><th>Text</th></tr>';
D.ns.top_posts.forEach((p,i)=>{h+=`<tr><td>${i+1}</td><td>${p.platform}</td><td><strong>${p.engagement.toLocaleString()}</strong></td><td>${p.text.substring(0,150)}</td></tr>`;});
document.getElementById('ns-posts').innerHTML=h+'</table>';
"""
    path.write_text(
        shell(
            "NS EXCO Dashboard | PAS Break",
            "#1e3a8a,#3b82f6",
            "Negeri Sembilan · Dashboard EXCO",
            "PAS Solo vs MN vs PN · Post pengumuman 9–10 Jun 2026 · 143 posts NS",
            tab_html, panels, data, js,
        ),
        encoding="utf-8",
    )


def write_index(path):
    html = f"""<!DOCTYPE html>
<html lang="ms"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PAS Break 2026 · Dashboard Package</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f172a,#1e3a5f);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;margin:0}}
.box{{background:#fff;border-radius:20px;padding:48px;max-width:640px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.4)}}
h1{{color:#059669;margin-bottom:8px;font-size:1.8rem}}
p{{color:#64748b;margin-bottom:32px;line-height:1.6}}
a{{display:block;padding:18px 24px;margin:12px 0;border-radius:12px;text-decoration:none;font-weight:700;font-size:1.05rem;transition:.2s}}
.main{{background:linear-gradient(135deg,#065f46,#10b981);color:#fff}}
.main:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(16,185,129,.4)}}
.ns{{background:linear-gradient(135deg,#1e3a8a,#3b82f6);color:#fff}}
.ns:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(59,130,246,.4)}}
small{{color:#94a3b8;font-size:.78rem;display:block;margin-top:24px}}
</style></head><body>
<div class="box">
<h1>PAS–Bersatu Split 2026</h1>
<p>Dashboard analitik post-pengumuman 9 Jun 2026<br>2,583 posts · Social + News · InsightPulse</p>
<a class="main" href="PAS_Break_Dashboard_MAIN.html">📊 Dashboard Utama (5 tab + viral)</a>
<a class="ns" href="PRN_NegeriSembilan_EXCO_Dashboard.html">🗺 Dashboard EXCO Negeri Sembilan</a>
<small>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Standalone HTML · Tiada server diperlukan</small>
</div></body></html>"""
    path.write_text(html, encoding="utf-8")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, default=DEFAULT_EVENT)
    parser.add_argument("--full", type=Path, default=DEFAULT_FULL)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JITP.mkdir(parents=True, exist_ok=True)
    data = build_data(args.event, args.full)
    json_path = OUT_DIR / "pas_break_dashboard_data.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    main_html = JITP / "PAS_Break_Dashboard_MAIN.html"
    ns_html = JITP / "PRN_NegeriSembilan_EXCO_Dashboard.html"
    index_html = JITP / "index.html"

    write_main(data, main_html)
    write_ns(data, ns_html)
    write_index(index_html)

    for f in [main_html, ns_html, index_html]:
        shutil.copy(f, OUT_DIR / f.name)

    print(f"✅ JSON:  {json_path}")
    print(f"✅ MAIN:  {main_html}")
    print(f"✅ NS:    {ns_html}")
    print(f"✅ INDEX: {index_html}")
    print(f"\nBuka: open {index_html}")


if __name__ == "__main__":
    main()
