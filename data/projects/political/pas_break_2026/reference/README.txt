PAS Break 2026 — Reference & Crawl URL Lists
Generated: 2026-06-11 00:51

FILES:
  Politik_Malaysia_SocMed_2026.xlsx  — Direktori + sheet baru PRN Negeri
  crawl_urls_01_official_all.txt     — 82 akaun rasmi/pemimpin
  crawl_urls_02_pas_bersatu.txt      — 18 PAS + Bersatu (suara elit)
  crawl_urls_03_prn_negeri.txt       — 17 PRN NS/Johor/Melaka
  crawl_urls_04_viral_posts.txt      — 40 post viral (deep komen)
  crawl_url_master.csv               — Master gabungan

CARA GUNA (InsightPulse UI):
  1. Buka http://localhost:8001
  2. Mod Crawl → Direct URL Crawl
  3. Copy-paste URL dari fail .txt (satu URL per baris, abaikan baris #)
  4. Project: pas_break_2026
  5. Dataset: 2000-3000 (fokus komen)

CADANGAN URUTAN CRAWL:
  Crawl 3B (PAS+Bersatu) → suara elit post-split
  Crawl 3D (viral posts) → komen rakyat deep-dive
  Crawl 3E (NS only)     → fokus EXCO Negeri Sembilan
