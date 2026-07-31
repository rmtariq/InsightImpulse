#!/usr/bin/env python3
"""
Generate PAS/PN/MN actionable copy kit — socmed, poster, video prompts.
Grounded in Johor+N9 filtered narrative intel + agentic brief.

Output:
  data/projects/political/PRN/reports/naratif_cina_india/naratif_action_kit.json
  data/projects/political/PRN/reports/naratif_cina_india/naratif_action_kit.html
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
BRIEF = OUT_DIR / "naratif_agentic_brief.json"
ANALYTICS = OUT_DIR / "naratif_cina_india_johor_n9_analytics.json"
OUT_JSON = OUT_DIR / "naratif_action_kit.json"
OUT_HTML = OUT_DIR / "naratif_action_kit.html"
MYT = timezone(timedelta(hours=8))

ANTHROPIC_MODELS = ("claude-sonnet-4-6", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001")

# Rule-based fallback — isu #1 dari crawl ditapis
FALLBACK_KIT: Dict[str, Any] = {
    "generated_at": "",
    "coalition": "PAS · PN · MN (Muafakat Nasional)",
    "tone_rules": [
        "Fokus perkhidmatan, ekonomi, kestabilan — bukan teologi atau agama",
        "Jangan ulang isu syurga/Harakat — gunakan Shawn Loh/China Press sebagai fakta sahaja",
        "Jawab 巫伊 dengan ketelusan: stabil negeri, bukan pakatan sulit",
        "BM + 中文 + Tamil dalam setiap asset utama",
        "Elak serangan perkauman; serang prestasi & penyelesaian konkrit",
    ],
    "johor": {
        "chinese": {
            "facebook": [
                {
                    "title": "Johor stabil — peniaga kecil didahulukan",
                    "bm": "Kos sara hidup & trafik JB/Skudai memang isu sebenar. Kami dengar. Senarai bantuan negeri + perkhidmatan bandar dikemas kini. Stabiliti Johor = perniagaan boleh merancang. #PRNJohor",
                    "zh": "柔佛要稳定，小贩和中小企业才能安心做生意。州政府整理生活成本援助与市区交通服务清单。#柔佛州选",
                    "cta": "PM untuk helaian BM+中文",
                    "hashtags": "#PRNJohor #柔佛州选 #新山 #士古来",
                },
                {
                    "title": "Ketelusan — bukan kerjasama sulit",
                    "bm": "Soalan komuniti Cina: adakah ada 'pakatan tersembunyi'? Jawapan kami: kestabilan negeri & elak pecah undi. Fakta di meja — bukan rumor WhatsApp.",
                    "zh": "华人社区关心：有没有“秘密协议”？我们的立场：州选稳定、避免分裂投票。事实摆在桌面，不是谣言。",
                    "cta": "Kongsi ke group merchant JB",
                    "hashtags": "#Johor #国阵 #稳定",
                },
            ],
            "poster": {
                "headline_bm": "JOHOR STABIL · PENIAGA DIDAHULUKAN",
                "headline_zh": "柔佛稳定 · 商家优先",
                "sub_bm": "Bantuan kos sara hidup · Trafik & perkhidmatan bandar · Fakta disahkan",
                "sub_zh": "生活援助 · 市区交通与服务 · 经核实的信息",
                "footer": "PAS · PN · MN — Muafakat untuk Johor",
            },
            "tiktok_prompt": (
                "30s vertical video, Johor PRN. Scene 1: busy Skudai street market. "
                "Malay presenter + Chinese subtitle. Script BM: 'Kami dengar isu kos & trafik.' "
                "Scene 2: infographic overlay — 3 bullet bantuan negeri. "
                "Scene 3: CTA 'Stabiliti = perniagaan boleh merancang.' Tone: calm, factual, no religion."
            ),
            "whatsapp_forward": "📋 Helaian BM+中文: Bantuan kos sara hidup & perkhidmatan bandar Johor (Skudai/JB). Stabiliti negeri — bukan rumor. [pautan]",
        },
        "indian": {
            "facebook": [
                {
                    "title": "Segamat Hospital — kami dengar",
                    "bm": "Kekurangan doktor di Hospital Segamat dirakam. Pasukan negeri sedang susun jawapan fakta + langkah interim. Pekerjaan & kesihatan komuniti India kekal keutamaan.",
                    "ta": "சிகாமாத் மருத்துவமனையில் மருத்துவர் பற்றாக்குறை குறித்து கேள்விகள் உள்ளன. மாநில அ팀் உறுதிப்படுத்தப்பட்ட தகவலுடன் பதிலளிக்கிறது.",
                    "cta": "Share di group kilang Kluang/Batu Pahat",
                    "hashtags": "#Johor #Segamat #SJKT",
                },
            ],
            "poster": {
                "headline_bm": "PEKERJAAN & KESIHATAN · JOHOR",
                "headline_ta": "வேலைவாய்ப்பு & சுகாதாரம்",
                "sub_bm": "Kilang selatan · Hospital · Perkhidmatan disahkan",
                "footer": "PAS · PN · MN",
            },
            "tiktok_prompt": (
                "35s Tamil+BM factory worker POV, Kluang/Batu Pahat. "
                "Show hospital queue cutaway. Voiceover: pekerjaan & perubatan komuniti. "
                "End card: 'Fakta dari kerajaan negeri — bukan spekulasi.'"
            ),
        },
        "punjabi": {
            "note": "Komuniti Punjabi kecil di Johor (Kulai, JB) — guna BM+English, elak politik agama",
            "facebook": [
                {
                    "bm": "Kepada sahabat komuniti Punjabi di Johor: isu pekerjaan, perniagaan kecil & keselamatan kejiranan — kami sedia dengar di pejabat khidmat.",
                    "en": "To our Punjabi friends in Johor: jobs, small business & neighbourhood safety — service centre open for verified assistance.",
                }
            ],
        },
    },
    "n9": {
        "chinese": {
            "facebook": [
                {
                    "title": "Kos hidup Seremban — jawapan konkrit",
                    "bm": "Aduan kos sara hidup & SME di Jelebu/Seremban kami rakam. Helaian bantuan aktif (negeri + persekutuan) BM+中文 dalam 48 jam. Undi = perkhidmatan, bukan drama.",
                    "zh": "芙蓉及汝来商家关注生活成本。48小时内发布中英对照援助清单。投票要看服务，不是口水战。",
                    "cta": "Tag persatuan peniaga NS",
                    "hashtags": "#PRNN9 #森美兰 #芙蓉",
                },
                {
                    "title": "Trafik Seremban — kami ambil serius",
                    "bm": "Kesesakan & parking di bandar Seremban isu berulang. Pasukan tempatan sedang susun mesyuarat dengan MBSA & peniaga — kemas kini minggu ini.",
                    "zh": "芙蓉市区交通与停车问题，州团队本周与市议会及商家开会跟进。",
                    "cta": "Share di group merchant Seremban",
                    "hashtags": "#Seremban #交通",
                },
            ],
            "poster": {
                "headline_bm": "NEGERI SEMBILAN · KOS HIDUP & PERKHIDMATAN",
                "headline_zh": "森美兰 · 生活成本与服务",
                "sub_bm": "Bantuan disahkan · SME · Trafik Seremban",
                "sub_zh": "核实援助 · 中小企业 · 芙蓉交通",
                "footer": "PAS · PN · MN",
            },
            "tiktok_prompt": (
                "40s Seremban night market. Chinese auntie voiceover (subtitle BM+中文). "
                "Topic: kos hidup & parking. Show 3 verified aid bullets. "
                "Avoid attacking DAP personally — focus 'penyelesaian konkrit'."
            ),
        },
        "indian": {
            "facebook": [
                {
                    "title": "SJKT — guru & masa depan anak",
                    "bm": "Isu guru SJKT & pendidikan Tamil masih panas di N9. Kami sediakan kemas kini BM+Tamil status pengisian & peruntukan — fakta sahaja.",
                    "ta": "SJKT ஆசிரியர் பற்றாக்குறை — தமிழ்+BM அதிகாரப்பூர்வ புதுப்பிப்பு விரைவில்.",
                    "cta": "Forward ke group SJKT parents Port Dickson/Seremban",
                    "hashtags": "#SJKT #N9 #PortDickson",
                },
            ],
            "poster": {
                "headline_bm": "PENDIDIKAN TAMIL · PEKERJAAN",
                "headline_ta": "தமிழ் கல்வி · வேலைவாய்ப்பு",
                "sub_bm": "SJKT · Port Dickson · Fakta disahkan",
                "footer": "PAS · PN · MN",
            },
            "tiktok_prompt": (
                "30s SJKT classroom B-roll + parent interview Tamil. "
                "Message: pendidikan & pekerjaan anak India N9. Calm tone, no communal bait."
            ),
        },
        "punjabi": {
            "note": "Punjabi Sikh komuniti di Seremban/KL fringe — fokus perniagaan & keselamatan",
            "facebook": [
                {
                    "bm": "Komuniti Punjabi N9: kos operasi kedai & keselamatan kawasan perniagaan — hubungi pejabat khidmat untuk senarai bantuan disahkan.",
                    "en": "N9 Punjabi business community: operating costs & safety — contact service office for verified aid list.",
                }
            ],
        },
    },
    "counter_narratives": {
        "dap_hidden_pact": {
            "bm": "Tiada pakatan sulit. Ada kestabilan negeri supaya undi tidak pecah. Fakta di meja.",
            "zh": "没有秘密协议。只有州选稳定，避免分裂投票。事实为主。",
            "ta": "ரகசிய கூட்டணி இல்லை. நிலைத்தன்மை மற்றும் உண்மைகள் மட்டும்.",
        },
        "harakat_fake_news": {
            "bm": "Berita palsu Harakatdaily disahkan media Cina (China Press). Jangan kongsi tanpa semak.",
            "zh": "Harakatdaily假新闻已被中国报澄清。请勿转发未经核实内容。",
            "do_not": "Jangan debat syurga — redirect ke fakta Shawn Loh",
        },
        "abstention_risk": {
            "bm": "Duduk rumah = undi PH/BN tanpa usaha. Jika mahu perubahan perkhidmatan — keluar undi, pilih kestabilan.",
            "zh": "不投票等于把结果交给别人。要改善服务，就要出来投票，选择稳定。",
        },
    },
    "video_prompts_capcut": [
        {
            "name": "Template A — 3 fakta 30s",
            "prompt": "CapCut template: 3 slides. Slide1 hook question in BM+中文. Slide2 3 bullet facts with icons. Slide3 CTA vote for stability. Music: neutral corporate. No flags drama.",
        },
        {
            "name": "Template B — Calon di pasar",
            "prompt": "Handheld market walk, Skudai/Seremban. Calon dengar peniaga. Subtitle trilingual. End: 'Kami dengar. Kami urus.'",
        },
        {
            "name": "Template C — Infografik animasi",
            "prompt": "Motion graphic: kos hidup comparison chart (verified sources only). BM voiceover + 中文 subtitles. Brand colors: blue/green calm.",
        },
    ],
    "llm_provider": "rule_based",
}


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _load_context() -> Dict[str, Any]:
    ctx: Dict[str, Any] = {"brief": {}, "analytics": {}}
    if BRIEF.exists():
        ctx["brief"] = json.loads(BRIEF.read_text(encoding="utf-8"))
    if ANALYTICS.exists():
        ctx["analytics"] = json.loads(ANALYTICS.read_text(encoding="utf-8"))
    return ctx


def _llm_kit(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    _load_env()
    prompt = f"""Anda pakar komunikasi politik Malaysia untuk koalisi PAS + PN + Muafakat Nasional (MN/BN).

