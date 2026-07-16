# PRN Negeri Sembilan · Johor · Melaka

**Root:** `data/projects/political/PRN/`

Struktur sistematik — setiap negeri ada folder sendiri, senang cari dan selenggara.

---

## Struktur folder

```
PRN/
├── _registry.json              # Indeks semua negeri
├── _shared/                    # Sumber merentasi negeri
│   ├── spr/                    # Tarikh SPR (penamaan, undi)
│   ├── templates/              # CSV templates
│   └── chinese_narrative/      # Pack berita Cina 3 negeri
│
├── PRN_N9/                     # ★ Negeri Sembilan (36 DUN)
│   ├── metadata.json
│   ├── crawls/
│   │   ├── news/               # PRN_N9_News_Multilingual_*.csv
│   │   ├── news_analyzed/      # Tier A ML sentiment
│   │   ├── chinese_news/       # Berita Cina (filter NS)
│   │   ├── adun_seeds/         # Crawl seed ADUN
│   │   └── archive/            # Fail lama
│   ├── reference/
│   │   ├── queries/            # Query siap guna (socmed, berita)
│   │   ├── seeds/              # Excel narrative seeds
│   │   └── *.json              # Ringkasan crawl/analyze
│   ├── reports/
│   │   ├── dashboards/         # prn-negeri-sembilan-dashboard.html
│   │   ├── war_room/           # JSON + WhatsApp digest
│   │   └── seats/              # Analitik 36 kerusi SPR
│   └── master/                 # Master negeri-specific
│
├── PRN_Johor/                  # Johor (56 DUN)
│   ├── crawls/
│   ├── reference/
│   ├── reports/
│   └── master/
│
└── PRN_Melaka/                 # Melaka (28 DUN)
    └── (skeleton — siap untuk crawl)
```

---

## Narrative merentasi negeri (berasingan)

**PAS-Break / PN split** — bukan data negeri sahaja:

```
data/projects/political/pas_break_2026/
├── master/          # Socmed master FB/TikTok/X (3 negeri)
├── crawls/          # Crawl cross-state
└── reports/         # PAS Break dashboard
```

---

## Command harian (N9)

```bash
bash scripts/run_prn_n9_daily.sh
```

Output ke `PRN/PRN_N9/` — bukan `pas_break_2026/`.

---

## Path dalam kod

Semua skrip guna **`scripts/prn_paths.py`**:

```python
from prn_paths import prn_dir, crawls, reference, reports

crawls("N9", "news")           # .../PRN_N9/crawls/news/
reference("N9")                # .../PRN_N9/reference/
reports("N9") / "dashboards"   # .../PRN_N9/reports/dashboards/
```

---

## Migrasi (sekali sahaja)

```bash
NEImpulse/bin/python scripts/migrate_prn_folder_structure.py --dry-run
NEImpulse/bin/python scripts/migrate_prn_folder_structure.py
```

---

## Cari fail dengan cepat

| Apa | Di mana |
|-----|---------|
| Crawl berita latest | `PRN_N9/crawls/news/PRN_N9_News_Multilingual_*.csv` |
| Analyzed Tier A | `PRN_N9/crawls/news_analyzed/` |
| Dashboard HTML | `PRN_N9/reports/dashboards/prn-negeri-sembilan-dashboard.html` |
| War Room | `PRN_N9/reports/war_room/n9_war_room.json` |
| Kerusi 36 DUN | `PRN_N9/reports/seats/n9_seats_analytics.csv` |
| Query socmed | `PRN_N9/reference/queries/PRN_N9_SOCMED_QUERIES_SIAP_GUNA.txt` |
| Tarikh SPR | `PRN/_shared/spr/spr_prn_dates_2026.json` |
| Socmed PAS-Break | `pas_break_2026/master/` |
