#!/usr/bin/env python3
"""
Jana semula DOCX cadangan tindakan — GPT-4o, bahasa mudah, format panduan operasi.
Untuk pasukan calon & ground team yang bukan penganalisis data.

Output:
  naratif_cadangan_tindakan_johor.docx
  naratif_cadangan_tindakan_n9.docx
  naratif_cadangan_tindakan_johor_llm.json
  naratif_cadangan_tindakan_n9_llm.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/projects/political/PRN/reports/naratif_cina_india"
MYT = timezone(timedelta(hours=8))

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from naratif_action_plan_builder import JOHOR_DUNS, N9_DUNS  # noqa: E402


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _load_context() -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}
    for name in ("naratif_cina_india_johor_n9_analytics", "naratif_agentic_brief", "naratif_action_kit"):
        p = OUT_DIR / f"{name}.json"
        if p.exists():
            ctx[name] = json.loads(p.read_text(encoding="utf-8"))
    return ctx


def _state_intel(ctx: Dict[str, Any], state_key: str) -> Dict[str, Any]:
    analytics = ctx.get("naratif_cina_india_johor_n9_analytics", {})
    brief = ctx.get("naratif_agentic_brief", {})
    st = analytics.get("states", {}).get(state_key, {})
    brief_key = "johor" if state_key == "Johor" else "n9"
    return {
        "stats": st,
        "brief": brief.get(brief_key, {}),
        "coalition_priorities": brief.get("coalition_priorities", []),
        "do_not_do": brief.get("do_not_do", []),
        "filtered_rows": analytics.get("filtered_rows"),
    }


def _dun_list(state: str) -> List[Dict[str, str]]:
    table = JOHOR_DUNS if state == "Johor" else N9_DUNS
    prefix = "JHR" if state == "Johor" else "NS"
    return [{"code": c, "name": n, "label": f"{prefix}-{c}"} for c, n in table.items()]


def _gpt4o_plan(
    state: str,
    ctx: Dict[str, Any],
    *,
    project_id: str = "PRN_N9",
    llm_provider: Optional[str] = None,
) -> Dict[str, Any]:
    _load_env()
    from backend.nim_client import generate_json, get_llm_client, get_provider_for_project, provider_failover_order

    intel = _state_intel(ctx, state)
    kit_key = "johor" if state == "Johor" else "n9"
    kit = ctx.get("naratif_action_kit", {}).get(kit_key, {})
    duns = _dun_list(state)
    dun_count = len(duns)

    prompt = f"""Anda penulis panduan operasi kempen PRN untuk PAS + PN + Muafakat Nasional (MN).
Tulis untuk PEGAWAI KEMPEN BIASA — bukan penganalisis data. Bahasa Melayu mudah, jelas, mesra.

NEGERI: {state} ({dun_count} kerusi DUN)
INTEL DATA (dari media sosial & berita komuniti Cina/India):
{json.dumps(intel, ensure_ascii=False)[:5000]}

KIT COPYWRITING SEDIA ADA:
{json.dumps(kit, ensure_ascii=False)[:3000]}

SENARAI SEMUA DUN:
{json.dumps(duns, ensure_ascii=False)}

ARAHAN PENTING:
1. JANGAN guna jargon teknikal (contoh: abstention, optics, intel crawl, RAG, KPI tanpa penjelasan).
   Ganti dengan bahasa biasa: "pengundi duduk rumah", "imej koalisi", "data media sosial", "sasaran kerja".
2. Setiap tindakan mesti jawab 5 soalan: MASALAH APA? → BUAT APA? → SIAPA? → BILA? → AYAT APA NAK CAKAP?
3. Terangkan istilah politik jika perlu (contoh: 巫伊 = kerjasama UMNO-PAS, MN = Muafakat Nasional).
4. Tajuk tindakan = ayat pendek yang calon faham terus (contoh: "Jawab rumor pakatan sulit di group WhatsApp merchant").
5. Sertakan SEMUA {dun_count} DUN dalam senarai_dun — ayat 1 baris mudah per komuniti (Cina & India).
6. Nada: profesional, tenang, fokus perkhidmatan — BUKAN agama/syurga.
7. Copy BM + 中文 wajib untuk tindakan Cina; BM + Tamil untuk tindakan India.