Berdasarkan intel naratif ini, hasilkan KIT COPYWRITING lengkap JSON untuk menarik sokongan / mengurangkan abstention komuniti Cina, India, dan Punjabi di Johor & Negeri Sembilan.

INTEL:
{json.dumps(ctx, ensure_ascii=False)[:6000]}

RULES:
- Tiada retorik agama/syurga/JAKIM
- Fokus: kos hidup, trafik, SME, SJKT, hospital, kestabilan, ketelusan MN
- Setiap blok perlu BM + 中文 (Cina) dan/atau Tamil (India)
- Copy mesti boleh paste terus ke FB/IG/TikTok
- Sertakan poster headline, subhead, CTA
- Sertakan 3 prompt video pendek (CapCut/Runway style)
- Sertakan counter-narrative untuk: DAP hidden pact, Harakat fake news, abstention

JSON schema:
{{
  "coalition": "PAS · PN · MN",
  "tone_rules": ["..."],
  "johor": {{
    "chinese": {{ "facebook": [{{"title","bm","zh","cta","hashtags"}}], "instagram_carousel": ["slide1","slide2"], "poster": {{}}, "tiktok_script_30s": "", "whatsapp": "" }},
    "indian": {{ ... }},
    "punjabi": {{ "facebook": [...], "note": "" }}
  }},
  "n9": {{ same structure }},
  "counter_narratives": {{}},
  "video_prompts_capcut": [{{"name","prompt"}}],
  "weekly_calendar": [{{"day","platform","community","topic"}}]
}}

