#!/usr/bin/env python3
"""
RAG + Agentic LLM analysis for Negeri Sembilan (N9) Chinese & Indian narrative.
Filters noise → retrieves top evidence → Claude/OpenAI strategic brief for PAS/PN/MN.

Outputs:
  data/projects/political/PRN/reports/naratif_cina_india/naratif_agentic_brief.json
  data/projects/political/PRN/reports/naratif_cina_india/naratif_cadangan_tindakan.json
  data/projects/political/PRN/reports/naratif_cina_india/naratif_cina_india_johor_n9_dashboard.html
  data/projects/political/PRN/reports/naratif_cina_india/naratif_cadangan_tindakan_n9.docx
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "n9_chinese_narrative_dashboard"
CSV = DASH / "data/prn_chinese_narrative_posts_3negeri.csv"
RAG_CORPUS = ROOT / "data/projects/political/PRN/PRN_N9/reference/n9_pn_faction_rag.json"
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
OUT_BRIEF = OUT_DIR / "naratif_agentic_brief.json"
OUT_HTML = OUT_DIR / "naratif_cina_india_johor_n9_dashboard.html"
OUT_JSON = OUT_DIR / "naratif_cina_india_johor_n9_analytics.json"
OUT_ACTION_PLAN = OUT_DIR / "naratif_cadangan_tindakan.json"
MYT = timezone(timedelta(hours=8))

# Anthropic pinned IDs retire often — try current aliases first (Jul 2026).
ANTHROPIC_MODEL_FALLBACKS = (
    "claude-sonnet-4-6",
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
)

if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _load_df(rebuild: bool) -> pd.DataFrame:
    if rebuild or not CSV.exists():
        from utils.build_dataset import build_dataset  # noqa: WPS433
        return build_dataset()
    return pd.read_csv(CSV, low_memory=False)


def _is_chinese(row: pd.Series) -> bool:
    from utils.community import infer_community  # noqa: WPS433
    if str(row.get("crawl_community") or "").lower() == "india":
        return False
    if infer_community(row) == "indian":
        return False
    if infer_community(row) == "chinese":
        return True
    if str(row.get("language_detected") or "").startswith("zh"):
        return True
    if re.search(r"[\u4e00-\u9fff]", str(row.get("post_text") or "")):
        return True
    return False


def _is_indian(row: pd.Series) -> bool:
    return str(row.get("crawl_community") or "").lower() == "india"


def _neg_pct(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    return int(round((df["sentiment"].astype(str).str.lower() == "negative").mean() * 100))


def _top_issues(df: pd.DataFrame, n: int = 5, community: str = "chinese") -> List[List[Any]]:
    from utils.keyword_classifier import classify_issue_community  # noqa: WPS433
    c: Counter[str] = Counter()
    for _, row in df.iterrows():
        c[classify_issue_community(str(row.get("post_text") or ""), row.get("issue_cluster"), community)] += 1
    total = sum(c.values()) or 1
    return [[k, int(round(v / total * 100))] for k, v in c.most_common(n)]


def _engagement_total(df: pd.DataFrame) -> int:
    if df.empty or "engagement_total" not in df.columns:
        return 0
    return int(df["engagement_total"].fillna(0).sum())


def _date_range_label(df: pd.DataFrame) -> str:
    for col in ("published_at", "post_date", "crawl_date"):
        if col not in df.columns:
            continue
        ser = pd.to_datetime(df[col], errors="coerce").dropna()
        if ser.empty:
            continue
        months = ("", "Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogos", "Sep", "Okt", "Nov", "Dis")
        d0, d1 = ser.min(), ser.max()
        return f"{d0.day} {months[d0.month]} – {d1.day} {months[d1.month]} {d1.year}"
    return "—"


def _rag_context() -> str:
    chunks: List[str] = []
    if RAG_CORPUS.exists():
        rag = json.loads(RAG_CORPUS.read_text(encoding="utf-8"))
        chunks.append("=== RAG: N9 PN Faction Map ===")
        chunks.append(json.dumps(rag.get("blocs", {}), ensure_ascii=False)[:2500])
    guide = ROOT / "data/projects/political/Cina_Narative_2026/CRAWL_4_JOHOR_CN_FB.txt"
    if guide.exists():
        chunks.append("=== RAG: Johor Cina Campaign Guide (excerpt) ===")
        chunks.append(guide.read_text(encoding="utf-8")[:2000])
    return "\n".join(chunks)


def _evidence_pack(df: pd.DataFrame, state: str, comm: str, n: int = 12) -> List[Dict[str, str]]:
    from utils.translator import has_chinese, lookup_static_bm, resolve_bm_translation  # noqa: WPS433

    sub = df[df["state"] == state]
    sub = sub[sub.apply(_is_chinese if comm == "chinese" else _is_indian, axis=1)]
    if sub.empty:
        return []
    work = sub.sort_values("engagement_total", ascending=False) if "engagement_total" in sub.columns else sub
    out: List[Dict[str, str]] = []
    for _, row in work.head(n).iterrows():
        original = str(row.get("post_text") or "").strip()[:320]
        bm = lookup_static_bm(original) or resolve_bm_translation(row, auto_translate=True).strip()
        if bm == original and original and not has_chinese(original):
            from utils.translator import translate_text  # noqa: WPS433
            bm = translate_text(original, target="ms").strip() or original
        # Elak papar mesej ralat terjemahan sebagai teks utama
        if bm.startswith("(Terjemahan gagal") or bm.startswith("(Terjemahan belum"):
            bm = lookup_static_bm(original) or original
        if bm and original and bm in original:
            display_bm = bm
        elif bm and original and original in bm:
            display_bm = bm
        else:
            display_bm = bm or original
        out.append({
            "text_original": original,
            "text_bm": display_bm,
            "text": display_bm,
            "sentiment": str(row.get("sentiment") or "neutral"),
            "issue": str(row.get("issue_cluster") or ""),
            "platform": str(row.get("platform") or ""),
            "location": str(row.get("constituency") or row.get("district") or state),
            "has_chinese": str(has_chinese(original)),
        })
    return out


def _stats_bundle(df: pd.DataFrame, state: str) -> Dict[str, Any]:
    sub = df[df["state"] == state]
    ch = sub[sub.apply(_is_chinese, axis=1)]
    ind = sub[sub.apply(_is_indian, axis=1)]
    return {
        "chinese": {"posts": len(ch), "neg_pct": _neg_pct(ch), "issues": _top_issues(ch, community="chinese"), "evidence": _evidence_pack(df, state, "chinese")},
        "indian": {"posts": len(ind), "neg_pct": _neg_pct(ind), "issues": _top_issues(ind, community="indian"), "evidence": _evidence_pack(df, state, "indian")},
    }


def _llm_brief(
    stats: Dict[str, Any],
    filtered_total: int,
    raw_total: int,
    *,
    project_id: str = "PRN_N9",
    llm_provider: Optional[str] = None,
) -> Dict[str, Any]:
    _load_env()
    n9 = stats.get("N9", {})
    prompt = f"""Anda pakar strategi kempen PRN Malaysia untuk koalisi PAS + PN + Muafakat Nasional (MN).

