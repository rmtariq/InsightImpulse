PRN JOHOR + N9 — CRAWL UPDATE KIT
==================================
Folder operasi di Desktop untuk kemaskini data InsightPulse → War Room

STRUKTUR
--------
  00_MULA_DI_SINI.txt          ← baca pertama
  01_jadual_crawl/             Jadual crawl 20 Jun → 1 Ogos
  02_keywords_calon/           Template calon + berita + backup
  03_url_batches_social/       URL paste Direct URL (Batch 1-6)
  04_settings/                 Setting InsightPulse standard
  05_selepas_crawl/            Combine master + update war room
  06_pautan/                   Link command centre + lokasi data
  09_naratif_cina_india/       Naratif Cina & India → Modul #6
      Johor/                   ← SCRIPT JOHOR (double-click .command)
  09_naratif_cina_india/Johor/
      RUN_JOHOR_PENUH.command  crawl penuh Johor + India
      RUN_JOHOR_PAGI.command   crawl pagi 3 negeri
      RUN_JOHOR_SEMAK.command  publish cepat (~30 saat)
      MULA_JOHOR.txt           baca pertama (Johor)

CARA KERJA
----------
  1. Ikut jadual dalam 01_jadual_crawl/
  2. Social → paste URL dari 03_url_batches_social/
  3. Berita → copy keyword dari 02_keywords_calon/NEWS_KEYWORDS_COPY_PASTE.txt
  4. Naratif Cina/India → 09_naratif_cina_india/ → ./scripts/update_narrative.sh pagi
  5. Selepas penamaan → isi template calon Johor/N9
  6. Selepas crawl → 05_selepas_crawl/ → refresh http://localhost:8080/

Salinan repo: /Users/rmtariq/Documents/InsightPulse/data/projects/political/PRN/_shared/PRN_Crawl_Update_Kit/
Dikemaskini: 22 Jun 2026
