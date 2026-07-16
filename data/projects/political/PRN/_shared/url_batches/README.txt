PRN Johor + N9 — URL Crawl Batches
================================
Source: PRN_JOHOR_N9_FULL_URLS_COPY_PASTE.txt
Generated: 2026-06-21 10:19
Total URLs split: 513

CARA GUNA (InsightPulse http://localhost:8001)
----------------------------------------------
1. Mod: Direct URL Crawl
2. Paste isi fail .txt (URL sahaja, abaikan baris #)
3. Date Range: Last 7 Days
4. Dataset Size: 1000 (batch kecil) atau 2000 (batch besar)
5. Analysis Type: Social Listening
6. Project: pas_break_2026 (atau projek PRN anda)

URUTAN DISYORKAN
----------------
  1. 01_parti_rasmi_pemimpin.txt (74 URL) — Parti rasmi + pemimpin (FB/IG/TikTok/X/Threads)
  2. 02_search_hashtag_queries.txt (189 URL) — Search / hashtag / YouTube results queries
  3. 03_facebook_profil_halaman_kumpulan.txt (122 URL) — Facebook profil, ADUN, halaman, kumpulan
  4. 04_instagram_tiktok_x_profil.txt (76 URL) — Instagram + TikTok @ + X profil (bukan search)
  5. 05_youtube_threads.txt (13 URL) — YouTube saluran + baki YouTube/Threads
  6. 06_BONUS_berita_guna_keyword_mode.txt (39 URL) — Portal berita — guna Keyword+News, BUKAN Direct URL ← guna Keyword Search + platform News
  7. 08_cula_seed_36dun_N9_PASTE_ONLY.txt — pointer ke folder cula_seeds_N9/ (36 fail, satu per DUN)

CULA DIGITAL — 36 DUN N9 (sentiment + sokongan tempatan)
---------------------------------------------------------
  Setiap kerusi ada fail sendiri:
    url_batches/cula_seeds_N9/N01_Chennah_PASTE_ONLY.txt … N36_Repah_PASTE_ONLY.txt

  Fasa 1 — Seed (manual, RM0, semua 36 DUN):
    Post santai di kumpulan FB tempatan setiap DUN. Gaya berbeza ikut kerusi.
    Contoh N10: "agaknya di Nilai ni PAS menang ok ke?"
    Contoh N25: "area Paroi — BN ke PAS ke PH yg lebih sesuai kali ni?"
    Biar 2–3 hari.

  Fasa 2 — Kumpul URL post ke fail Nxx masing-masing (bukan profil).

  Fasa 3 — Crawl:
    python3 scripts/crawl_cula_seed_batches_n9.py --all-filled
    (atau --code N10 untuk satu kerusi)

  Fasa 4 — War room:
    merge_prn_johor_n9_master.py → build_warroom_production_bundle.py
    → sentiment + emotion + sokongan per DUN dalam dashboard

  Jana/refresh template:
    python3 scripts/generate_cula_seed_batches_n9.py

NOTA PENTING
------------
- Batch 2 (search/hashtag): kadang kurang stabil di Direct URL — OK untuk cuba, backup guna Keyword mode
- Batch 6 berita: Direct URL TIDAK disokong — crawl berita via Keyword + tick News
- Jangan paste semua batch serentak — satu batch, tunggu siap, baru batch seterusnya
- Anggaran masa: 15-45 min per batch (bergantung saiz & platform)

LOKASI FAIL
-----------
/Users/rmtariq/Documents/InsightPulse/data/projects/political/PRN/_shared/url_batches