TUGAS: Analisis naratif komuniti Cina & India Negeri Sembilan (N9) SAHAJA. Jangan sebut Johor.

STATISTIK (selepas tapis {filtered_total} dari {raw_total} rows):
N9 Cina: {n9.get('chinese', {})}
N9 India: {n9.get('indian', {})}

EVIDENCE N9 CINA:
{json.dumps((n9.get('chinese') or {}).get('evidence', [])[:10], ensure_ascii=False)}

EVIDENCE N9 INDIA:
{json.dumps((n9.get('indian') or {}).get('evidence', [])[:8], ensure_ascii=False)}

RAG CONTEXT:
{_rag_context()}

Jawab JSON SAHAJA (tiada markdown):
{{
  "executive_summary_ms": "3-4 ayat ringkas fokus Negeri Sembilan sahaja",
  "n9": {{
    "chinese": {{"support_ph_assessment": "...", "boycott_risk": "low|medium|high", "pas_pn_mn_perception": "...", "playable_narratives": ["..."], "actions_p1": ["..."], "actions_p2": ["..."]}},
    "indian": {{"support_ph_assessment": "...", "boycott_risk": "low|medium|high", "pas_pn_mn_perception": "...", "playable_narratives": ["..."], "actions_p1": ["..."], "actions_p2": ["..."]}}
  }},
  "coalition_priorities": ["5 keutamaan PAS/PN/MN minggu ini untuk N9"],
  "do_not_do": ["3 kesilapan messaging N9"],
  "confidence": "low|medium|high"
}}