Jawab JSON SAHAJA:
{{
  "tajuk_utama": "Panduan Operasi Kempen — {state}",
  "subtajuk": "Komuniti Cina & India · bahasa mudah untuk calon & ground team",
  "baca_ini_dahulu": {{
    "situasi_sekarang": "3-5 ayat: apa yang komuniti Cina & India sedang bincang di {state}",
    "tiga_perkara_paling_penting": ["ayat 1", "ayat 2", "ayat 3"],
    "risiko_terbesar": "1-2 ayat: apa jadi kalau kita tak buat apa-apa",
    "peluang_menang_hati": "1-2 ayat: apa yang boleh menarik sokongan"
  }},
  "peraturan_emas": ["5 peraturan ringkas — ayat mudah"],
  "jangan_buat": ["3 kesilapan — ayat mudah"],
  "tindakan_minggu_ini": [
    {{
      "nombor": 1,
      "tajuk": "tajuk ringkas calon faham",
      "masalah": "apa pengundi/rakyat adu — bahasa biasa",
      "apa_kita_buat": "ringkasan 1-2 ayat",
      "langkah": ["Langkah 1 ...", "Langkah 2 ...", "Langkah 3 ...", "Langkah 4 ..."],
      "siapa_bertanggungjawab": "nama peranan jelas: calon DUN X, exco, operasi Cina, dll",
      "bila": "contoh: dalam 48 jam / minggu ini",
      "di_mana": "FB group / pasar / kilang / WhatsApp",
      "ayat_siap_copy_bm": "teks penuh boleh paste",
      "ayat_siap_copy_zh": "中文",
      "ayat_siap_copy_ta": "தமிழ் atau kosong",
      "dun_terlibat": ["N48 Skudai", "..."],
      "cara_ukur_berjaya": "sasaran mudah difahami, bukan jargon"
    }}
  ],
  "tindakan_minggu_depan": [ ... struktur sama, 2-3 item ... ],
  "senarai_dun": [
    {{
      "kod": "N48",
      "nama": "Skudai",
      "keutamaan": "TINGGI|SEDERHANA|RENDAH",
      "untuk_komuniti_cina": "1 ayat: apa calon buat minggu ini",
      "untuk_komuniti_india": "1 ayat: apa calon buat minggu ini"
    }}
  ],
  "jawapan_pantasan": [
    {{
      "soalan_rakyat": "contoh: Ada pakatan sulit antara PAS dan BN?",
      "jawapan_bm": "2-3 ayat mudah",
      "jawapan_zh": "中文"
    }}
  ],
  "minggu_ini_di_socmed": {{
    "post_1": {{"tajuk": "", "bm": "", "zh": "", "ta": "", "platform": "FB", "bila_pos": "Isnin 8mlm"}},
    "post_2": {{...}},
    "poster": {{"tajuk_bm": "", "tajuk_zh": "", "isi_bm": ""}}
  }}
}}

