#!/usr/bin/env python3
"""Halatuju N9: logo PAS sendiri + seat-sharing (BUKAN solo penuh).

Grounded in lesson PRN Johor + crawl naratif Cina/India N9 + War Room ops.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
OPS_JSON = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_daily_ops.json"
OFFICIAL_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reference/official_statements"
HADI_SIDANG = OFFICIAL_DIR / "hadi_sidang_media_n9_20260712_0qSESgWMoG8.json"


def _load_n9_ops_context() -> Dict[str, Any]:
    if not OPS_JSON.exists():
        return {}
    try:
        return json.loads(OPS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_official_statement() -> Dict[str, Any]:
    if not HADI_SIDANG.exists():
        return {}
    try:
        return json.loads(HADI_SIDANG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_halatuju_brief(data: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
    n9 = (data.get("states") or {}).get("N9", {})
    ch, ind = n9.get("chinese", {}), n9.get("indian", {})
    ops = _load_n9_ops_context()
    keputusan = ops.get("keputusan") or {}
    mn_vs_solo = keputusan.get("mn_vs_solo_pct")
    filtered = data.get("filtered_rows") or 0
    eng = data.get("engagement_label") or "—"
    date_range = data.get("date_range") or "—"
    ch_posts, ch_neg = ch.get("posts", 0), ch.get("neg_pct", 0)
    ind_posts = ind.get("posts", 0)
    ch_top = (ch.get("issues") or [["—", 0]])[0]
    ind_top = (ind.get("issues") or [["—", 0]])[0]
    boycott = (brief.get("n9") or {}).get("chinese", {}).get("boycott_risk", "medium")
    stmt = _load_official_statement()
    src = stmt.get("source") or {}
    eng_cap = stmt.get("engagement_at_capture") or {}
    align = stmt.get("alignment_with_halatuju") or {}
    ci_imp = stmt.get("implications_for_cina_india") or {}
    fu = stmt.get("followup_checklist") or {}
    official_banner = None
    if stmt:
        official_banner = {
            "id": stmt.get("id"),
            "status": stmt.get("status"),
            "title": src.get("title") or "Sidang Media N9",
            "speaker": src.get("speaker") or "Presiden PAS",
            "url": src.get("url"),
            "upload_date": src.get("upload_date"),
            "views": eng_cap.get("view_count"),
            "likes": eng_cap.get("like_count"),
            "comments": eng_cap.get("comment_count"),
            "engagement_note": eng_cap.get("note"),
            "key_points": [p.get("point") for p in (stmt.get("key_points_draft") or []) if p.get("point")],
            "match": align.get("match") or [],
            "tension": align.get("tension") or [],
            "cina_india_now": ci_imp.get("now"),
            "cina_india_risk": ci_imp.get("risk"),
            "followup_due": fu.get("due_after"),
            "transcript_quality": (stmt.get("transcript") or {}).get("quality_note"),
        }

    return {
        "verdict": "BUKAN solo penuh",
        "formula": "Logo bulan PAS sendiri + runding seat-sharing dengan Bersatu / Wawasan / Berjasa",
        "deadline": "2026-07-18",
        "deadline_label": "18 Julai 2026 — penamaan calon",
        "official_statement": official_banner,
        "johor_lesson": {
            "headline": "PRN Johor: PAS 0/11 kerusi · PN 0/56 keseluruhan",
            "punca": [
                "PAS–Bersatu berkempen berasingan (isu logo/watikah PN dengan SPR) — jentera pecah",
                "Bukan senama: dua 'blok' bertembung → pengundi keliru, undi pecah",
                "PAS suruh penyokong undi BN di kerusi PN tak tanding — tolong parti lawan sendiri",
            ],
            "takeaway": (
                "Masalah teknikal logo/watikah + pecah undi dalaman lebih merosakkan "
                "daripada isu 'simbol PN' di mata Cina/India."
            ),
        },
        "n9_recommendation": {
            "do": [
                "PAS guna logo bulan sendiri — elak isu SPR/pertikaian tandatangan seperti Johor",
                "WAJIB runding & bahagi kerusi dengan Bersatu, Wawasan, Berjasa sebelum 18 Julai",
                "Jangan lawan sesama sendiri di kerusi yang sama",
                "Di kerusi PAS tak tanding: sokong calon sekutu (bukan BN)",
            ],
            "dont": [
                "Solo penuh tanpa seat-sharing (ulang Johor)",
                "Suruh penyokong undi BN sebagai 'jalan singkat'",
                "Biarkan dua calon 'blok pembangkang' bertembung di DUN sama",
            ],
            "why_own_logo_ok": [
                "Elak terus isu SPR / watikah seperti Johor",
                "Cina & India tak fokus simbol logo — mereka risau kenyataan/rhetorik PAS",
                "Logo bulan dikenali jelas oleh pengundi tradisional PAS",
            ],
        },
        "cina_india_grounding": {
            "data_label": f"{filtered:,} posts N9 · ~{eng} engagement · {date_range}",
            "chinese": {
                "posts": ch_posts,
                "neg_pct": ch_neg,
                "boycott_risk": boycott,
                "top_issue": f"{ch_top[0]} ({ch_top[1]}%)",
                "insight": (
                    "Komuniti Cina N9 fokus kos hidup, SME & perkhidmatan PBT — bukan logo parti. "
                    f"Negatif {ch_neg}% · risiko soft abstention di Seremban/Nilai/Lobak jika rhetorik "
                    "agama/perkauman diulang (senjata DAP seperti di Johor)."
                ),
            },
            "indian": {
                "posts": ind_posts,
                "top_issue": f"{ind_top[0]} ({ind_top[1]}%)",
                "insight": (
                    "Komuniti India N9 pragmatik: SJKT, pekerjaan, prestasi parti. "
                    "Faktor PAS muncul dalam corpus tetapi respons terbaik = perkhidmatan, bukan teologi."
                ),
            },
            "messaging_rule": (
                "Simbol (bulan vs telefon vs PN) hampir tidak material kepada Cina/India. "
                "Yang merosakkan = kenyataan awam yang boleh diframing sebagai takutkan minoriti."
            ),
        },
        "seat_focus": {
            "priority": "Kerusi majoriti tipis + kerusi UMNO (realistik tambah kerusi)",
            "avoid": "Jangan utamakan pecah kubu kuat DAP sebagai strategi utama",
            "mn20_note": "Selaras War Room: 20 kerusi sasaran MN — push ABC, maintain D",
        },
        "ops_now": [
            "Pantau status rundingan seat-sharing harian hingga 18 Julai",
            "Siapkan mesej rasmi jentera: kekal dalam blok pembangkang / sekutu — BUKAN undi BN",
            f"Track sentimen Cina/India harian (kini ~{filtered} posts, ~{eng} engagement)",
            "Jaga kenyataan awam — elak rhetorik perkauman/agama yang jadi senjata DAP",
            "Arahan undi bertulis untuk setiap DUN: siapa calon kita / siapa sekutu / siapa lawan",
        ],
        "warroom_signal": {
            "mn_vs_solo_pct": mn_vs_solo,
            "headline": keputusan.get("headline"),
            "ringkasan": keputusan.get("ringkasan"),
        },
        "sources": [
            "Ulasan strategi pasca-PRN Johor (PAS 0/11, PN 0/56) — Jul 2026",
            "Crawl naratif Cina & India N9 (analyze_naratif_agentic)",
            "War Room n9_daily_ops.json (MN vs Solo)",
            "Sidang Media Presiden PAS N9 (YouTube 0qSESgWMoG8, 12 Jul 2026) — statement only",
        ],
    }


def _render_official_banner(ob: Dict[str, Any] | None) -> str:
    if not ob:
        return ""
    pts = "".join(f"<li>{x}</li>" for x in (ob.get("key_points") or [])[:8])
    match = "".join(f"<li>{x}</li>" for x in (ob.get("match") or []))
    tension = "".join(f"<li>{x}</li>" for x in (ob.get("tension") or []))
    url = ob.get("url") or "#"
    return f"""
  <div class="panel" style="margin-bottom:16px;border-color:rgba(56,189,248,.45)">
    <div class="head n"><h2>0. Kenyataan rasmi — Sidang Media Presiden (12 Jul)</h2></div>
    <div style="padding:14px 16px">
      <p><strong>{ob.get('speaker','')}</strong> ·
        <a href="{url}" target="_blank" rel="noopener">{ob.get('title','')}</a></p>
      <p class="data-meta" style="margin:8px 0">
        Status: <strong style="color:var(--amber)">{ob.get('status','')}</strong> ·
        {ob.get('views','—')} views · {ob.get('likes','—')} likes · {ob.get('comments','—')} comments ·
        Follow-up: {ob.get('followup_due','—')}
      </p>
      <p style="font-size:0.82rem;color:var(--muted);margin:0 0 10px">{ob.get('engagement_note','')}
        · {ob.get('transcript_quality','')}</p>
      <h4>Poin utama (auto-caption — sahkan sebelum quote)</h4>
      <ul>{pts}</ul>
      <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">
        <div>
          <h4 style="color:var(--emerald)">Selaras Halatuju</h4>
          <ul>{match}</ul>
        </div>
        <div>
          <h4 style="color:var(--rose)">Tegangan / clarify HQ</h4>
          <ul>{tension}</ul>
        </div>
      </div>
      <p style="margin-top:12px;padding:10px;border-radius:8px;background:#0b1220;border:1px solid var(--border)">
        <strong>Cina/India:</strong> {ob.get('cina_india_now','')}
        <br/><span style="color:var(--amber)">{ob.get('cina_india_risk','')}</span>
      </p>
    </div>
  </div>
