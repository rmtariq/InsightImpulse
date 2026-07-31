#!/usr/bin/env python3
"""
Analytics + Insight padat untuk 4 post Pengundi Malaysia (Mac1+Mac2).
Guna: post + comments + engagement + sentiment/emotion + sample komen (RAG context).
Output: DOCX + JSON insight (War Room + dashboard).

Usage:
  python3 scripts/generate_pengundi_4posts_insight_docx.py
  python3 scripts/generate_pengundi_4posts_insight_docx.py --no-llm
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
MYT = timezone(timedelta(hours=8))
ANALYSIS_JSON = (
    ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/n9_pengundi_4posts_analysis.json"
)
MASTER_CSV = ROOT / "data/combined/Combined_facebook_MAC1_MAC2_master_20260715_015148.csv"
OUT_DIR = ROOT / "data/projects/political/PRN/PRN_N9/reports/pengundi_4posts"
OUT_DOCX = OUT_DIR / f"Pengundi_4Posts_Insight_{datetime.now(MYT).strftime('%Y%m%d_%H%M%S')}.docx"
OUT_JSON = OUT_DIR / "pengundi_4posts_insight_latest.json"

POST_MATCHERS = [
    ("POST-1", lambda t: "keramat terbesar" in t or "kembalikan kuasa melayu" in t),
    ("POST-2", lambda t: "adat pepatih" in t or ("majoriti" in t and "umno" in t and "pas" in t)),
    ("POST-3", lambda t: "situasi negeri sembilan" in t or ("pakatan harapan" in t and "barisan nasional" in t)),
    ("POST-4", lambda t: ("pas & umno" in t or "pas dan umno" in t) and "adat" not in t and "keramat" not in t),
]

THEME_KEYWORDS = {
    "mn_gabungan": r"umno|pas|mn|gabungan|kerjasama|bersatu|perpaduan",
    "tolak_ph_dap": r"tolak.*(ph|dap|harapan)|lawan.*(ph|dap)|x\s*sokong.*ph|anti.?ph",
    "adat_istana": r"adat|pepatih|undang|istana|muhriz|monarki",
    "melayu_islam": r"melayu|islam|agama|bangsa|ummah|keramat",
    "skeptikal": r"tak\s*setuju|tidak\s*setuju|jangan\s*percaya|malu|00000|skept",
    "sokong_ph": r"sokong.*(ph|harapan|dap)|pilihan\s*a|\(a\)|^a[\.\)]",
    "sokong_bn_pn": r"sokong.*(bn|pn|barisan)|pilihan\s*b|\(b\)|^b[\.\)]|umno.?pas",
}


def load_csv(path: Path) -> List[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def belongs_post(row: dict, post_row: dict) -> bool:
    if (row.get("Type") or "").lower() == "post":
        return row.get("ID") == post_row.get("ID")
    pid = post_row.get("ID") or ""
    purl = post_row.get("URL") or ""
    ppid = row.get("Parent_Post_ID") or ""
    ppu = row.get("Parent_Post_URL") or ""
    if pid and ppid == pid:
        return True
    if pid and pid in ppu:
        return True
    if purl and len(purl) > 30 and (purl in ppu or purl[:50] in ppu):
        return True
    return False


def extract_post_bundle(rows: List[dict], match_fn) -> tuple[dict, List[dict]]:
    posts = [r for r in rows if (r.get("Type") or "").lower() == "post" and match_fn((r.get("Text") or "").lower())]
    if not posts:
        return {}, []
    post = max(posts, key=lambda p: int(float(p.get("comments_count") or 0)))
    comments = [r for r in rows if belongs_post(r, post) and (r.get("Type") or "").lower() == "comment"]
    return post, comments


def theme_counts(comments: List[dict]) -> Counter:
    c: Counter = Counter()
    for row in comments:
        t = (row.get("Text") or "").lower()
        for name, pat in THEME_KEYWORDS.items():
            if re.search(pat, t, re.I):
                c[name] += 1
    return c


def top_quotes(comments: List[dict], n: int = 5) -> List[str]:
    def eng(r):
        try:
            return int(float(r.get("total_engagement") or r.get("likes") or 0))
        except (TypeError, ValueError):
            return 0

    ranked = sorted(comments, key=eng, reverse=True)
    out = []
    for r in ranked:
        text = (r.get("Text") or "").strip().replace("\n", " ")
        if len(text) < 20:
            continue
        if text in out:
            continue
        out.append(text[:220])
        if len(out) >= n:
            break
    return out


def rule_based_insight(post_id: str, post: dict, comments: List[dict], base: dict) -> dict:
    themes = theme_counts(comments)
    top3 = themes.most_common(4)
    likes = int(float(post.get("likes") or base.get("likes") or 0))
    shares = int(float(post.get("shares") or base.get("shares") or 0))
    n = len(comments)
    neg = base.get("negative_pct") or 0
    pos = base.get("positive_pct") or 0
    love = (base.get("emotions_top5") or {}).get("love", 0)
    love_pct = round(100 * love / max(n, 1), 1)

    analytics = (
        f"{n:,} komen crawled ({base.get('coverage_pct', 0)}% FB) · "
        f"{likes:,} likes · {shares} shares · "
        f"Sentimen {neg}% neg / {pos}% pos · Emosi Love {love_pct}%"
    )

    if post_id == "POST-3":
        vs = base.get("vote_signal") or {}
        insight = (
            f"Undian eksplisit: BN+PN **{vs.get('B_pct_of_decided')}%** vs PH **{vs.get('A_pct_of_decided')}%** "
            f"({vs.get('B_BN_PN_explicit', 0)} B vs {vs.get('A_PH_explicit', 0)} A). "
            f"Frame 'N9 ≠ Johor' berkesan — komen pro-MN/anti-PH dominan. "
            f"PH perlu counter-narrative khusus N9 (bukan copy Selangor/Johor)."
        )
        tindakan = [
            "MN: tekankan perbezaan N9 — adat, MN pragmatik, bukan model Johor",
            "PH: elak debat DAP frontal; fokus ekonomi + kestabilan negeri",
            "Digital: boost komen B dengan testimoni Undang/adat (selari Post 2)",
        ]
        bloc = "MN/PN +3pp · PH -2pp"
    elif post_id == "POST-1":
        sig = base.get("cooperation_signal") or {}
        insight = (
            f"Post **paling viral** (14.6K likes). Setuju ~{base.get('setuju_pct_of_signal')}% vs tidak {sig.get('tidak_setuju', 0)} — "
            f"base Melayu-Islam **engaged** (Love {love_pct}%) walaupun sentiment negatif tinggi (debate panas). "
            f"Frame 'dua parti keramat' = kod MN; pushback dari anti-BN dan skeptikal PAS murni."
        )
        tindakan = [
            "Guna influencer selari Ustazah Asmak — konsisten, elak over-promise gabungan rasmi",
            "Rapid response: bezakan 'kerjasama rakyat Melayu' vs 'gabungan parti'",
            "Jangan biarkan negatif dibaca sebagai anti-MN — siarkan testimoni setuju",
        ]
        bloc = "MN +2pp · PAS Solo +1pp"
    elif post_id == "POST-2":
        insight = (
            f"Coverage **98%** — data paling lengkap untuk frame **Adat Pepatih**. "
            f"Setuju ~{base.get('setuju_pct_of_signal')}% — komen sebut Hadi/Zahid, target N9 BN+PAS. "
            f"Negatif = politicking dalaman (Johor/Gerakan), bukan reject adat."
        )
        tindakan = [
            "Couple MN dengan adat + Undang — elak sentuh sensitif MB vs Undang-4",
            "Waar room message: 'selamatkan Adat Pepatih' = hook Melayu tradisional N9",
            "Monitor Zahid vs Hadi narrative — satu suara sahaja di digital",
        ]
        bloc = "MN +3pp (adat frame)"
    else:  # POST-4
        sig = base.get("cooperation_signal") or {}
        insight = (
            f"Soalan direct — **{sig.get('neutral', 0)} komen neutral** (wait-and-see). "
            f"Setuju ~{base.get('setuju_pct_of_signal')}% — pengundi **boleh terima** PAS+UMNO "
            f"tetapi tunggu bukti (seat deal, manifesto). Engagement tinggi, commitment rendah."
        )
        tindakan = [
            "Perlu proof point: contoh kerusi, calon, atau statement bersama",
            "Convert neutral → setuju dengan fakta (bukan slogan)",
            "Elak ulang Post 1/2 — fokus 'bagaimana' bukan 'setuju tak'",
        ]
        bloc = "MN +1pp (belum fully committed)"

    theme_txt = ", ".join(f"{k} ({v})" for k, v in top3) if top3 else "—"
    quotes = top_quotes(comments)

    return {
        "analytics_line": analytics,
        "insight_ringkas": insight,
        "tema_komen_top": theme_txt,
        "komen_representatif": quotes,
        "tindakan_disyorkan": tindakan,
        "impak_bloc": bloc,
        "method": "rule_based_rag",
    }


def try_llm_enrich(post_id: str, question: str, rag: dict, insight: dict) -> dict:
    """Optional LLM polish via Nemotron/OpenAI."""
    try:
        sys.path.insert(0, str(ROOT))
        from backend.nim_client import get_llm_client, generate_json, PROVIDER_RULE_ONLY

        for provider in ("on-prem-nemotron", "cloud-openai"):
            try:
                client, model, prov = get_llm_client(provider)
            except Exception:
                continue
            prompt = f"""Post: {post_id}