Wajib: tindakan_minggu_ini = 5 item. tindakan_minggu_depan = 3 item. senarai_dun = semua {dun_count} DUN."""

    primary = get_provider_for_project(project_id=project_id, explicit_provider=llm_provider)
    last_err: Optional[Exception] = None
    for provider in provider_failover_order(primary):
        if provider == "rule-based":
            break
        try:
            client, model, normalized_provider = get_llm_client(provider)
            print(f"   🤖 {normalized_provider} {model} — {state}…")
            data = generate_json(
                client=client,
                model=model,
                provider=normalized_provider,
                prompt=prompt,
                system=(
                    "Anda pakar komunikasi politik Malaysia. Tulis panduan operasi dalam BM mudah "
                    "untuk pasukan kempen lapangan. Output JSON sahaja, valid, lengkap."
                ),
                required_keys=(
                    "tajuk_utama",
                    "baca_ini_dahulu",
                    "peraturan_emas",
                    "jangan_buat",
                    "tindakan_minggu_ini",
                    "tindakan_minggu_depan",
                    "senarai_dun",
                    "jawapan_pantasan",
                ),
                cache_path=OUT_DIR / "cache" / f"naratif_cadangan_tindakan_{state.lower().replace(' ', '_')}.last_good.json",
                temperature=0.4,
                max_tokens=16000,
            )
            data["state"] = state
            data["generated_at"] = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
            return data
        except Exception as e:
            last_err = e
            print(f"⚠️ DOCX LLM failed ({provider}, {state}): {e}")

    raise RuntimeError(f"No DOCX LLM provider succeeded for {state}: {last_err}")


def _para(doc, text: str, bold: bool = False, size: Optional[int] = None) -> None:
    from docx.shared import Pt
    p = doc.add_paragraph()
    r = p.add_run(text)
    if bold:
        r.bold = True
    if size:
        r.font.size = Pt(size)


def _write_llm_docx(content: Dict[str, Any], out_path: Path) -> Path:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()
    navy = RGBColor(30, 58, 95)
    green = RGBColor(22, 101, 52)

    # === MUKA SURAT ===
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("PAS · PN · MN — Muafakat Nasional")
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = navy

    h = doc.add_heading(content.get("tajuk_utama", "Panduan Operasi"), level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph(content.get("subtajuk", ""))
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for line in [
        f"Dijana: {content.get('generated_at', '')}",
        f"Model: {content.get('llm_model', 'gpt-4o')}",
        "UNTUK: Calon DUN, pengurus kempen, operasi Cina/India",
        "⚠ INTERNAL — Jangan edar luar tanpa semakan HQ",
    ]:
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(
        "Dokumen ini ditulis dalam bahasa mudah supaya sesiapa di lapangan "
        "tahu apa masalah, apa tindakan, siapa buat, dan ayat apa nak guna.",
        style="Intense Quote",
    )

    # === BACA INI DAHULU ===
    doc.add_page_break()
    doc.add_heading("📌 BACA INI DAHULU (3 minit)", level=1)
    baca = content.get("baca_ini_dahulu", {})

    doc.add_heading("Apa situasi sekarang?", level=2)
    doc.add_paragraph(baca.get("situasi_sekarang", "—"))

    doc.add_heading("3 Perkara Paling Penting Minggu Ini", level=2)
    for i, item in enumerate(baca.get("tiga_perkara_paling_penting", []), 1):
        p = doc.add_paragraph(style="List Number")
        run = p.add_run(item)
        run.bold = True

    doc.add_heading("Risiko kalau kita tak buat apa-apa", level=2)
    p = doc.add_paragraph(baca.get("risiko_terbesar", "—"))
    for run in p.runs:
        run.font.color.rgb = RGBColor(180, 40, 40)

    doc.add_heading("Peluang untuk menarik sokongan", level=2)
    p = doc.add_paragraph(baca.get("peluang_menang_hati", "—"))
    for run in p.runs:
        run.font.color.rgb = green

    doc.add_heading("Peraturan Emas (WAJIB ikut)", level=2)
    for rule in content.get("peraturan_emas", []):
        doc.add_paragraph(rule, style="List Bullet")

    doc.add_heading("⛔ Jangan Buat Ini", level=2)
    for item in content.get("jangan_buat", []):
        p = doc.add_paragraph(item, style="List Bullet")
        for run in p.runs:
            run.font.color.rgb = RGBColor(180, 40, 40)

    # === TINDAKAN MINGGU INI ===
    doc.add_page_break()
    doc.add_heading("✅ TINDAKAN MINGGU INI — Mesti Buat", level=1)
    doc.add_paragraph(
        "Setiap tindakan di bawah sudah lengkap: masalah → langkah → ayat siap copy. "
        "Agihkan kepada calon mengikut DUN terlibat."
    )

    for act in content.get("tindakan_minggu_ini", []):
        doc.add_page_break()
        nom = act.get("nombor", "?")
        doc.add_heading(f"TINDAKAN {nom}: {act.get('tajuk', '')}", level=1)

        meta = doc.add_paragraph()
        meta.add_run(f"⏰ Bila: {act.get('bila', '—')}  |  ").bold = True
        meta.add_run(f"👤 Siapa: {act.get('siapa_bertanggungjawab', '—')}  |  ")
        meta.add_run(f"📍 Di mana: {act.get('di_mana', '—')}")
        if act.get("dun_terlibat"):
            doc.add_paragraph(f"Kerusi terlibat: {', '.join(act['dun_terlibat'])}")

        doc.add_heading("Masalah apa yang rakyat/pengundi adu?", level=2)
        doc.add_paragraph(act.get("masalah", "—"))

        doc.add_heading("Apa kita nak buat?", level=2)
        doc.add_paragraph(act.get("apa_kita_buat", "—"))

        doc.add_heading("Langkah demi langkah", level=2)
        for step in act.get("langkah", []):
            doc.add_paragraph(step, style="List Number")

        doc.add_heading("Ayat siap copy — paste terus ke FB/WhatsApp", level=2)
        if act.get("ayat_siap_copy_bm"):
            p = doc.add_paragraph()
            p.add_run("🇲🇾 BM:\n").bold = True
            p.add_run(act["ayat_siap_copy_bm"])
        if act.get("ayat_siap_copy_zh"):
            p = doc.add_paragraph()
            p.add_run("🇨🇳 中文:\n").bold = True
            p.add_run(act["ayat_siap_copy_zh"])
        if act.get("ayat_siap_copy_ta"):
            p = doc.add_paragraph()
            p.add_run("🇮🇳 தமிழ்:\n").bold = True
            p.add_run(act["ayat_siap_copy_ta"])

        doc.add_heading("Cara tahu kita berjaya", level=2)
        doc.add_paragraph(act.get("cara_ukur_berjaya", "—"))

    # === TINDAKAN MINGGU DEPAN ===
    susulan = content.get("tindakan_minggu_depan", [])
    if susulan:
        doc.add_page_break()
        doc.add_heading("📅 TINDAKAN MINGGU DEPAN — Susulan", level=1)
        for act in susulan:
            doc.add_heading(f"{act.get('tajuk', '')}", level=2)
            doc.add_paragraph(f"Masalah: {act.get('masalah', '')}")
            doc.add_paragraph(f"Buat apa: {act.get('apa_kita_buat', '')}")
            for step in act.get("langkah", []):
                doc.add_paragraph(step, style="List Bullet")
            if act.get("ayat_siap_copy_bm"):
                doc.add_paragraph(f"BM: {act['ayat_siap_copy_bm']}")

    # === JAWAPAN PANTAS ===
    jawapan = content.get("jawapan_pantasan", [])
    if jawapan:
        doc.add_page_break()
        doc.add_heading("💬 Jawapan Pantas — Bila Orang Tanya", level=1)
        doc.add_paragraph("Guna ayat ini bila pengundi tanya di group WhatsApp, pasar, atau komen FB.")
        for j in jawapan:
            doc.add_heading(j.get("soalan_rakyat", ""), level=2)
            doc.add_paragraph(j.get("jawapan_bm", ""))
            if j.get("jawapan_zh"):
                p = doc.add_paragraph()
                p.add_run("中文: ").bold = True
                p.add_run(j["jawapan_zh"])

    # === SENARAI DUN ===
    dun_rows = content.get("senarai_dun", [])
    if dun_rows:
        doc.add_page_break()
        doc.add_heading(f"📋 Senarai Semua DUN — {content.get('state', '')}", level=1)
        doc.add_paragraph(
            "Checklist untuk setiap calon: 1 ayat untuk komuniti Cina, 1 ayat untuk India. "
            "Keutamaan TINGGI = buat minggu ini."
        )
        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        for i, hdr in enumerate(["DUN", "Nama", "Keutamaan", "Apa calon buat (Cina)", "Apa calon buat (India)"]):
            table.rows[0].cells[i].text = hdr
            for p in table.rows[0].cells[i].paragraphs:
                for r in p.runs:
                    r.bold = True
        for row in dun_rows:
            cells = table.add_row().cells
            cells[0].text = row.get("kod", "")
            cells[1].text = row.get("nama", "")
            cells[2].text = row.get("keutamaan", "")
            cells[3].text = row.get("untuk_komuniti_cina", "")
            cells[4].text = row.get("untuk_komuniti_india", "")

    # === SOC MED ===
    soc = content.get("minggu_ini_di_socmed", {})
    if soc:
        doc.add_page_break()
        doc.add_heading("📱 Post Socmed Minggu Ini — Siap Copy", level=1)
        for key in ("post_1", "post_2", "post_3"):
            post = soc.get(key)
            if not post:
                continue
            doc.add_heading(post.get("tajuk", key), level=2)
            doc.add_paragraph(f"Platform: {post.get('platform', 'FB')} · Masa: {post.get('bila_pos', '')}")
            if post.get("bm"):
                doc.add_paragraph(f"BM: {post['bm']}")
            if post.get("zh"):
                doc.add_paragraph(f"中文: {post['zh']}")
            if post.get("ta"):
                doc.add_paragraph(f"தமிழ்: {post['ta']}")
        poster = soc.get("poster", {})
        if poster:
            doc.add_heading("Teks Poster", level=2)
            doc.add_paragraph(f"Tajuk BM: {poster.get('tajuk_bm', '')}")
            doc.add_paragraph(f"Tajuk 中文: {poster.get('tajuk_zh', '')}")
            doc.add_paragraph(f"Isi: {poster.get('isi_bm', '')}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=["Johor", "N9", "both"], default="both")
    parser.add_argument("--project-id", default="PRN_N9")
    parser.add_argument(
        "--llm-provider",
        default=None,
        help="Override registry provider: on-prem-nemotron, cloud-openai, cloud-super",
    )
    args = parser.parse_args()

    _load_env()

    ctx = _load_context()
    states = ["Johor", "Negeri Sembilan"] if args.state == "both" else (
        ["Johor"] if args.state == "Johor" else ["Negeri Sembilan"]
    )

    print("📄 Jana semula DOCX panduan operasi (LLM provider ikut registry/CLI)…")
    for state in states:
        key = "johor" if state == "Johor" else "n9"
        content = _gpt4o_plan(
            state,
            ctx,
            project_id=args.project_id,
            llm_provider=args.llm_provider,
        )
        json_path = OUT_DIR / f"naratif_cadangan_tindakan_{key}_llm.json"
        json_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        docx_path = _write_llm_docx(content, OUT_DIR / f"naratif_cadangan_tindakan_{key}.docx")
        n_dun = len(content.get("senarai_dun", []))
        n_act = len(content.get("tindakan_minggu_ini", []))
        print(f"✅ {state}: {n_act} tindakan · {n_dun} DUN · {docx_path}")

    print("\n💡 Nasihat: Mulakan dengan bahagian 'BACA INI DAHULU' — 3 minit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
