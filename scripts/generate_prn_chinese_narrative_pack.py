#!/usr/bin/env python3
"""Generate PRN Chinese Narrative pack — Negeri Sembilan + Melaka + Johor."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data/projects/political/pas_break_2026/reference"
N9_SEATS = ROOT / "data/projects/political/pas_break_2026/reports/n9_seats_analytics.csv"

OUT_XLSX = REF / "PRN_Chinese_Narrative_NS_Melaka_Johor.xlsx"
OUT_TXT = REF / "PRN_Chinese_Narrative_queries.txt"
OUT_GUIDE = REF / "PRN_Chinese_Narrative_CARA_GUNA.txt"

# Legacy alias (NS-only filename — regenerated from same pack)
OUT_N9_XLSX = REF / "N9_Chinese_Narrative_Seeds.xlsx"
OUT_N9_TXT = REF / "N9_Chinese_Narrative_queries.txt"
OUT_N9_GUIDE = REF / "N9_Chinese_Narrative_CARA_GUNA.txt"


def norm_fb(handle: str) -> str:
    if not handle or str(handle).strip().lower() in ("nan", "—", "-", ""):
        return ""
    h = str(handle).strip()
    if h.startswith("http"):
        return h.split("?")[0].rstrip("/")
    if not h.startswith("facebook."):
        h = f"facebook.com/{h.lstrip('/')}"
    return f"https://www.{h.lstrip('www.')}"


def norm_x(handle: str) -> str:
    if not handle or str(handle).strip().lower() in ("nan", "—", "-", ""):
        return ""
    return f"https://x.com/{str(handle).strip().lstrip('@')}"


def norm_tt(handle: str) -> str:
    if not handle or str(handle).strip().lower() in ("nan", "—", "-", ""):
        return ""
    return f"https://www.tiktok.com/@{str(handle).strip().lstrip('@')}"


def seed_row(
    negeri: str,
    koalisi: str,
    parti: str,
    nama: str,
    platform: str,
    url: str,
    kerusi: str,
    jenis: str,
    bahasa: str,
    prioriti: str,
    nota: str = "",
) -> dict:
    return {
        "Negeri": negeri,
        "Koalisi": koalisi,
        "Parti": parti,
        "Nama": nama,
        "Platform": platform,
        "URL": url,
        "Kerusi": kerusi,
        "Jenis_Suara": jenis,
        "Bahasa_Utama": bahasa,
        "Crawl_Mode": "direct_url",
        "Prioriti": prioriti,
        "Nota": nota,
    }


def build_seeds_direct() -> pd.DataFrame:
    rows: list[dict] = []

    # ── Negeri Sembilan ──
    ns = [
        ("PH", "DAP", "DAP Negeri Sembilan", "Facebook", norm_fb("facebook.com/dapnegerisembilan"), "N01-N36", "party_official", "bm", "Tinggi"),
        ("PH", "DAP", "Anthony Loke", "Facebook", norm_fb("facebook.com/anthonyloke"), "N01", "leader_chinese", "bm", "Tinggi"),
        ("PH", "DAP", "Anthony Loke", "X", norm_x("@anthonyloke"), "N01", "leader_chinese", "bm", "Tinggi"),
        ("PH", "DAP", "Nicole Tan", "Facebook", norm_fb("facebook.com/nicoletan.ns"), "N21", "adun_chinese", "bm", "Tinggi"),
        ("PH", "DAP", "Yap Yew Weng", "Facebook", norm_fb("facebook.com/yapyewweng"), "N23", "adun_chinese", "bm", "Tinggi"),
        ("PH", "DAP", "Gunasekaren Palasamy", "Facebook", norm_fb("facebook.com/gunasekaren.palasamy"), "N24", "adun_indian", "bm", "Tinggi"),
        ("PH", "DAP", "Teo Kok Seong", "Facebook", norm_fb("facebook.com/teokok.seong"), "N08", "adun_chinese", "bm", "Tinggi"),
        ("BN", "MCA", "MCA Malaysia", "Facebook", norm_fb("facebook.com/mcamalaysia"), "NS", "party_official", "bm", "Tinggi"),
    ]
    for r in ns:
        rows.append(seed_row("Negeri Sembilan", *r))

    # ── Johor ──
    jh = [
        ("PH", "DAP", "Liew Chin Tong", "Facebook", norm_fb("facebook.com/liewchintong"), "N46", "leader_chinese", "bm", "Tinggi", "Pengerusi DAP Johor"),
        ("PH", "DAP", "Liew Chin Tong", "X", norm_x("@LiewChinTong"), "N46", "leader_chinese", "bm", "Tinggi", ""),
        ("PH", "DAP", "DAP Johor", "Facebook", norm_fb("facebook.com/DAPJohor"), "N01-N56", "party_official", "bm", "Tinggi", "Sahkan URL jika gagal crawl"),
        ("BN", "MCA", "MCA Malaysia", "Facebook", norm_fb("facebook.com/mcamalaysia"), "Johor", "party_official", "bm", "Tinggi", "Nasional — relevan JB/bandar"),
        ("BN", "UMNO", "Onn Hafiz Ghazi", "Facebook", norm_fb("facebook.com/OnnHafizGhazi"), "MB", "leader_malay", "bm", "Sederhana", "Konteks MB Johor"),
        ("BN", "UMNO", "UMNO Johor", "Facebook", norm_fb("facebook.com/UMNOJohor"), "Johor", "party_official", "bm", "Sederhana", ""),
        ("PN", "PAS", "PAS Johor", "Facebook", norm_fb("facebook.com/PASJohor"), "Johor", "party_official", "bm", "Sederhana", ""),
    ]
    for r in jh:
        rows.append(seed_row("Johor", *r))

    # ── Melaka ──
    ml = [
        ("PH", "PKR/DAP", "Kerajaan Melaka (PH)", "Facebook", norm_fb("facebook.com/kerajaanmelaka"), "Kerajaan", "party_official", "bm", "Tinggi", "Kerajaan negeri PH"),
        ("PH", "DAP", "Khoo Poay Tiong", "Facebook", norm_fb("facebook.com/khoopoaytiong"), "N09", "leader_chinese", "bm", "Tinggi", "Pengerusi DAP Melaka"),
        ("PH", "DAP", "Low Chee Leong", "Facebook", norm_fb("facebook.com/lowcheeleong"), "N13", "adun_chinese", "bm", "Tinggi", "Kota Laksamana"),
        ("BN", "MCA", "MCA Malaysia", "Facebook", norm_fb("facebook.com/mcamalaysia"), "Melaka", "party_official", "bm", "Tinggi", ""),
        ("BN", "UMNO", "UMNO Melaka", "Facebook", norm_fb("facebook.com/UMNOMelaka"), "Melaka", "party_official", "bm", "Sederhana", ""),
        ("PN", "PAS", "PAS Melaka", "Facebook", norm_fb("facebook.com/pasmelaka"), "Melaka", "party_official", "bm", "Sederhana", ""),
    ]
    for r in ml:
        rows.append(seed_row("Melaka", *r))

    # Nasional (semua negeri)
    rows.append(seed_row(
        "Semua", "PH", "DAP", "DAP Malaysia", "Facebook", norm_fb("facebook.com/dapmalaysia"),
        "—", "party_official", "bm", "Sederhana", "Konteks nasional",
    ))

    df = pd.DataFrame(rows)
    return df[df["URL"].astype(str).str.len() > 10].reset_index(drop=True)


def build_kerusi_bandar() -> pd.DataFrame:
    """Kerusi bandar / DAP — proxy komuniti Cina (PRN lepas; kemaskini selepas penamaan)."""
    rows: list[dict] = []

    if N9_SEATS.exists():
        dap = pd.read_csv(N9_SEATS)
        dap = dap[dap["parti_menang"] == "DAP"]
        for _, r in dap.iterrows():
            rows.append({
                "Negeri": "Negeri Sembilan",
                "Kod_DUN": r["kod_dun"],
                "Kawasan": r["kawasan_dun"],
                "ADUN_2023": r["nama_adun"],
                "Query_Keyword": f'"{r["nama_adun"]}" OR "{r["kawasan_dun"]}" "Negeri Sembilan" PRN when:30d',
                "Query_Cina_Proxy": f'"pengundi Cina" OR DAP "{r["kawasan_dun"]}" "Negeri Sembilan" when:30d',
                "Prioriti": "Tinggi" if r["kod_dun"] in {"N01", "N10", "N11", "N21", "N22", "N23", "N24"} else "Sederhana",
            })

    johor_dap = [
        ("N12", "Bentayan", "Ng Yak Howe"),
        ("N23", "Penggaram", "Gan Peck Cheng"),
        ("N28", "Mengkibol", "Chew Chong Sin"),
        ("N42", "Johor Jaya", "Liow Cai Tung"),
        ("N45", "Stulang", "Andrew Chen Kah Eng"),
        ("N46", "Perling", "Liew Chin Tong"),
        ("N48", "Skudai", "Marina Ibrahim"),
        ("N52", "Senai", "Wong Bor Yang"),
    ]
    for code, kawasan, adun in johor_dap:
        rows.append({
            "Negeri": "Johor",
            "Kod_DUN": code,
            "Kawasan": kawasan,
            "ADUN_2023": adun,
            "Query_Keyword": f'"{adun}" OR "{kawasan}" Johor PRN when:30d',
            "Query_Cina_Proxy": f'"pengundi Cina" OR DAP "{kawasan}" Johor when:30d',
            "Prioriti": "Tinggi",
        })

    melaka_dap = [
        ("N09", "Ayer Keroh", "Khoo Poay Tiong"),
        ("N13", "Kota Laksamana", "Low Chee Leong"),
        ("N15", "Bandar Hilir", "— kemaskini calon"),
        ("N14", "Duyong", "— kemaskini calon"),
    ]
    for code, kawasan, adun in melaka_dap:
        rows.append({
            "Negeri": "Melaka",
            "Kod_DUN": code,
            "Kawasan": kawasan,
            "ADUN_2023": adun,
            "Query_Keyword": f'"{kawasan}" Melaka PRN OR "pilihan raya negeri melaka" when:30d',
            "Query_Cina_Proxy": f'"pengundi Cina" OR DAP "{kawasan}" Melaka when:30d',
            "Prioriti": "Tinggi" if code in {"N13", "N15", "N09"} else "Sederhana",
        })

    df = pd.DataFrame(rows)
    df["Kemaskini_Selepas_Penamaan"] = "Ganti nama calon 2026 bila SPR sah"
    return df


def build_queries() -> pd.DataFrame:
    states = [
        ("S1", "Negeri Sembilan", "Negeri Sembilan", "森美兰", "Seremban OR Nilai"),
        ("S2", "Johor", "Johor", "柔佛", "Johor Bahru OR Skudai OR Stulang"),
        ("S3", "Melaka", "Melaka", "马六甲", 'Melaka OR "Bandar Hilir"'),
    ]
    rows: list[tuple] = []

    for prefix, label, en, zh, bandar in states:
        rows += [
            (f"{prefix}A1", "News", f"Media Cina {label}", "news",
             f'"Sin Chew" OR "China Press" OR "星洲日报" OR "中国报" {en} OR {zh} when:30d',
             "media_chinese", "Tinggi", f"Suara media Cina — {label}"),
            (f"{prefix}A2", "News", f"Proxy BM {label}", "news",
             f'"pengundi Cina" OR "komuniti Cina" "{en}" PRN when:30d',
             "proxy_about_chinese", "Rendah", "Bukan suara Cina langsung"),
            (f"{prefix}B1", "news,facebook", f"DAP/PH {label}", "news,facebook",
             f'DAP OR "Pakatan Harapan" "{en}" PRN when:30d',
             "party_official", "Tinggi", "InsightPulse · dataset_size 2000"),
            (f"{prefix}B2", "news,facebook,x", f"Bandar {label}", "news,facebook,x",
             f'{bandar} calon OR PRN "{en}" when:30d',
             "seat_bandar", "Tinggi", ""),
            (f"{prefix}B3", "news,facebook", f"MCA/BN {label}", "news,facebook",
             f'MCA OR "Barisan Nasional" "{en}" PRN when:30d',
             "party_official", "Sederhana", ""),
        ]

    rows.append((
        "SX1", "News", "3 negeri serentak (media Cina)", "news",
        '"Sin Chew" OR "China Press" ("Negeri Sembilan" OR Johor OR Melaka) PRN when:30d',
        "media_chinese", "Tinggi", "Satu crawl untuk banding negeri",
    ))
    rows.append((
        "SX2", "news,facebook", "3 negeri — pengundi Cina", "news,facebook",
        '"pengundi Cina" ("Negeri Sembilan" OR Johor OR Melaka) when:30d',
        "proxy_about_chinese", "Rendah", "Banding naratif cross-state",
    ))

    return pd.DataFrame(rows, columns=[
        "ID", "Label", "Negeri", "Platform", "Query", "Jenis_Suara", "Prioriti_Analisis", "Nota",
    ])


def build_negeri_overview() -> pd.DataFrame:
    return pd.DataFrame([
        {"Negeri": "Negeri Sembilan", "DUN": 36, "Kerusi_DAP_2023": 11, "Fokus_Bandar": "Seremban, Nilai, PD", "Crawl_Priority": "Tinggi — PRN serentak Jun 2026"},
        {"Negeri": "Johor", "DUN": 56, "Kerusi_DAP_2023": 10, "Fokus_Bandar": "JB, Skudai, Stulang, Perling", "Crawl_Priority": "Tinggi — pengundi Cina bandar"},
        {"Negeri": "Melaka", "DUN": 28, "Kerusi_DAP_2023": "~8", "Fokus_Bandar": "Melaka Tengah, Bandar Hilir", "Crawl_Priority": "Sederhana — bandar kompak"},
    ])


def build_analysis_rules() -> pd.DataFrame:
    return pd.DataFrame([
        ("media_chinese", "Tinggi", "Suara media / komuniti Cina", "Sin Chew, China Press, 华文"),
        ("leader_chinese", "Tinggi", "Pemimpin DAP negeri", "Anthony Loke, Liew Chin Tong, Khoo Poay Tiong"),
        ("adun_chinese", "Tinggi", "ADUN kerusi bandar", "Nicole Tan, Low Chee Leong, dll."),
        ("adun_indian", "Sederhana", "Komuniti bukan Melayu bandar", "Gunasekaren — campuran"),
        ("party_official", "Sederhana", "Parti bercakap kepada pengundi", "DAP NS/Johor, MCA, kerajaan Melaka"),
        ("proxy_about_chinese", "Rendah", "Pihak lain sebut pengundi Cina", "Jangan kira 100% sebagai suara Cina"),
        ("seat_bandar", "Sederhana", "Perbincangan kawasan bandar", "Filter ikut Negeri semasa analisis"),
        ("leader_malay", "Rendah", "Pemimpin Melayu negeri", "Konteks politik, bukan suara Cina"),
    ], columns=["Jenis_Suara", "Weight_Analisis", "Cara_Guna", "Contoh"])


def build_cara_guna() -> pd.DataFrame:
    return pd.DataFrame([
        ("1", "Berita 3 negeri (percuma)", "python3 scripts/crawl_prn_chinese_news.py", "Output: crawls/PRN_Chinese_News_*.csv"),
        ("2", "Socmed InsightPulse", "./start_full_app.sh · project pas_break_2026 · query dari PRN_Chinese_Narrative_queries.txt", "dataset_size: 2000 · crawl S1/S2/S3 atau SX1"),
        ("3", "Direct URL", "Sheet SEEDS_DIRECT — filter Negeri · Prioriti=Tinggi", "Liew Chin Tong, DAP NS, Khoo Poay Tiong, dll."),
        ("4", "Analisis", "Asingkan ikut Negeri + Jenis_Suara (sheet ANALYSIS_RULES)", "Lapor 3 negeri berasingan, jangan campur"),
        ("5", "Banding negeri", "Guna query SX1/SX2 atau banding sheet KERUSI_BANDAR", "Contoh: NS krisis MB vs Johor stabil vs Melaka PH"),
        ("6", "Penamaan", "Kemaskini KERUSI_BANDAR — calon 2026 + URL FB", "Regenerate: python3 scripts/generate_prn_chinese_narrative_pack.py"),
    ], columns=["Langkah", "Apa", "Command / Tindakan", "Nota"])


def write_query_txt(queries: pd.DataFrame, path: Path, title: str) -> None:
    lines = [
        f"# {title}",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "# dataset_size: 2000 · project: pas_break_2026",
        "",
    ]
    for _, r in queries.iterrows():
        lines.append(f"## {r['ID']} — {r['Label']} [{r.get('Negeri', r['Platform'])}]")
        lines.append(f"# Jenis: {r['Jenis_Suara']} · Prioriti: {r['Prioriti_Analisis']}")
        lines.append(r["Query"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_guide(path: Path) -> None:
    path.write_text("""PRN CHINESE NARRATIVE — NS + MELAKA + JOHOR