"""


def render_halatuju_tab(h: Dict[str, Any]) -> str:
    johor = h.get("johor_lesson") or {}
    rec = h.get("n9_recommendation") or {}
    ci = h.get("cina_india_grounding") or {}
    ch, ind = ci.get("chinese") or {}, ci.get("indian") or {}
    seat = h.get("seat_focus") or {}
    wr = h.get("warroom_signal") or {}
    punca = "".join(f"<li>{x}</li>" for x in johor.get("punca", []))
    do = "".join(f"<li>{x}</li>" for x in rec.get("do", []))
    dont = "".join(f"<li>{x}</li>" for x in rec.get("dont", []))
    why = "".join(f"<li>{x}</li>" for x in rec.get("why_own_logo_ok", []))
    ops = "".join(f"<li>{x}</li>" for x in h.get("ops_now", []))
    src = "".join(f"<li>{x}</li>" for x in h.get("sources", []))
    official_html = _render_official_banner(h.get("official_statement"))
    wr_box = ""
    if wr.get("mn_vs_solo_pct") is not None:
        wr_box = (
            f'<div class="kpi"><label>War Room · MN vs Solo</label>'
            f'<strong>{wr.get("mn_vs_solo_pct")}%</strong>'
            f'<span style="font-size:0.72rem;color:var(--muted);display:block;margin-top:4px">'
            f'{wr.get("headline") or ""}</span></div>'
        )
    return f"""
