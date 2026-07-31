# PRN — Pemantauan Naratif Berbahasa Cina

Dashboard ringkas untuk **Negeri Sembilan · Johor · Melaka**.

## Mula

```bash
cd n9_chinese_narrative_dashboard
.venv/bin/streamlit run app.py
```

## 5 Halaman Sahaja

| # | Halaman | Apa yang anda dapat |
|---|---------|---------------------|
| 1 | **Ringkasan** (home) | KPI, status HIJAU/MERAH, daerah, fakta, sentimen |
| 2 | **Isu & Tindakan** | 5 isu utama + papan tindakan P1/P2 |
| 3 | **Respons & Copy** | Kit copy BM/中文, platform, cara balas |
| 4 | **Kawasan & Risiko** | Daerah/DUN, risiko tinggi, URL bukti |
| 5 | **Data & Laporan** | Jadual hantaran + jana PDF/DOCX |

## Sidebar

- **Pilih negeri** (N9 / Johor / Melaka)
- **Penapis ringkas** (tarikh, platform, isu, sentimen)
- **Jana laporan** (Eksekutif + Kit Respons)

## Laporan

```bash
cd ..
python3 scripts/generate_prn_chinese_narrative_reports.py
```

Output: `data/projects/political/pas_break_2026/reports/chinese_narrative/`
