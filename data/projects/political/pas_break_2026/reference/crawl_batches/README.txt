PAS Break 2026 — Crawl Batch Files (Fasa 1 Discovery)
Generated: 2026-06-11 08:33
Source: Politik_Malaysia_SocMed_2026_v3 — 33 pemimpin, 86 URLs

URUTAN DISYORKAN:
  1. BATCH_1A_TikTok_ALL_16.txt        ← MULA DI SINI (paling reliable)
  2. BATCH_1B_X_ALL_25.txt
  3. BATCH_1C_Facebook_part1..7.txt    ← 5 URL pada satu masa
  4. BATCH_1D_Instagram_ALL_13.txt
  5. BATCH_1E_PRN_Negeri (optional)

QUICK TEST (jika nak cuba dulu):
  BATCH_0_QUICK_PN_PH_BN_TikTok.txt

SETTING UI (setiap batch):
  Mod: Direct URL Crawl
  Platform: TICK SATU SAHAJA (match batch name)
  Dataset: 1,500
  Date: Last 7 Days
  Project: pas_break_2026

SELEPAS BATCH 1A (16 pemimpin — DONE, 3,703 rows):
  Filter post 9-11 Jun (split/solo/MN/PRN)
  → Fasa 2: deep crawl post URL (komen)

FASA 1B — TikTok Media + Influencer + Extra PN (34 URLs, BARU):
  Mod: Direct URL Crawl | TikTok only | Dataset 1,200–1,500 | Last 7 Days

  Pilihan A — satu paste (disyorkan jika backend stabil):
    BATCH_2A_TikTok_ALL_34_CLEAN_paste.txt

  Pilihan B — pecah 3 batch (jika timeout / dataset cap):
    1. BATCH_2A_TikTok_Media_14.txt      (17 media — MG, Sinar, AWANI, Utusan, dll.)
    2. BATCH_2B_TikTok_Influencer_11.txt (11 influencer — Indera Shafri, JPS, dll.)
    3. BATCH_2C_TikTok_Leaders_PN_6.txt  (6 extra — Muhyiddin, PAS Johor, dll.)

  Fasa 1C — volume rakyat (keyword):
    BATCH_2E_TikTok_Keywords.txt

  Fasa 2 — komen dalam video viral (post URL, bukan profile):
    BATCH_2D_TikTok_Viral_Videos_28.txt  (33 video URLs)

  RETRY — 24 profile yang timeout dalam crawl 155933:
    BATCH_2F_TikTok_MISSING_24_RETRY.txt  (Malaysia Gazette, Sinar, Indera Shafri, dll.)

  Manifest: BATCH_2_TikTok_manifest.csv

  PENTING: Restart backend selepas timeout fix — timeout kini kira
  bilangan profile × video × komen (bukan satu field sahaja).

FILES:
  BATCH_0_QUICK_PN_PH_BN_TikTok.txt
  BATCH_1A_TikTok_ALL_16.txt
  BATCH_1A_TikTok_manifest.csv
  BATCH_1B_X_ALL_25.txt
  BATCH_1B_X_manifest.csv
  BATCH_1C_Facebook_ALL_32.txt
  BATCH_1C_Facebook_manifest.csv
  BATCH_1C_Facebook_part1_manifest.csv
  BATCH_1C_Facebook_part1_of_7.txt
  BATCH_1C_Facebook_part2_manifest.csv
  BATCH_1C_Facebook_part2_of_7.txt
  BATCH_1C_Facebook_part3_manifest.csv
  BATCH_1C_Facebook_part3_of_7.txt
  BATCH_1C_Facebook_part4_manifest.csv
  BATCH_1C_Facebook_part4_of_7.txt
  BATCH_1C_Facebook_part5_manifest.csv
  BATCH_1C_Facebook_part5_of_7.txt
  BATCH_1C_Facebook_part6_manifest.csv
  BATCH_1C_Facebook_part6_of_7.txt
  BATCH_1C_Facebook_part7_manifest.csv
  BATCH_1C_Facebook_part7_of_7.txt
  BATCH_1D_Instagram_ALL_13.txt
  BATCH_1D_Instagram_manifest.csv
  BATCH_1E_PRN_Negeri_NS_Johor_Melaka.txt
  BATCH_2A_TikTok_ALL_34_CLEAN_paste.txt
  BATCH_2A_TikTok_Media_14.txt
  BATCH_2B_TikTok_Influencer_11.txt
  BATCH_2C_TikTok_Leaders_PN_6.txt
  BATCH_2D_TikTok_Viral_Videos_28.txt
  BATCH_2E_TikTok_Keywords.txt
  BATCH_2F_TikTok_MISSING_24_RETRY.txt
  BATCH_2_TikTok_manifest.csv

EXCO CRAWL (ikut urutan BATCH — senang):
  BATCH_EXCO_MINIMUM_3runs.txt          ← JADUAL 4 RUN — MULA DI SINI
  BATCH_1B_X_CLEAN_paste.txt              Run 1: X (1B)
  BATCH_1E_Facebook_NS_5_CLEAN_paste.txt  Run 2: FB NS (1E pecah 5)
  BATCH_1C_Facebook_part5_CLEAN_paste.txt Run 3: FB Part 5
  BATCH_1D_Instagram_CLEAN_paste.txt      Run 4: Instagram (1D)
  BATCH_1E_Facebook_Johor_5_CLEAN_paste.txt   Optional: Johor
  BATCH_1E_Facebook_Melaka_3_CLEAN_paste.txt  Optional: Melaka