Jawab JSON sahaja."""

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        for model in [os.getenv("ANTHROPIC_MODEL")] + list(ANTHROPIC_MODELS):
            if not model:
                continue
            try:
                msg = client.messages.create(
                    model=model, max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = msg.content[0].text
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    data = json.loads(m.group())
                    data["llm_provider"] = "anthropic"
                    data["llm_model"] = model
                    return data
            except Exception:
                continue

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            data["llm_provider"] = "openai"
            data["llm_model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return data
        except Exception:
            pass
    return None


def _render_html(kit: Dict[str, Any]) -> str:
    def posts_block(posts: List[Dict]) -> str:
        if not posts:
            return "<p class='muted'>—</p>"
        html = ""
        for p in posts:
            html += f"<div class='copy-card'><h4>{p.get('title','Post')}</h4>"
            if p.get("bm"):
                html += f"<p><span class='lbl'>BM</span>{p['bm']}</p>"
            if p.get("zh"):
                html += f"<p><span class='lbl zh'>中文</span>{p['zh']}</p>"
            if p.get("ta"):
                html += f"<p><span class='lbl ta'>தமிழ்</span>{p['ta']}</p>"
            if p.get("en"):
                html += f"<p><span class='lbl'>EN</span>{p['en']}</p>"
            if p.get("hashtags"):
                html += f"<p class='tags'>{p['hashtags']}</p>"
            if p.get("cta"):
                html += f"<p class='cta'>CTA: {p['cta']}</p>"
            html += "</div>"
        return html

    def state_section(state_key: str, label: str) -> str:
        st = kit.get(state_key, {})
        parts = []
        for comm, title, color in [
            ("chinese", "🇨🇳 Komuniti Cina", "var(--rose)"),
            ("indian", "🇮🇳 Komuniti India", "var(--purple)"),
            ("punjabi", "🪯 Komuniti Punjabi", "var(--amber)"),
        ]:
            c = st.get(comm, {})
            if not c:
                continue
            poster = c.get("poster", {})
            poster_html = ""
            if poster:
                poster_html = (
                    f"<div class='poster'><div class='ph'>{poster.get('headline_bm','')}</div>"
                    f"<div class='ph zh'>{poster.get('headline_zh', poster.get('headline_ta',''))}</div>"
                    f"<div class='ps'>{poster.get('sub_bm','')}</div>"
                    f"<div class='pf'>{poster.get('footer','')}</div></div>"
                )
            tiktok = c.get("tiktok_prompt") or c.get("tiktok_script_30s") or ""
            parts.append(f"""
            <div class="comm-block">
              <h3 style="color:{color}">{title}</h3>
              {f"<p class='note'>{c['note']}</p>" if c.get('note') else ''}
              <h5>Facebook / Socmed</h5>{posts_block(c.get('facebook', []))}
              {poster_html}
              {f"<h5>TikTok / Video prompt</h5><pre class='prompt'>{tiktok}</pre>" if tiktok else ''}
              {f"<h5>WhatsApp</h5><p>{c.get('whatsapp_forward', c.get('whatsapp',''))}</p>" if c.get('whatsapp_forward') or c.get('whatsapp') else ''}
            </div>""")
        return f"<div class='state'><h2>{label}</h2>{''.join(parts)}</div>"

    rules = "".join(f"<li>{r}</li>" for r in kit.get("tone_rules", []))
    counters = ""
    for k, v in kit.get("counter_narratives", {}).items():
        if isinstance(v, dict):
            counters += f"<div class='copy-card'><h4>{k}</h4>"
            for lang, txt in v.items():
                if lang != "do_not":
                    counters += f"<p><strong>{lang}:</strong> {txt}</p>"
            if v.get("do_not"):
                counters += f"<p class='warn'>⚠️ {v['do_not']}</p>"
            counters += "</div>"

    videos = "".join(
        f"<div class='copy-card'><h4>{v.get('name','')}</h4><pre class='prompt'>{v.get('prompt','')}</pre></div>"
        for v in kit.get("video_prompts_capcut", [])
    )

    return f"""<!DOCTYPE html>