Fokus: tindakan konkrit N9 (Seremban, Nilai, Port Dickson, Jelebu, Bahau)."""

    try:
        from backend.nim_client import (  # noqa: WPS433
            PROVIDER_RULE_ONLY,
            generate_json,
            get_llm_client,
            get_provider_for_project,
            provider_failover_order,
        )

        primary = get_provider_for_project(project_id=project_id, explicit_provider=llm_provider)
        for provider in provider_failover_order(primary):
            if provider == PROVIDER_RULE_ONLY:
                break
            try:
                client, model, normalized_provider = get_llm_client(provider)
                parsed = generate_json(
                    client=client,
                    model=model,
                    provider=normalized_provider,
                    prompt=prompt,
                    system=(
                        "Anda pakar strategi kempen PRN Malaysia. "
                        "Jawab ONLY valid JSON. Tiada prose, tiada markdown fences."
                    ),
                    required_keys=(
                        "executive_summary_ms",
                        "n9",
                        "coalition_priorities",
                        "do_not_do",
                        "confidence",
                    ),
                    cache_path=OUT_DIR / "cache" / f"naratif_agentic_brief_{project_id}.last_good.json",
                    max_retries=2,
                    temperature=0.3,
                    max_tokens=4000,
                )
                print(f"   LLM OK: {normalized_provider} · {model}")
                return parsed
            except Exception as e:
                print(f"⚠️ LLM failed ({provider}): {e}")
    except Exception as e:
        print(f"⚠️ NIM/OpenAI-compatible route unavailable: {e}")

    # Legacy fallback path kept for operators who still have Anthropic configured.
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        models = [os.getenv("ANTHROPIC_MODEL")] if os.getenv("ANTHROPIC_MODEL") else []
        models.extend(m for m in ANTHROPIC_MODEL_FALLBACKS if m not in models)
        last_err: Optional[Exception] = None
        for model in models:
            try:
                msg = client.messages.create(
                    model=model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = msg.content[0].text
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    parsed = json.loads(m.group())
                    parsed["llm_provider"] = "anthropic"
                    parsed["llm_model"] = model
                    print(f"   Anthropic OK: {model}")
                    return parsed
            except Exception as e:
                last_err = e
                if "404" in str(e) or "not_found" in str(e):
                    continue
                print(f"⚠️ Anthropic failed ({model}): {e}")
                break
        if last_err:
            print(f"⚠️ Anthropic failed (all models): {last_err}")

    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            parsed = json.loads(resp.choices[0].message.content or "{}")
            parsed["llm_provider"] = "openai"
            parsed["llm_model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            print(f"   OpenAI OK: {parsed['llm_model']}")
            return parsed
        except Exception as e:
            print(f"⚠️ OpenAI failed: {e}")

    return _rule_brief(stats)


def _rule_brief(stats: Dict[str, Any]) -> Dict[str, Any]:
    n9 = stats.get("N9", {})
    ch, ind = n9.get("chinese", {}), n9.get("indian", {})
    ch_neg = ch.get("neg_pct", 0)
    n_top = (ch.get("issues") or [["—", 0]])[0]
    return {
        "executive_summary_ms": (
            f"Negeri Sembilan: komuniti Cina menekankan {n_top[0]} ({n_top[1]}%), SME dan perkhidmatan PBT "
            f"({ch_neg}% negatif) — risiko soft abstention di kerusi bandar (Seremban, Nilai, Lobak). "
            f"Komuniti India ({ind.get('posts', 0)} posts) fokus SJKT, pekerjaan dan isu parti; "
            f"sokongan PH pragmatik jika perkhidmatan disampaikan. "
            f"Prioriti PAS/PN/MN: fakta bantuan + lawatan ground N9, elak retorik agama."
        ),
        "n9": {
            "chinese": {
                "support_ph_assessment": "PH base kuat tapi kos hidup erode trust",
                "boycott_risk": "medium" if ch_neg >= 30 else "low",
                "pas_pn_mn_perception": "PAS factor dipantau — fokus perkhidmatan, bukan teologi",
                "playable_narratives": [
                    "Perkhidmatan tempatan Seremban (trafik & parkir)",
                    "SME Jelebu/Nilai — bantuan kos operasi",
                    "Kestabilan negeri — elak pecah undi",
                ],
                "actions_p1": [
                    "Respons aduan kos hidup/SME dengan data exco N9 (BM+中文)",
                    "Ground team Seremban/Nilai — dialog peniaga Cina",
                ],
                "actions_p2": ["Lawatan DUN bandar Cina N10/N11/N12/N28"],
            },
            "indian": {
                "support_ph_assessment": "SJKT & pekerjaan — PH deliver = kekal",
                "boycott_risk": "low",
                "pas_pn_mn_perception": "Neutral — fokus perkhidmatan",
                "playable_narratives": ["SJKT guru kekurangan", "Port Dickson pekerjaan"],
                "actions_p1": ["Koordinasi pendidikan SJKT — BM+Tamil update"],
                "actions_p2": ["Pantau PN strategy mentions — counter pecah undi"],
            },
        },
        "coalition_priorities": [
            "N9: counter kos hidup Cina dengan fakta bantuan negeri",
            "Seremban/Nilai: perkhidmatan PBT (trafik, parkir) — 48 jam response",
            "India N9: SJKT + pekerjaan — bukan agama",
            "Elak ulang retorik syurga/Harakat di N9",
            "Muafakat 1-vs-1 kerusi Melayu sasaran MN",
        ],
        "do_not_do": [
            "Debat agama/syurga dengan komuniti Cina N9",
            "Abaikan isu tempat letak kereta & trafik Seremban",
            "Fokus berlebihan pada isu agama di kerusi India N9",
        ],
        "confidence": "medium",
        "llm_provider": "rule_based_fallback",
    }


def _format_sample_li(s: Dict[str, str]) -> str:
    """Dashboard sample: BM first, original (ZH/EN) as secondary line."""
    sent = s.get("sent", s.get("sentiment", "?"))
    meta = s.get("meta", "")
    bm = str(s.get("text_bm") or s.get("text") or "").strip()
    orig = str(s.get("text_original") or "").strip()
    if orig and bm and orig != bm and orig not in bm:
        body = f"<strong>{bm}</strong><br/><span class='orig'>Asal: {orig}</span>"
    else:
        body = f"<strong>{bm or orig}</strong>"
    return (
        f"<li><span class='tag {sent}'>{sent}</span>{body}"
        f"<br/><small>{meta}</small></li>"
    )


def _render_action_card(act: Dict[str, Any]) -> str:
    pri = act.get("priority", "")
    pri_cls = "p1" if "P1" in pri else "p2"
    duns = ", ".join(act.get("duns", []))
    how = "".join(f"<li>{s}</li>" for s in act.get("how_steps", []))
    msg = act.get("message", {})
    msg_html = ""
    if msg.get("bm"):
        msg_html += f"<p><span class='lbl'>BM</span>{msg['bm']}</p>"
    if msg.get("zh"):
        msg_html += f"<p><span class='lbl zh'>中文</span>{msg['zh']}</p>"
    if msg.get("ta"):
        msg_html += f"<p><span class='lbl ta'>தமிழ்</span>{msg['ta']}</p>"
    return f"""
    <div class="action-card {pri_cls}">
      <div class="action-head">
        <span class="pri-tag {pri_cls}">{pri}</span>
        <h3>{act.get('title','')}</h3>
        <span class="act-meta">{act.get('id','')} · {act.get('community','').upper()} · {act.get('issue','')}</span>
      </div>
      <div class="action-body">
        <div class="action-col">
          <h5>Apa yang perlu dilakukan</h5>
          <p>{act.get('what','')}</p>
          <h5>Mengapa penting (intel crawl)</h5>
          <p class="why">{act.get('why','')}</p>
          <h5>Bagaimana — langkah operasi</h5>
          <ol class="how">{how}</ol>
        </div>
        <div class="action-col">
          <h5>Mesej yang hendak disampaikan</h5>
          <div class="msg-box">{msg_html or '<p class="muted">—</p>'}</div>
          <div class="act-footer">
            <p><strong>Saluran:</strong> {act.get('channel','—')}</p>
            <p><strong>Pemilik:</strong> {act.get('owner','—')}</p>
            <p><strong>Tarikh akhir:</strong> {act.get('deadline','—')}</p>
            <p><strong>DUN sasaran:</strong> {duns}</p>
            <p><strong>KPI:</strong> {act.get('kpi','—')}</p>
          </div>
        </div>
      </div>
    </div>"""


def _render_dun_table(rows: List[Dict[str, str]], state_label: str) -> str:
    if not rows:
        return "<p class='muted'>Tiada data DUN</p>"
    body = ""
    for r in rows:
        body += f"""<tr>
          <td><strong>{r['dun_code']}</strong></td>
          <td>{r['dun_name']}</td>
          <td><span class="pri-sm {r['priority'].lower()}">{r['priority']}</span></td>
          <td>{r['primary_issue']}</td>
          <td class="act-cell">{r['chinese_action']}</td>
          <td class="act-cell">{r['indian_action']}</td>
        </tr>"""
    return f"""
    <div class="dun-wrap">
      <h3>Jadual Cadangan Semua DUN — {state_label}</h3>
      <p class="dun-note">Checklist operasi calon & ground team. Setiap DUN ada cadangan minimum Cina + India.</p>
      <div class="dun-scroll">
        <table class="dun-table">
          <thead><tr>
            <th>DUN</th><th>Nama</th><th>Pri</th><th>Isu</th><th>Tindakan Cina</th><th>Tindakan India</th>
          </tr></thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </div>"""


def _render_actions_tab(plan: Dict[str, Any]) -> str:
    rules = "".join(f"<li>{r}</li>" for r in plan.get("tone_rules", []))
    dont = "".join(f"<li>{d}</li>" for d in plan.get("do_not_do", []))
    pri = "".join(f"<li>{p}</li>" for p in plan.get("coalition_priorities", []))

    n9_cards = "".join(_render_action_card(a) for a in plan.get("n9", {}).get("priority_actions", []))
    n9_dun = _render_dun_table(plan.get("n9", {}).get("dun_matrix", []), "Negeri Sembilan · 36 DUN")

    return f"""
    <div id="tab-actions" class="tab-panel hidden">
      <div class="ai-box action-intro">
        <h2>📋 Cadangan Tindakan Operasi — Negeri Sembilan</h2>
        <p>{plan.get('purpose','')}</p>
        <p class="doc-links">
          📄 DOCX N9: <code>naratif_cadangan_tindakan_n9.docx</code>
        </p>
      </div>

      <div class="rules-grid">
        <div class="rules-panel"><h4>Peraturan nada (WAJIB)</h4><ul>{rules}</ul></div>
        <div class="rules-panel"><h4>Keutamaan koalisi</h4><ul class="green">{pri}</ul></div>
        <div class="rules-panel warn-panel"><h4>Jangan buat</h4><ul class="red">{dont}</ul></div>
      </div>

      <div class="state-actions">
        <div class="state-block n">
          <h2>Negeri Sembilan · Tindakan Keutamaan</h2>
          <p class="stats-note">{plan.get('n9',{}).get('stats_note','')}</p>
          {n9_cards or '<p class="muted">—</p>'}
          {n9_dun}
        </div>
      </div>
    </div>"""


# 20 kerusi sasaran MN — War Room + kawasan keutamaan (Nilai, Seremban, Jelebu, Bahau)
N9_TARGET_DUNS: List[tuple[str, str]] = [
    ("N10", "Nilai"),
    ("N28", "Seremban Kota"),
    ("N08", "Bahau"),
    ("N13", "Sikamat"),       # Jelebu
    ("N06", "Palong"),
    ("N02", "Pertang"),
    ("N03", "Sungai Lui"),
    ("N05", "Serting"),
    ("N07", "Jeram Padang"),
    ("N09", "Lenggeng"),
    ("N14", "Ampangan"),
    ("N15", "Juasseh"),
    ("N16", "Seri Menanti"),
    ("N17", "Senaling"),
    ("N19", "Johol"),
    ("N20", "Labu"),
    ("N25", "Paroi"),
    ("N27", "Rantau"),
    ("N31", "Port Dickson"),
    ("N35", "Gemencheh"),
]

# Kata kunci tambahan per DUN (kawasan)
N9_DUN_EXTRA_KW: Dict[str, List[str]] = {
    "N10": ["汝来", "bandar baru nilai"],
    "N28": ["seremban", "芙蓉", "森美兰"],
    "N13": ["jelebu", "日叻务"],
    "N08": ["马口"],
    "N31": ["波德申", "lukut", "芦骨"],
    "N25": ["senawang"],
}


N9_DUN_CONSTITUENCY_ALIASES: Dict[str, List[str]] = {
    "N10": ["nilai"],
    "N28": ["seremban kota", "kota", "rasah"],
    "N08": ["bahau"],
    "N13": ["sikamat", "jelebu"],
    "N25": ["paroi", "senawang"],
    "N31": ["bagan pinang", "port dickson", "lukut", "teluk kemang"],
    "N06": ["palong"],
    "N09": ["lenggeng"],
    "N14": ["ampangan"],
    "N27": ["rantau"],
    "N35": ["gemencheh"],
}


def _row_matches_target_dun(row: pd.Series, code: str, name: str, kws: List[str]) -> bool:
    from dun_seat_keywords import row_matches_seat  # noqa: WPS433

    cols = ("constituency", "district", "location_tag")
    blob = " ".join(str(row.get(c) or "") for c in cols).lower()
    for alias in N9_DUN_CONSTITUENCY_ALIASES.get(code, [name.lower()]):
        if alias in blob:
            return True

    text = " ".join(str(row.get(c) or "") for c in ("post_text",) + cols)
    if row_matches_seat(text, code, kws, "N9"):
        return True
    # Cina: 汝来 = Nilai, 马口 = Bahau, 芙蓉 = Seremban
    zh_map = {"N10": "汝来", "N08": "马口", "N28": "芙蓉", "N13": "日叻务"}
    zh = zh_map.get(code, "")
    if zh and zh in str(row.get("post_text") or ""):
        return True
    return False


def _strip_dun_prefix(text: str) -> str:
    return re.sub(r"^\[N\d+\s+[^\]]+\]\s*", "", str(text or "")).strip()


def _n9_ground_plan_lookup() -> Dict[str, Dict[str, str]]:
    from naratif_action_plan_builder import (  # noqa: WPS433
        N9_CHINESE_MIXED,
        N9_CHINESE_URBAN,
        _build_dun_matrix,
    )
    lookup: Dict[str, Dict[str, str]] = {}
    for row in _build_dun_matrix("Negeri Sembilan"):
        code = row["dun_code"]
        if code in N9_CHINESE_URBAN:
            fokus = "Bandar Cina — counter abstention"
        elif code in N9_CHINESE_MIXED:
            fokus = "Campuran — lawatan peniaga + data exco"
        else:
            fokus = "Melayu majoriti — ground utama; Cina sentuhan minimum"
        lookup[code] = {
            "priority": row.get("priority", "P2"),
            "primary_issue": row.get("primary_issue", ""),
            "chinese_action": _strip_dun_prefix(row.get("chinese_action", "")),
            "indian_action": _strip_dun_prefix(row.get("indian_action", "")),
            "ground_fokus": fokus,
        }
    return lookup


def _source_badge(status: str) -> tuple[str, str]:
    if status == "ok":
        return "crawl_tpl", "CRAWL + TEMPLATE"
    if status == "thin":
        return "thin", "NIPIS + TEMPLATE"
    return "tpl", "TEMPLATE"


def _build_n9_target_duns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    from dun_seat_keywords import N9_SEAT_KEYWORDS  # noqa: WPS433
    from utils.keyword_classifier import classify_issue_community  # noqa: WPS433

    ground = _n9_ground_plan_lookup()
    sub = df[df["state"] == "Negeri Sembilan"] if "state" in df.columns else pd.DataFrame()
    rows_out: List[Dict[str, Any]] = []

    for code, name in N9_TARGET_DUNS:
        kws = list(N9_SEAT_KEYWORDS.get(code, [name.lower()]))
        kws.extend(N9_DUN_EXTRA_KW.get(code, []))

        matched_idx = []
        for idx, row in sub.iterrows():
            if _row_matches_target_dun(row, code, name, kws):
                matched_idx.append(idx)

        dun_df = sub.loc[matched_idx] if matched_idx else pd.DataFrame()
        ch = dun_df[dun_df.apply(_is_chinese, axis=1)] if not dun_df.empty else pd.DataFrame()
        ind = dun_df[dun_df.apply(_is_indian, axis=1)] if not dun_df.empty else pd.DataFrame()

        top_issue = "—"
        if not ch.empty:
            from collections import Counter
            ic: Counter[str] = Counter()
            for _, r in ch.iterrows():
                ic[classify_issue_community(str(r.get("post_text") or ""), r.get("issue_cluster"), "chinese")] += 1
            top_issue = _issue_label(ic.most_common(1)[0][0]) if ic else "—"

        sample = ""
        if not ch.empty:
            srow = ch.iloc[0]
            sample = str(srow.get("post_text") or "")[:120]
        elif not ind.empty:
            sample = str(ind.iloc[0].get("post_text") or "")[:120]

        st = "ok" if len(ch) >= 3 else ("thin" if len(ch) else "kosong")
        src_cls, src_lbl = _source_badge(st)
        plan = ground.get(code, {})
        rows_out.append({
            "code": code,
            "name": name,
            "posts_total": len(dun_df),
            "posts_chinese": len(ch),
            "posts_indian": len(ind),
            "neg_pct_chinese": _neg_pct(ch),
            "top_issue_chinese": top_issue,
            "sample": sample,
            "status": st,
            "priority": plan.get("priority", "P2"),
            "primary_issue": plan.get("primary_issue", "Outreach minoriti"),
            "ground_fokus": plan.get("ground_fokus", ""),
            "chinese_action": plan.get("chinese_action", ""),
            "indian_action": plan.get("indian_action", ""),
            "source_cls": src_cls,
            "source_label": src_lbl,
        })
    return rows_out


def _render_n9_targets_section(targets: List[Dict[str, Any]]) -> str:
    if not targets:
        return ""
    body = ""
    for r in targets:
        st = r.get("status", "kosong")
        st_cls = "p1" if st == "kosong" else ("p2" if st == "thin" else "ok")
        st_lbl = {"ok": "OK", "thin": "Nipis", "kosong": "Kosong"}.get(st, st)
        pri = r.get("priority", "P2")
        pri_cls = "p1" if pri == "P1" else "p2"
        src_cls = r.get("source_cls", "tpl")
        src_lbl = r.get("source_label", "TEMPLATE")
        intel_issue = r.get("top_issue_chinese") or "—"
        intel_sample = r.get("sample") or "—"
        if st == "kosong":
            intel_issue = "<span class='muted-lbl'>Tiada crawl</span>"
            intel_sample = "<span class='muted-lbl'>—</span>"
        body += f"""<tr class="st-{st_cls}">
          <td><strong>{r['code']}</strong><br/><span class="pri-sm {pri_cls}">{pri}</span></td>
          <td>{r['name']}</td>
          <td><span class="pri-sm {st_cls}">{st_lbl}</span><br/><span class="src-badge {src_cls}">{src_lbl}</span></td>
          <td>{r['posts_chinese']}</td>
          <td>{r['posts_indian']}</td>
          <td>{r['neg_pct_chinese'] if st != 'kosong' else '—'}{'' if st == 'kosong' else '%'}</td>
          <td class="intel-cell">{intel_issue}</td>
          <td class="fokus-cell"><strong>{r.get('ground_fokus') or '—'}</strong><br/><small>{r.get('primary_issue') or ''}</small></td>
          <td class="act-cell act-ch">🇨🇳 {r.get('chinese_action') or '—'}</td>
          <td class="act-cell act-in">🇮🇳 {r.get('indian_action') or '—'}</td>
          <td class="intel-cell sample-cell">{intel_sample}</td>
        </tr>"""
    total_ch = sum(r["posts_chinese"] for r in targets)
    kosong_n = sum(1 for r in targets if r.get("status") == "kosong")
    return f"""