==============================================

TUJUAN
  Analisis naratif komuniti Cina untuk 3 negeri PRN 2026.
  BUKAN polling — social listening + tag weight.

MULA (percuma)
  python3 scripts/crawl_prn_chinese_news.py
  python3 scripts/crawl_prn_chinese_news.py --negeri johor   # satu negeri

INSIGHTPULSE
  Query S1A1/S1B1 = Negeri Sembilan
  Query S2A1/S2B1 = Johor
  Query S3A1/S3B1 = Melaka
  Query SX1       = banding 3 negeri sekali

ANALISIS — WAJIB pisah negeri
  NS   → krisis MB, DUN bubar, PAS split
  Johor → bandar JB, DAP vs BN, MB Onn Hafiz
  Melaka → kerajaan PH, bandar heritage

Weight TINGGI = media_chinese + leader/adun_chinese
Weight RENDAH = proxy_about_chinese

FAIL
  reference/PRN_Chinese_Narrative_NS_Melaka_Johor.xlsx
  reference/PRN_Chinese_Narrative_queries.txt
""", encoding="utf-8")


def write_excel(path: Path, seeds, queries, kerusi, rules, cara, overview) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="NEGERI_OVERVIEW", index=False)
        cara.to_excel(writer, sheet_name="CARA_GUNA", index=False)
        seeds.to_excel(writer, sheet_name="SEEDS_DIRECT", index=False)
        queries.to_excel(writer, sheet_name="QUERIES", index=False)
        kerusi.to_excel(writer, sheet_name="KERUSI_BANDAR", index=False)
        rules.to_excel(writer, sheet_name="ANALYSIS_RULES", index=False)


def write_n9_legacy(seeds, queries, kerusi, rules, cara) -> None:
    """Backward-compatible NS-only files."""
    ns_seeds = seeds[seeds["Negeri"].isin(["Negeri Sembilan", "Semua"])]
    ns_kerusi = kerusi[kerusi["Negeri"] == "Negeri Sembilan"]
    ns_queries = queries[queries["ID"].str.startswith("S1") | queries["ID"].str.startswith("SX")]
    write_query_txt(ns_queries, OUT_N9_TXT, "N9 Chinese Narrative (subset of 3-negeri pack)")
    write_guide(OUT_N9_GUIDE)
    with pd.ExcelWriter(OUT_N9_XLSX, engine="openpyxl") as writer:
        cara.to_excel(writer, sheet_name="CARA_GUNA", index=False)
        ns_seeds.to_excel(writer, sheet_name="SEEDS_DIRECT", index=False)
        ns_queries.to_excel(writer, sheet_name="QUERIES", index=False)
        ns_kerusi.to_excel(writer, sheet_name="KERUSI_DAP", index=False)
        rules.to_excel(writer, sheet_name="ANALYSIS_RULES", index=False)


def main() -> None:
    REF.mkdir(parents=True, exist_ok=True)
    overview = build_negeri_overview()
    seeds = build_seeds_direct()
    queries = build_queries()
    kerusi = build_kerusi_bandar()
    rules = build_analysis_rules()
    cara = build_cara_guna()

    write_excel(OUT_XLSX, seeds, queries, kerusi, rules, cara, overview)
    write_query_txt(queries, OUT_TXT, "PRN Chinese Narrative — NS + Melaka + Johor")
    write_guide(OUT_GUIDE)
    write_n9_legacy(seeds, queries, kerusi, rules, cara)

    print(f"✅ Excel (3 negeri): {OUT_XLSX}")
    print(f"✅ Query:            {OUT_TXT}")
    print(f"✅ Guide:            {OUT_GUIDE}")
    print(f"✅ Legacy NS:        {OUT_N9_XLSX}")
    print(f"   Seeds: {len(seeds)} · Queries: {len(queries)} · Kerusi bandar: {len(kerusi)}")


if __name__ == "__main__":
    main()