<html lang="ms"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Kit Copywriting · PAS/PN/MN · Johor + N9</title>
<style>
:root {{ --bg:#0b1220; --card:#151f32; --border:#2a3650; --text:#e8edf5; --muted:#93a4bd;
  --rose:#fb7185; --purple:#c084fc; --blue:#60a5fa; --green:#34d399; --amber:#fbbf24; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:1.45rem; }}
.sub {{ color:var(--muted); margin:8px 0 16px; font-size:0.88rem; }}
.pill {{ display:inline-block; background:var(--card); border:1px solid var(--border); border-radius:999px; padding:5px 11px; font-size:0.75rem; margin-right:6px; }}
.panel {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:14px; }}
.panel h2 {{ color:var(--blue); font-size:1rem; margin-bottom:10px; }}
.state {{ margin-bottom:20px; }}
.comm-block {{ border-top:1px solid var(--border); padding-top:12px; margin-top:12px; }}
.comm-block h3 {{ font-size:0.95rem; margin-bottom:8px; }}
.comm-block h5 {{ font-size:0.7rem; color:var(--muted); text-transform:uppercase; margin:12px 0 6px; letter-spacing:.06em; }}
.copy-card {{ background:#0b1220; border:1px solid var(--border); border-radius:8px; padding:12px; margin-bottom:8px; }}
.copy-card h4 {{ font-size:0.85rem; color:var(--green); margin-bottom:6px; }}
.lbl {{ display:inline-block; font-size:0.65rem; background:#334155; padding:2px 6px; border-radius:4px; margin-right:6px; }}
.lbl.zh {{ background:rgba(251,113,133,.2); }}
.lbl.ta {{ background:rgba(192,132,252,.2); }}
.tags {{ font-size:0.78rem; color:var(--blue); }}
.cta {{ font-size:0.8rem; color:var(--amber); }}
.poster {{ background:linear-gradient(135deg,#1e3a5f,#0f172a); border:2px solid var(--blue); border-radius:10px; padding:20px; text-align:center; margin:10px 0; }}
.poster .ph {{ font-size:1.3rem; font-weight:800; letter-spacing:.04em; }}
.poster .ph.zh {{ font-size:1.1rem; color:var(--rose); margin-top:4px; }}
.poster .ps {{ font-size:0.85rem; color:var(--muted); margin-top:8px; }}
.poster .pf {{ font-size:0.75rem; margin-top:12px; color:var(--green); }}
.prompt {{ background:#0b1220; border:1px solid var(--border); border-radius:8px; padding:10px; font-size:0.78rem; white-space:pre-wrap; margin:6px 0; }}
.warn {{ color:var(--rose); font-size:0.82rem; }}
.note {{ font-size:0.82rem; color:var(--muted); font-style:italic; }}
.muted {{ color:var(--muted); }}
footer {{ margin-top:20px; color:var(--muted); font-size:0.72rem; }}
</style></head><body><div class="wrap">
<h1>📣 Kit Copywriting Kempen · PAS / PN / MN</h1>
<p class="sub">Johor + Negeri Sembilan · Cina · India · Punjabi · Socmed · Poster · Video prompts</p>
<span class="pill">Dijana: {kit.get('generated_at','')}</span>
<span class="pill">LLM: {kit.get('llm_provider','?')}</span>

<div class="panel"><h2>🎯 Peraturan nada (WAJIB)</h2><ul>{rules}</ul></div>

{state_section('johor', 'Johor · 56 DUN')}
{state_section('n9', 'Negeri Sembilan · 36 DUN')}

<div class="panel"><h2>🛡️ Counter-narrative (copy-paste)</h2>{counters or '<p class="muted">—</p>'}</div>
<div class="panel"><h2>🎬 Prompt video pendek (CapCut / TikTok)</h2>{videos or '<p class="muted">—</p>'}</div>

<footer>InsightPulse · NEImpulse/bin/python scripts/generate_naratif_action_kit.py</footer>
</div></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    print("📣 Jana kit copywriting PAS/PN/MN…")
    ctx = _load_context()
    kit = None if args.no_llm else _llm_kit(ctx)
    if not kit:
        kit = json.loads(json.dumps(FALLBACK_KIT))
        kit["llm_provider"] = "rule_based_professional"
        print("   Guna kit profesional rule-based (fallback)")

    kit["generated_at"] = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
    kit["source_brief"] = str(BRIEF.relative_to(ROOT)) if BRIEF.exists() else None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(_render_html(kit), encoding="utf-8")
    print(f"✅ JSON: {OUT_JSON}")
    print(f"✅ HTML: {OUT_HTML}")
    print(f"   Provider: {kit.get('llm_provider')}")

    # Kemas kini DOCX jika pelan tindakan wujud
    plan_path = OUT_DIR / "naratif_cadangan_tindakan.json"
    if plan_path.exists():
        try:
            if str(ROOT / "scripts") not in sys.path:
                sys.path.insert(0, str(ROOT / "scripts"))
            from export_naratif_docx import export_both  # noqa: WPS433
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            for label, p in export_both(plan=plan, kit=kit).items():
                print(f"✅ DOCX {label}: {p}")
        except Exception as e:
            print(f"⚠️ DOCX: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