<div id="tab-halatuju" class="tab-panel hidden">
  <div class="ai-box" style="border-color:rgba(251,191,36,.4);background:rgba(251,191,36,.08)">
    <h2 style="color:var(--amber)">Halatuju Strategi N9 — Logo PAS + Seat-Sharing</h2>
    <p><strong>Verdict:</strong> <span style="color:var(--amber)">{h.get('verdict')}</span> —
    {h.get('formula')}</p>
    <p style="margin-top:8px"><strong>Deadline genting:</strong>
      <span style="color:var(--rose)">{h.get('deadline_label')}</span>
      — rundingan seat-sharing WAJIB selesai sebelum penamaan calon.
    </p>
  </div>
{official_html}

  <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr);margin-bottom:16px">
    <div class="kpi"><label>Crawl N9 (tapis)</label><strong>{(ci.get('data_label') or '—').split('·')[0].strip()}</strong></div>
    <div class="kpi"><label>Cina · negatif</label><strong>{ch.get('neg_pct',0)}%</strong>
      <span style="font-size:0.72rem;color:var(--muted);display:block">{ch.get('posts',0)} posts · boikot {ch.get('boycott_risk','?')}</span></div>
    <div class="kpi"><label>India · posts</label><strong>{ind.get('posts',0)}</strong>
      <span style="font-size:0.72rem;color:var(--muted);display:block">Top: {ind.get('top_issue','—')}</span></div>
    {wr_box}
  </div>

  <div class="grid" style="grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
    <div class="panel">
      <div class="head n"><h2>1. Lesson Johor — jangan ulang</h2></div>
      <div style="padding:14px 16px">
        <p><strong>{johor.get('headline','')}</strong></p>
        <h4>Punca sebenar (bukan semata undi Melayu)</h4>
        <ul>{punca}</ul>
        <p class="assess" style="margin-top:10px;color:var(--amber)">{johor.get('takeaway','')}</p>
      </div>
    </div>
    <div class="panel">
      <div class="head n"><h2>2. Cadangan N9 — BUKAN solo</h2></div>
      <div style="padding:14px 16px">
        <h4>Buat</h4><ul class="actions">{do}</ul>
        <h4>Jangan</h4><ul style="color:var(--rose)">{dont}</ul>
        <h4>Kenapa logo bulan sendiri OK</h4><ul>{why}</ul>
      </div>
    </div>
  </div>

  <div class="panel" style="margin-bottom:16px">
    <div class="head n"><h2>3. Implikasi Cina &amp; India (data crawl)</h2></div>
    <div style="padding:14px 16px">
      <p class="data-meta" style="margin:0 0 12px">{ci.get('data_label','')}</p>
      <div class="comm-grid">
        <div class="comm ch">
          <h3>Cina N9</h3>
          <p class="assess">Isu #1: <strong>{ch.get('top_issue','—')}</strong></p>
          <p>{ch.get('insight','')}</p>
        </div>
        <div class="comm in">
          <h3>India N9</h3>
          <p class="assess">Isu #1: <strong>{ind.get('top_issue','—')}</strong></p>
          <p>{ind.get('insight','')}</p>
        </div>
      </div>
      <p style="margin-top:14px;padding:12px;border-radius:8px;background:#0b1220;border:1px solid var(--border)">
        <strong>Peraturan mesej:</strong> {ci.get('messaging_rule','')}
      </p>
    </div>
  </div>

  <div class="grid" style="grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
    <div class="panel">
      <div class="head n"><h2>4. Fokus kerusi</h2></div>
      <div style="padding:14px 16px">
        <p><strong>Utama:</strong> {seat.get('priority','')}</p>
        <p style="color:var(--rose);margin-top:8px"><strong>Elak:</strong> {seat.get('avoid','')}</p>
        <p class="muted" style="margin-top:8px">{seat.get('mn20_note','')}</p>
      </div>
    </div>
    <div class="panel">
      <div class="head n"><h2>5. Apa kita buat sekarang</h2></div>
      <div style="padding:14px 16px">
        <ul class="actions">{ops}</ul>
      </div>
    </div>
  </div>

  <div class="panel">
    <div class="head n"><h2>Sumber &amp; asas</h2></div>
    <div style="padding:14px 16px">
      <ul class="muted">{src}</ul>
      <p class="muted" style="margin-top:10px;font-size:0.78rem">
        Nota: Cadangan operasi berasaskan data crawl + lesson Johor — bukan polling SPR.
        {(' War Room: ' + str(wr.get('ringkasan'))) if wr.get('ringkasan') else ''}
      </p>
    </div>
  </div>
</div>
"""