<div class="panel n9-targets">
  <div class="head n"><h2>🎯 N9 · 20 Kerusi Sasaran MN — Intel + Tindakan Ground</h2></div>
  <div class="targets-inner">
    <p class="dun-note">
      <strong>Intel (kiri):</strong> data crawl media/FB · <strong>Tindakan (kanan):</strong> checklist ground team — sentiasa ada walaupun kosong.<br/>
      <span class="src-badge crawl_tpl">CRAWL + TEMPLATE</span> = ada data + cadangan &nbsp;
      <span class="src-badge tpl">TEMPLATE</span> = tiada crawl, ikut cadangan operasi ({kosong_n} kerusi).<br/>
      Total Cina crawl: <strong>{total_ch} posts</strong> · Refresh crawl: <code>update_narrative.sh pagi</code>
    </p>
    <div class="dun-scroll">
      <table class="dun-table targets-table">
        <thead><tr>
          <th>DUN</th><th>Nama</th><th>Data</th><th>Cina</th><th>India</th><th>Neg%</th>
          <th>Isu crawl</th><th>Fokus operasi</th><th>Tindakan Cina</th><th>Tindakan India</th><th>Sample crawl</th>
        </tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  </div>
</div>"""


def _issue_label(name: str) -> str:
    """Label BM ringkas untuk bar isu — elak potong dalam panel sempit."""
    labels = {
        "Cost of Living": "Kos hidup",
        "SME and Business": "SME & perniagaan",
        "Local Government Services": "Perkhidmatan PBT",
        "Road and Traffic": "Jalan & trafik",
        "Chinese Education": "Pendidikan Cina",
        "Tamil Education": "Pendidikan Tamil (SJKT)",
        "Healthcare": "Kesihatan & hospital",
        "Water Supply": "Bekalan air",
        "DAP Performance": "Prestasi DAP",
        "MCA Relevance": "Relevan MCA",
        "Gerakan and PN": "Gerakan & PN",
        "PAS Factor": "Faktor PAS",
        "PH-BN Relationship": "Hubungan PH-BN",
        "Candidate Performance": "Prestasi calon",
        "Employment": "Pekerjaan",
        "Housing": "Perumahan",
        "Misinformation": "Maklumat palsu",
        "Race and Religion": "Perkauman & agama",
        "State Government Stability": "Kestabilan negeri",
        "Other": "Lain-lain",
    }
    return labels.get(name, name)


def _render_html(data: Dict[str, Any], brief: Dict[str, Any], plan: Dict[str, Any]) -> str:
    states = data.get("states", {})
    n9 = states.get("N9", {})

    def section(st: Dict, brief_key: str, comm: str) -> str:
        c = st.get(comm, {})
        b = brief.get(brief_key, {}).get(comm, {})
        issues = "".join(
            f"<div class='issue-row'><span class='issue-name' title='{n}'>{_issue_label(n)}</span>"
            f"<div class='bar-wrap'><div class='bar'><span style='width:{p}%'></span></div></div>"
            f"<strong class='issue-pct'>{p}%</strong></div>"
            for n, p in c.get("issues", [])
        )
        samples = c.get("samples", [])
        samp_html = "".join(_format_sample_li(s) for s in samples) or "<li class='muted'>Tiada</li>"
        actions = b.get("actions_p1", []) + b.get("actions_p2", [])
        act_html = "".join(f"<li>{a}</li>" for a in actions) or "<li class='muted'>—</li>"
        playable = "".join(f"<li>{p}</li>" for p in b.get("playable_narratives", []))
        return f"""
        <div class="kpi-grid">
          <div class="kpi"><label>Posts (tapis)</label><strong>{c.get('posts',0)}</strong></div>
          <div class="kpi"><label>Negatif</label><strong>{c.get('neg_pct',0)}%</strong></div>
          <div class="kpi"><label>Boikot</label><strong>{b.get('boycott_risk','?')}</strong></div>
        </div>
        <p class='assess'><strong>PH:</strong> {b.get('support_ph_assessment','—')}</p>
        <p class='assess'><strong>PAS/PN/MN:</strong> {b.get('pas_pn_mn_perception','—')}</p>
        <h4>Isu actionable</h4>{issues or '<p class="muted">—</p>'}
        <h4>Naratif boleh dimainkan</h4><ul>{playable or '<li>—</li>'}</ul>
        <h4>Tindakan ({brief.get('llm_provider','?')})</h4><ul class="actions">{act_html}</ul>
        <h4>Bukti (RAG sample · BM)</h4><ul class="samples">{samp_html}</ul>"""

    exec_sum = brief.get("executive_summary_ms", "")
    priorities = "".join(f"<li>{p}</li>" for p in brief.get("coalition_priorities", []))
    dont = "".join(f"<li>{d}</li>" for d in brief.get("do_not_do", []))
    from naratif_halatuju_n9 import build_halatuju_brief, render_halatuju_tab  # noqa: WPS433
    halatuju = build_halatuju_brief(data, brief)
    halatuju_html = render_halatuju_tab(halatuju)

    return f"""<!DOCTYPE html>
