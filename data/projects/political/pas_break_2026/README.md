# PAS Break 2026 · PRN Negeri Sembilan — Data & Dashboard

**Projek:** `data/projects/political/pas_break_2026/`  
**Dashboard:** `reports/prn-negeri-sembilan-dashboard.html`  
**Regenerate:** `python3 scripts/generate_prn_n9_dashboard.py` (NEImpulse venv)  
**Full refresh:** `bash scripts/run_prn_n9_data_refresh.sh`

---

## Folder structure

```
pas_break_2026/
├── crawls/                    Raw CSV — setiap crawl = fail baru (timestamp)
├── reference/                 JSON ringkasan — dashboard baca ini
│   └── templates/             CSV templates (PapaParse / InsightPulse future)
├── master/                    Master PAS-Break digabung + analyzed
├── reports/                   Dashboard HTML, seat JSON/CSV, pas_break data
└── reference/crawl_batches/   Keyword lists crawl manual
```

---

## Dashboard sections (sidebar)

| # | Seksyen | Sumber data |
|---|---------|-------------|
| 1 | Gambaran Keseluruhan | Kerusi baseline, SME, BNM, Coalition Watch |
| 2 | Kerusi DUN | Excel SPR + kategori PAS + ramalan |
| 3 | Analitik & Ramalan | Seat analytics + ADUN crawl |
| 4 | **Scenario Engine** | S1–S5 mock + verified facts (PapaParse-ready) |
| 5 | Senario Pakatan | Model analis (legacy panel) |
| 6 | Sentimen & Naratif | PAS-Break JSON + news |
| 7 | Profil Kawasan | 8 priority seats |
| 8 | Unjuran PRN | Model analis |
| 9 | Data & Sumber | Registry semua sumber |

**Shortcut:** Alt+1 … Alt+9

---

## Data → Dashboard wiring

| Sumber | Fail | Dashboard? | Seksyen |
|--------|------|:----------:|---------|
| Excel SPR 36 kerusi | `JITP_2026/Master_File/PRN2023_NegeriSembilan_v2.xlsx` | ✅ | Kerusi, Analitik, Overview |
| Seat analytics + ramalan | `reports/n9_seats_export.json` | ✅ | Analitik, Kerusi DUN, drawer |
| **Scenario Engine S1–S5** | `scripts/n9_scenario_engine.py` → embed HTML | ✅ | **Scenario Engine** |
| Verified facts (PAS split) | Inline mock JS | ✅ | Scenario Engine |
| CSV templates | `reference/templates/*.csv` | 🔜 | PapaParse hook (future live load) |
| BNM OPR & FX | `reference/economic_n9.json` | ✅ | Ekonomi Outlook |
| SME persepsi ekonomi | `data/projects/sme/smebank/master/SMEBank_Master_*.csv` | ✅ | Ekonomi Outlook |
| Berita PRN NS | `reference/prn_n9_news_summary.json` | ⚠️ | Tab Media |
| ADUN seed crawl | `reference/prn_n9_adun_social_summary.json` | ✅ | Analitik, drawer |
| PAS-Break NS | `reports/pas_break_dashboard_data.json` | ✅ | Sentimen (222 posts) |
| Trend volume 30 hari | Mock | ❌ | Sentimen chart |
| Raw CSV crawls | `crawls/PRN_N9_*.csv` | ❌ | Audit sahaja |
| InsightPulse async | `crawls/pas_break_social_*.csv` | ❌ | Perlu merge manual |
| Export CSV/PNG/PDF | — | ❌ | Placeholder |

**Legend:** ✅ live · ⚠️ partial · 🔜 hooks ready · ❌ not wired

---

## Scenario Engine module

**Kod:** `scripts/n9_scenario_engine.py` (injected into HTML at generate time)

| Komponen | Kandungan |
|----------|-----------|
| **Verified Facts** | PAS putus Bersatu, Bersatu N9 kekal PN, logo PAS belum final, UMNO tiada MN 2.0 |
| **S1–S5** | PN berfungsi, Solo, PAS-UMNO taktikal, Clash, Fragmentasi |
| **Labels** | Verified Fact · Operational Ambiguity · Analytical Scenario |
| **UI** | Filter tabs, cards, heat matrix, 4 charts, transitions, monitor checklist |
| **CSV hooks** | `loadCsvText`, `parseCsv`, `mapScenarioCsvRows`, `hydrateScenarioEngineFromCsv` |

**CSV templates (future PapaParse load):**
```
reference/templates/scenario_input_template.csv
reference/templates/seat_features_template.csv
reference/templates/event_log_template.csv
reference/templates/raw_posts_template.csv      (placeholder — add when ready)
reference/templates/raw_comments_template.csv
reference/templates/news_crawl_template.csv
reference/templates/youtube_podcast_template.csv
reference/templates/economic_indicators_template.csv
reference/templates/model_training_template.csv
```

---

## Crawl outputs (by script)

| Skrip | Raw CSV | Summary JSON |
|-------|---------|--------------|
| `scripts/n9_seat_analytics.py` | — | `reports/n9_seats_export.json`, `n9_seats_analytics.*` |
| `scripts/pull_economic_n9.py` | — | `reference/economic_n9.json` |
| `scripts/crawl_prn_n9_news.py` | `crawls/PRN_N9_News_*.csv` | `reference/prn_n9_news_summary.json` |
| `scripts/crawl_prn_n9_adun_seeds.py` | `crawls/PRN_N9_ADUN_Seeds_*.csv` | `reference/prn_n9_adun_social_summary.json` |
| `scripts/generate_prn_n9_dashboard.py` | — | `reports/prn-negeri-sembilan-dashboard.html` |

Dashboard embed data at **generate time** — wajib jalankan generator selepas crawl.

---

## Quick commands

```bash
source NEImpulse/bin/activate
cd /Users/rmtariq/Documents/InsightPulse

bash scripts/run_prn_n9_data_refresh.sh

# atau step by step
python3 scripts/n9_seat_analytics.py
python3 scripts/pull_economic_n9.py
python3 scripts/crawl_prn_n9_news.py
python3 scripts/crawl_prn_n9_adun_seeds.py
python3 scripts/generate_prn_n9_dashboard.py
```

**Buka:** `reports/prn-negeri-sembilan-dashboard.html` → sidebar **Scenario Engine** (Cmd+Shift+R)

---

## Nota penting

1. **HTML = snapshot** (~200 KB) — data dibake semasa generate, bukan live API.
2. **Scenario Engine** — semua output dilabel **Analytical Scenario** kecuali verified facts; bukan polling.
3. **Calon 2023 ≠ 2026** — update selepas SPR penamaan.
4. **CSV live load** — hooks sedia; panggil `hydrateScenarioEngineFromCsv()` bila serve via HTTP (file:// block fetch).

*Kemas kini: Jun 2026 — Scenario Engine S1–S5*