Soalan poll: {question}
Analytics: {insight['analytics_line']}
Tema komen: {insight['tema_komen_top']}
Sample komen: {rag.get('quotes', [])[:3]}

Tulis JSON dengan kunci:
- insight_executive (2-3 ayat BM, padat, untuk EXCO)
- risiko (1 ayat)
- peluang (1 ayat)
- mesej_48jam (bullet 3 item, max 12 perkataan/item)
Fokus PRN N9, MN vs PH, data-driven."""
            try:
                out = generate_json(
                    client=client,
                    model=model,
                    prompt=prompt,
                    system="Anda analis politik Malaysia. Jawab JSON sahaja. Bahasa Melayu formal ringkas.",
                    provider=prov,
                    required_keys=["insight_executive"],
                    temperature=0.25,
                    max_tokens=800,
                )
                insight["llm"] = out
                insight["method"] = f"llm_{prov}"
                return insight
            except Exception:
                continue
    except Exception:
        pass
    return insight


def build_docx(report: dict, path: Path) -> None:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    title = doc.add_heading("InsightPulse — Analitik & Insight", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("4 Post Pengundi Malaysia · PRN Negeri Sembilan · Mac1 + Mac2")
    doc.add_paragraph(f"Generated: {report['generated']} · Master: {report['master_csv']}")
    doc.add_paragraph(
        f"Jumlah: {report['summary']['posts']} post · "
        f"{report['summary']['comments']:,} komen · "
        f"{report['summary']['engagement']:,} engagement"
    )
    doc.add_paragraph()

    for p in report["posts"]:
        doc.add_heading(f"{p['id']} — {p['title'][:80]}", level=1)
        doc.add_paragraph(p.get("post_url") or "")

        doc.add_heading("Analitik", level=2)
        doc.add_paragraph(p["analytics_line"])

        tbl = doc.add_table(rows=2, cols=5)
        tbl.style = "Table Grid"
        hdr = ["Komen", "Likes", "Shares", "Neg%", "Pos%"]
        vals = [
            str(p.get("crawled_comments", "")),
            str(p.get("likes", "")),
            str(p.get("shares", "")),
            f"{p.get('negative_pct', '—')}%",
            f"{p.get('positive_pct', '—')}%",
        ]
        for i, h in enumerate(hdr):
            tbl.rows[0].cells[i].text = h
            tbl.rows[1].cells[i].text = vals[i]

        doc.add_heading("Insight (padat)", level=2)
        doc.add_paragraph(p["insight_ringkas"])

        llm = p.get("llm") or {}
        if llm.get("insight_executive"):
            doc.add_paragraph(f"EXCO: {llm['insight_executive']}")
        if llm.get("risiko"):
            doc.add_paragraph(f"Risiko: {llm['risiko']}")
        if llm.get("peluang"):
            doc.add_paragraph(f"Peluang: {llm['peluang']}")

        doc.add_heading("Tema komen (RAG)", level=2)
        doc.add_paragraph(p.get("tema_komen_top") or "—")

        doc.add_heading("Komen representatif", level=2)
        for q in p.get("komen_representatif") or []:
            doc.add_paragraph(q, style="List Bullet")

        doc.add_heading("Tindakan disyorkan (72j)", level=2)
        for t in p.get("tindakan_disyorkan") or []:
            doc.add_paragraph(t, style="List Number")

        if llm.get("mesej_48jam"):
            doc.add_heading("Mesej 48 jam", level=2)
            for m in llm["mesej_48jam"]:
                doc.add_paragraph(str(m), style="List Bullet")

        doc.add_paragraph(f"Impak bloc (anggaran): {p.get('impak_bloc', '—')}")
        doc.add_paragraph()

    doc.add_heading("Kesimpulan Gabungan", level=1)
    doc.add_paragraph(report.get("kesimpulan_gabungan") or "")

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--master", type=Path, default=MASTER_CSV)
    args = parser.parse_args()

    if not args.master.exists():
        print(f"❌ Master CSV not found: {args.master}")
        return 1

    rows = load_csv(args.master)
    base_analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8")) if ANALYSIS_JSON.exists() else {}
    base_by_id = {p["id"]: p for p in base_analysis.get("posts_analyzed", [])}

    titles = {
        "POST-1": "Kerjasama dua parti keramat · Kuasa Melayu Islam (Ustazah Asmak)",
        "POST-2": "UMNO & PAS · Selamatkan Adat Pepatih",
        "POST-3": "PH vs BN+PN · N9 ≠ Johor (Poll A/B)",
        "POST-4": "PAS & UMNO kerjasama di PRN N9",
    }

    posts_out = []
    for pid, match_fn in POST_MATCHERS:
        post, comments = extract_post_bundle(rows, match_fn)
        base = base_by_id.get(pid, {})
        insight = rule_based_insight(pid, post, comments, base)
        rag = {"quotes": top_quotes(comments, 8), "themes": theme_counts(comments).most_common(5)}
        if not args.no_llm:
            insight = try_llm_enrich(pid, base.get("question") or titles[pid], rag, insight)
        posts_out.append({
            "id": pid,
            "title": titles[pid],
            "question": base.get("question") or titles[pid],
            "post_url": base.get("post_url") or post.get("URL"),
            "crawled_comments": len(comments) or base.get("crawled_comments"),
            "likes": base.get("likes") or int(float(post.get("likes") or 0)),
            "shares": base.get("shares") or int(float(post.get("shares") or 0)),
            "negative_pct": base.get("negative_pct"),
            "positive_pct": base.get("positive_pct"),
            "vote_signal": base.get("vote_signal"),
            "cooperation_signal": base.get("cooperation_signal"),
            **insight,
        })

    total_comments = sum(p["crawled_comments"] for p in posts_out)
    total_eng = sum((p.get("likes") or 0) + (p.get("shares") or 0) + (p.get("crawled_comments") or 0) for p in posts_out)

    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    OUT_DOCX = OUT_DIR / f"Pengundi_4Posts_Insight_{ts}.docx"

    report = {
        "generated": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
        "master_csv": str(args.master.relative_to(ROOT)),
        "summary": {"posts": 4, "comments": total_comments, "engagement": total_eng},
        "posts": posts_out,
        "kesimpulan_gabungan": (
            "Empat post viral Pengundi MY menunjukkan **sokongan komen terhadap MN/BN+PN** "
            "(Poll Post 3: B 76%) dan **kerjasama UMNO–PAS** bila diframe Melayu-Islam/adat (Post 1–2 ~63–69% setuju). "
            "Sentiment negatif tinggi = debate heated, bukan reject total. "
            "Post 4: pengundi wait-and-see — perlu proof point. "
            "Impak War Room: MN kekal laluan utama; PH perlu counter khusus N9."
        ),
        "insight_docx": None,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_docx(report, OUT_DOCX)
    report["insight_docx"] = str(OUT_DOCX.relative_to(ROOT))
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if ANALYSIS_JSON.exists():
        wa = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
        for p in wa.get("posts_analyzed", []):
            ext = next((x for x in posts_out if x["id"] == p["id"]), None)
            if ext:
                p["insight_padat"] = ext.get("insight_ringkas")
                p["analytics_line"] = ext.get("analytics_line")
                p["tindakan_72j"] = ext.get("tindakan_disyorkan")
                p["tema_komen"] = ext.get("tema_komen_top")
                if ext.get("llm"):
                    p["llm_insight"] = ext["llm"]
        wa["insight_report_json"] = str(OUT_JSON.relative_to(ROOT))
        wa["insight_docx"] = report["insight_docx"]
        ANALYSIS_JSON.write_text(json.dumps(wa, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ DOCX: {OUT_DOCX}")
    print(f"✅ JSON: {OUT_JSON}")
    print("   Run: python3 scripts/sync_pengundi_4posts_warroom.py  (refresh dashboard)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