<html lang="ms"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Naratif Cina & India · Negeri Sembilan · Agentic Intel</title>
<style>
:root {{ --bg:#0b1220; --card:#151f32; --border:#2a3650; --text:#e8edf5; --muted:#93a4bd;
  --rose:#fb7185; --purple:#c084fc; --blue:#60a5fa; --green:#34d399; --amber:#fbbf24; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family: system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
.wrap {{ max-width:1400px; margin:0 auto; padding:24px 20px 48px; }}
h1 {{ font-size:1.5rem; }}
.sub {{ color:var(--muted); margin:6px 0 16px; font-size:0.88rem; }}
.pill {{ display:inline-block; background:var(--card); border:1px solid var(--border); border-radius:999px; padding:5px 11px; font-size:0.75rem; margin:0 6px 6px 0; }}
.data-meta {{ background:rgba(52,211,153,.08); border:1px solid rgba(52,211,153,.25); border-radius:10px;
  padding:10px 14px; margin:10px 0 14px; font-size:0.84rem; color:var(--text); line-height:1.5; }}
.data-meta strong {{ color:var(--green); }}
.tabs {{ display:flex; gap:8px; margin:16px 0; flex-wrap:wrap; }}
.tab-btn {{ background:var(--card); border:1px solid var(--border); color:var(--muted); padding:10px 18px;
  border-radius:10px; cursor:pointer; font-size:0.88rem; font-weight:600; }}
.tab-btn.active {{ background:rgba(52,211,153,.15); border-color:var(--green); color:var(--green); }}
.tab-panel.hidden {{ display:none; }}
.ai-box {{ background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.3); border-radius:12px; padding:16px; margin-bottom:18px; }}
.ai-box h2 {{ color:var(--green); font-size:1rem; margin-bottom:8px; }}
.grid {{ display:grid; grid-template-columns:1fr; gap:18px; align-items:start; }}
.panel {{ background:var(--card); border:1px solid var(--border); border-radius:14px; overflow:visible; }}
.head {{ padding:14px 16px; border-bottom:1px solid var(--border); }}
.head.j {{ border-top:4px solid var(--blue); }}
.head.n {{ border-top:4px solid var(--green); }}
.comm-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:0; }}
@media(max-width:900px){{ .comm-grid {{ grid-template-columns:1fr; }} }}
.comm {{ background:var(--card); padding:16px 18px; border-right:1px solid var(--border); min-width:0; }}
.comm:last-child {{ border-right:none; }}
@media(max-width:900px){{ .comm {{ border-right:none; border-bottom:1px solid var(--border); }} .comm:last-child {{ border-bottom:none; }} }}
.comm.ch h3 {{ color:var(--rose); font-size:0.95rem; margin-bottom:8px; }}
.comm.in h3 {{ color:var(--purple); font-size:0.95rem; margin-bottom:8px; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:8px 0 10px; }}
.kpi {{ background:#0b1220; border:1px solid var(--border); border-radius:8px; padding:10px 8px; min-width:0; overflow:visible; }}
.kpi label {{ font-size:0.6rem; color:var(--muted); text-transform:uppercase; display:block; }}
.kpi strong {{ font-size:1.1rem; display:block; word-break:break-word; overflow:visible; white-space:normal; }}
h4 {{ font-size:0.68rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin:14px 0 8px; }}
.issue-row {{ display:grid; grid-template-columns:minmax(88px,120px) 1fr 42px; gap:8px; align-items:center;
  font-size:0.8rem; margin-bottom:6px; }}
.issue-name {{ line-height:1.3; word-break:break-word; }}
.issue-pct {{ text-align:right; white-space:nowrap; font-size:0.82rem; }}
.bar-wrap {{ min-width:40px; }}
.bar {{ height:8px; background:#0b1220; border-radius:4px; overflow:hidden; }}
.bar span {{ display:block; height:100%; min-width:2px; background:linear-gradient(90deg,var(--green),var(--blue)); }}
.assess {{ font-size:0.84rem; color:var(--muted); margin:6px 0; line-height:1.5; word-wrap:break-word; overflow-wrap:anywhere; }}
ul {{ padding-left:18px; font-size:0.84rem; }}
ul.actions li {{ color:var(--green); margin-bottom:8px; line-height:1.45; }}
ul.samples li {{ margin-bottom:10px; line-height:1.45; word-wrap:break-word; }}
.tag {{ font-size:0.6rem; padding:2px 6px; border-radius:4px; background:#334155; margin-right:6px; vertical-align:middle; }}
.muted {{ color:var(--muted); }}
.orig {{ display:block; margin-top:4px; font-size:0.78rem; color:var(--amber); font-style:italic; }}
footer {{ margin-top:20px; color:var(--muted); font-size:0.72rem; }}
/* Action tab */
.action-intro .doc-links {{ margin-top:8px; font-size:0.82rem; color:var(--green); }}
.rules-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px; }}
@media(max-width:800px){{ .rules-grid {{ grid-template-columns:1fr; }} }}
.rules-panel {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; }}
.rules-panel h4 {{ margin-top:0; }}
.rules-panel ul.green li {{ color:var(--green); }}
.rules-panel.warn-panel {{ border-color:rgba(251,113,133,.3); }}
.rules-panel ul.red li {{ color:var(--rose); }}
.state-actions {{ display:flex; flex-direction:column; gap:24px; }}
.state-block {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px; }}
.state-block.n {{ border-top:4px solid var(--green); }}
.state-block.j {{ border-top:4px solid var(--blue); }}
.state-block h2 {{ font-size:1.1rem; margin-bottom:8px; }}
.stats-note {{ font-size:0.82rem; color:var(--muted); margin-bottom:14px; }}
.action-card {{ background:#0b1220; border:1px solid var(--border); border-radius:12px; margin-bottom:14px; overflow:hidden; }}
.action-card.p1 {{ border-left:4px solid var(--rose); }}
.action-card.p2 {{ border-left:4px solid var(--amber); }}
.action-head {{ padding:14px 16px; border-bottom:1px solid var(--border); }}
.action-head h3 {{ font-size:0.95rem; margin:6px 0 4px; }}
.pri-tag {{ font-size:0.65rem; font-weight:700; padding:3px 8px; border-radius:6px; text-transform:uppercase; }}
.pri-tag.p1 {{ background:rgba(251,113,133,.2); color:var(--rose); }}
.pri-tag.p2 {{ background:rgba(251,191,36,.2); color:var(--amber); }}
.act-meta {{ font-size:0.72rem; color:var(--muted); }}
.action-body {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; padding:14px 16px; }}
@media(max-width:800px){{ .action-body {{ grid-template-columns:1fr; }} }}
.action-col h5 {{ font-size:0.68rem; color:var(--muted); text-transform:uppercase; margin:10px 0 6px; }}
.action-col h5:first-child {{ margin-top:0; }}
.action-col .why {{ color:var(--amber); font-size:0.85rem; }}
ol.how {{ padding-left:18px; font-size:0.84rem; }}
ol.how li {{ margin-bottom:6px; }}
.msg-box {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px; font-size:0.84rem; }}
.msg-box .lbl {{ font-size:0.62rem; background:#334155; padding:2px 6px; border-radius:4px; margin-right:6px; }}
.msg-box .lbl.zh {{ background:rgba(251,113,133,.2); }}
.msg-box .lbl.ta {{ background:rgba(192,132,252,.2); }}
.act-footer {{ margin-top:12px; font-size:0.8rem; color:var(--muted); }}
.act-footer p {{ margin:4px 0; }}
.dun-wrap {{ margin-top:24px; }}
.dun-wrap h3 {{ font-size:1rem; margin-bottom:6px; }}
.dun-note {{ font-size:0.82rem; color:var(--muted); margin-bottom:10px; }}
.dun-scroll {{ overflow-x:auto; }}
.dun-table {{ width:100%; border-collapse:collapse; font-size:0.78rem; min-width:900px; }}
.dun-table th, .dun-table td {{ border:1px solid var(--border); padding:8px; text-align:left; vertical-align:top; }}
.dun-table th {{ background:#0b1220; color:var(--muted); font-size:0.68rem; text-transform:uppercase; }}
.dun-table .act-cell {{ max-width:280px; line-height:1.45; }}
.pri-sm {{ font-size:0.65rem; font-weight:700; padding:2px 6px; border-radius:4px; }}
.pri-sm.p1 {{ background:rgba(251,113,133,.2); color:var(--rose); }}
.pri-sm.p2 {{ background:rgba(251,191,36,.2); color:var(--amber); }}
.n9-targets {{ margin-top:18px; }}
.targets-inner {{ padding:14px 16px 18px; }}
.targets-table {{ min-width:1400px; }}
.targets-table tr.st-kosong td {{ opacity:0.92; }}
.targets-table tr.st-kosong td.act-ch, .targets-table tr.st-kosong td.act-in, .targets-table tr.st-kosong td.fokus-cell {{ background:rgba(52,211,153,.06); opacity:1; }}
.targets-table tr.st-thin td {{ background:rgba(251,191,36,.04); }}
.pri-sm.ok {{ background:rgba(52,211,153,.2); color:var(--green); }}
.src-badge {{ display:inline-block; font-size:0.6rem; font-weight:700; padding:2px 6px; border-radius:4px; margin-top:4px; }}
.src-badge.tpl {{ background:rgba(148,163,184,.25); color:#cbd5e1; }}
.src-badge.crawl_tpl {{ background:rgba(56,189,248,.2); color:#7dd3fc; }}
.src-badge.thin {{ background:rgba(251,191,36,.2); color:var(--amber); }}
.fokus-cell {{ min-width:160px; line-height:1.4; }}
.fokus-cell small {{ color:var(--muted); }}
.act-ch {{ border-left:2px solid rgba(251,113,133,.35); }}
.act-in {{ border-left:2px solid rgba(192,132,252,.35); }}
.intel-cell {{ color:var(--muted); max-width:140px; }}
.sample-cell {{ max-width:180px; font-size:0.72rem; }}
.muted-lbl {{ color:#64748b; font-style:italic; }}
</style></head><body><div class="wrap">
<h1>Naratif Cina & India · Negeri Sembilan · Agentic Intel</h1>
<p class="sub">Fokus N9 sahaja · Data ditapis (isu actionable) · RAG + LLM · Untuk PAS / PN / MN</p>
<span class="pill">Dijana: {data.get('generated_at','')}</span>
<span class="pill">Tapis N9: {data.get('filtered_rows',0)} / {data.get('raw_rows',0)} rows</span>
<span class="pill">LLM: {brief.get('llm_provider','?')} · {brief.get('confidence','?')}</span>

<div class="data-meta">
  <strong>Data Negeri Sembilan:</strong> {data.get('filtered_rows',0):,} posts · ~{data.get('engagement_label','0')} engagement · {data.get('date_range','—')}<br/>
  <strong>Sumber:</strong> Chinese news crawl · Indian RSS · FB/IG/TikTok/X · 36 DUN N9
</div>

<div class="tabs">
  <button class="tab-btn active" data-tab="intel">📊 Intel Naratif N9</button>
  <button class="tab-btn" data-tab="halatuju">🧭 Halatuju Strategi N9</button>
  <button class="tab-btn" data-tab="actions">📋 Cadangan Tindakan N9</button>
</div>

<div id="tab-intel" class="tab-panel">
<div class="ai-box">
  <h2>🤖 Executive Summary (Agentic AI) — Negeri Sembilan</h2>
  <p>{exec_sum}</p>
  <h4 style="margin-top:12px">Keutamaan Koalisi Minggu Ini (N9)</h4>
  <ul>{priorities}</ul>
  <h4>Jangan Buat</h4>
  <ul style="color:var(--rose)">{dont}</ul>
</div>

<div class="grid">
  <div class="panel"><div class="head n"><h2>Negeri Sembilan · 36 DUN</h2></div>
    <div class="comm-grid">
      <div class="comm ch"><h3>🇨🇳 Cina</h3>{section(n9,'n9','chinese')}</div>
      <div class="comm in"><h3>🇮🇳 India</h3>{section(n9,'n9','indian')}</div>
    </div></div>
</div>

{_render_n9_targets_section(data.get('n9_target_duns', []))}
</div>

{halatuju_html}

{_render_actions_tab(plan)}

<footer>InsightPulse Agentic · Refresh: NEImpulse/bin/python scripts/analyze_naratif_agentic.py --rebuild</footer>
</div>
<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    btn.classList.add('active');
    const map = {{intel:'tab-intel', halatuju:'tab-halatuju', actions:'tab-actions'}};
    const id = map[btn.dataset.tab] || 'tab-intel';
    document.getElementById(id).classList.remove('hidden');
  }});
}});
</script>
</body></html>"""


def _build_state_stats(df: pd.DataFrame) -> Dict[str, Any]:
    out: Dict[str, Any] = {"states": {}, "n9_target_duns": _build_n9_target_duns(df), "focus": "Negeri Sembilan"}
    for state, key in [("Negeri Sembilan", "N9")]:
        bundle = _stats_bundle(df, state)
        ch, ind = bundle["chinese"], bundle["indian"]
        out["states"][key] = {
            "chinese": {
                "posts": ch["posts"],
                "neg_pct": ch["neg_pct"],
                "issues": ch["issues"],
                "samples": [
                    {
                        "text": e.get("text_bm") or e["text"],
                        "text_bm": e.get("text_bm") or e["text"],
                        "text_original": e.get("text_original", e["text"]),
                        "sent": e["sentiment"],
                        "meta": f"{e['location']} · {e['platform']}",
                    }
                    for e in ch["evidence"][:5]
                ],
            },
            "indian": {
                "posts": ind["posts"],
                "neg_pct": ind["neg_pct"],
                "issues": ind["issues"],
                "samples": [
                    {
                        "text": e.get("text_bm") or e["text"],
                        "text_bm": e.get("text_bm") or e["text"],
                        "text_original": e.get("text_original", e["text"]),
                        "sent": e["sentiment"],
                        "meta": f"{e['location']} · {e['platform']}",
                    }
                    for e in ind["evidence"][:5]
                ],
            },
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="Skip API call, use rule brief")
    parser.add_argument("--project-id", default="PRN_N9", help="Project registry key used for LLM provider routing")
    parser.add_argument(
        "--llm-provider",
        default=None,
        help="Override registry provider: on-prem-nemotron, cloud-openai, cloud-super, rule-based",
    )
    args = parser.parse_args()

    print("🔍 Tapisan Negeri Sembilan + analisis agentic…")
    _load_env()
    raw = _load_df(args.rebuild)
    raw_n9 = raw[raw["state"] == "Negeri Sembilan"] if "state" in raw.columns else raw

    from utils.johor_n9_relevance_filter import filter_johor_n9  # noqa: WPS433
    filtered = filter_johor_n9(raw_n9)
    if "state" in filtered.columns:
        filtered = filtered[filtered["state"] == "Negeri Sembilan"].copy()
    print(f"   Tapis: {len(filtered)} / {len(raw_n9)} rows (Negeri Sembilan sahaja)")

    eng_total = _engagement_total(filtered)
    eng_label = f"{eng_total // 1000}K" if eng_total >= 1000 else str(eng_total)

    stats_full = {
        "N9": _stats_bundle(filtered, "Negeri Sembilan"),
    }

    brief = (
        _rule_brief(stats_full)
        if args.no_llm
        else _llm_brief(
            stats_full,
            len(filtered),
            len(raw_n9),
            project_id=args.project_id,
            llm_provider=args.llm_provider,
        )
    )

    analytics = _build_state_stats(filtered)
    analytics.update({
        "generated_at": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "raw_rows": len(raw_n9),
        "filtered_rows": len(filtered),
        "engagement_total": eng_total,
        "engagement_label": eng_label,
        "date_range": _date_range_label(filtered),
        "filter_rate_pct": round(len(filtered) / max(len(raw_n9), 1) * 100, 1),
        "agentic_brief": brief,
        "focus_state": "Negeri Sembilan",
    })

    from naratif_action_plan_builder import build_action_plan, save_action_plan  # noqa: WPS433
    action_plan = build_action_plan(brief=brief, analytics=analytics, focus="n9")
    save_action_plan(action_plan)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(analytics, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_BRIEF.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(_render_html(analytics, brief, action_plan), encoding="utf-8")
    from naratif_halatuju_n9 import build_halatuju_brief as _hh  # noqa: WPS433
    _hp = OUT_DIR / "naratif_halatuju_n9_logo_seatshare.json"
    _hp.write_text(json.dumps(_hh(analytics, brief), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Halatuju: {_hp}")

    # Kit copywriting + DOCX N9 (GPT-4o bahasa mudah)
    if not args.no_llm:
        try:
            from regenerate_naratif_docx_gpt4o import (  # noqa: WPS433
                _gpt4o_plan,
                _load_context as _llm_ctx,
                _load_env as _llm_load_env,
                _write_llm_docx,
            )
            _llm_load_env()
            print("📄 Jana DOCX panduan operasi N9 (LLM provider ikut registry/CLI)…")
            llm_ctx = _llm_ctx()
            for state, key in [("Negeri Sembilan", "n9")]:
                content = _gpt4o_plan(
                    state,
                    llm_ctx,
                    project_id=args.project_id,
                    llm_provider=args.llm_provider,
                )
                json_out = OUT_DIR / f"naratif_cadangan_tindakan_{key}_llm.json"
                json_out.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
                p = _write_llm_docx(content, OUT_DIR / f"naratif_cadangan_tindakan_{key}.docx")
                print(f"✅ DOCX {key} ({content.get('llm_provider')}): {p}")
        except Exception as e:
            print(f"⚠️ GPT-4o DOCX gagal ({e}) — guna template asas")
            try:
                from export_naratif_docx import export_both  # noqa: WPS433
                kit_path = OUT_DIR / "naratif_action_kit.json"
                kit = json.loads(kit_path.read_text(encoding="utf-8")) if kit_path.exists() else None
                for label, p in export_both(plan=action_plan, kit=kit).items():
                    if "n9" in label.lower() or "sembilan" in label.lower():
                        print(f"✅ DOCX {label}: {p}")
            except Exception as e2:
                print(f"⚠️ DOCX export: {e2}")

    print(f"✅ Brief: {OUT_BRIEF}")
    print(f"✅ Action plan: {OUT_ACTION_PLAN}")
    print(f"✅ Dashboard: {OUT_HTML}")
    print(f"   LLM: {brief.get('llm_provider')} · confidence: {brief.get('confidence')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
