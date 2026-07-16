# PRN Johor 2026 — 11 Calon PAS/PN · Master Crawl Plan
**Updated:** 8 Jul 2026, 11:30 PM (post Cikgu Mala success)

## Lessons dari N.05 Tenang (Cikgu Mala) ✅

| Cara | Hasil | Guna? |
|------|-------|-------|
| Keyword 4-platform + 7 hari + Multimodal | 85–299 rows, banyak noise | ❌ Jangan |
| Direct URL 2 profil TikTok | 51 posts, 100% relevan | ✅ Step 1 |
| Post URL Batch 15 viral | **2,503** (2,488 komen) | ✅ Step 2 (lepas ada URL viral) |
| Multimodal ON | Block backend 30+ min | ❌ OFF sentiasa |

## Settings Standard (SETIAP RUN)

```
Project:         PRN Johor 2026 — Internal · JITP 2026
Analysis Type:   Social Listening
Multimodal:      OFF (uncheck)
Platform:        TikTok sahaja (kecuali FB batch / Yuhanita IG)
Date:            30 Days (Direct URL) | No filter (Post URL Batch)
Dataset:         500
Comment:         Smart
```

---

## Coverage Semasa (8 Jul malam)

| DUN | Calon | Status | Priority |
|-----|-------|--------|----------|
| N05 Tenang | Normala / Cikgu Mala | ✅ DONE (~2,550) | HIGH |
| N15 Maharani | Anuar Hayan | ❌ ~15 hits | **CRITICAL** (80.8% PN) |
| N32 Endau | Hasnul Hakimi | ❌ ~14 hits | **CRITICAL** (65.5% PN) |
| N16 Sungai Balang | Ustaz Amin | ⚠️ ~36 | HIGH |
| N17 Semerah | Halim Kepol | ❌ ~9 | HIGH |
| N18 Sri Medan | Rosdi | ❌ ~8 | HIGH |
| N40 Tiram | Khirul | ❌ ~9 | HIGH |
| N35 Pasir Raja | Yuhanita | ⚠️ ~36 | HIGH |
| N02 Jementah | Saifullah | ⚠️ ~14 | LOW |
| N13 Simpang Jeram | Arshed | ⚠️ ~33 | LOW |
| N31 Kahang | Mazlan Bujang | ⚠️ ~13 | LOW |

---

## Urutan Disyorkan (10 calon baki)

### MALAM INI — Batch TikTok Direct URL (3+3+3+1)

**BATCH T1 — CRITICAL PN (~15 min)**
```
https://www.tiktok.com/@anuarhayan
https://www.tiktok.com/@hakimyhussien
https://www.tiktok.com/@ustazamin_n16
```
Crawl Mode: Direct URL | TikTok | 30 days

**BATCH T2 — HIGH PN (~15 min)**
```
https://www.tiktok.com/@halimkepol
https://www.tiktok.com/@ustaz.rosdi1
https://www.tiktok.com/@khirul.muntanazar
```

**BATCH T3 — Sedia ada data (~15 min)**
```
https://www.tiktok.com/@mazlan.bujang2
https://www.tiktok.com/@yuhanita.yunan
https://www.tiktok.com/@saif_abduh
```

**BATCH T4 — LOW priority (~10 min)**
```
https://www.tiktok.com/@awanganakjeram
```

Skip @normalasudirman — DONE.

---

### ESOK — Facebook Direct URL (1 batch, 90 hari)

Paste semua 11 FB URL dari `PAS_PN_11_FB_URLS.txt`
Crawl Mode: Direct URL | Facebook sahaja | 90 days

---

### ESOK — Keyword TikTok (1 calon = 1 run)

Guna query **ketat** (ikut template Cikgu Mala):

```
("<NAMA CALON>" OR "<nama panggilan>" OR "<DUN>") ("N.xx <DUN>" OR "PRN Johor")
```

**Jangan** guna `PAS OR PN` tanpa anchor — terlalu noise.

| DUN | Query |
|-----|-------|
| N15 | `("Anuar Hayan" OR "Mohamad Anuar" OR "Maharani") ("N15 Maharani" OR "PRN Johor")` |
| N32 | `("Hasnul Hakimi" OR "Hakimi Hussien" OR "Endau") ("N32 Endau" OR "PRN Johor")` |
| N16 | `("Ustaz Amin" OR "Muhammad Amin" OR "Sungai Balang") ("N16" OR "PRN Johor")` |
| N17 | `("Halim Kepol" OR "Semerah") ("N17 Semerah" OR "PRN Johor")` |
| N18 | `("Ahmad Rosdi" OR "Ustaz Rosdi" OR "Sri Medan") ("N18" OR "PRN Johor")` |
| N40 | `("Khirul Muntanazar" OR "Tiram") ("N40 Tiram" OR "PRN Johor")` |
| N02 | `("Saifullah Abdul Wahab" OR "Jementah") ("N02 Jementah" OR "PRN Johor")` |
| N13 | `("Arshed Yahya" OR "Awang Anak Jeram" OR "Simpang Jeram") ("N13" OR "PRN Johor")` |
| N31 | `("Mazlan Bujang" OR "Kahang") ("N31 Kahang" OR "PRN Johor")` |
| N35 | `("Yuhanita Yunan" OR "Pasir Raja") ("N35 Pasir Raja" OR "PRN Johor")` |

---

### Post URL Batch (per calon, lepas jumpa viral)

Selepas Direct URL / keyword, semak `top_posts_by_engagement.csv` → paste URL viral ke Post URL Batch (sama macam Cikgu Mala RUN 3).

---

## Masa Anggaran

| Fasa | Calon | Masa |
|------|-------|------|
| TikTok Direct URL (10 calon, 4 batch) | 10 | ~1 jam |
| FB Direct URL (11 calon, 1 batch) | 11 | ~20 min |
| Keyword TikTok (10 calon, 1-by-1) | 10 | ~3 jam |
| Post URL Batch (viral, pilihan) | ~5 calon | ~2 jam |
| **Total** | | **~6–7 jam** |

Boleh jalan semalaman — **1 batch = 1 Analyze**, jangan paste banyak query sekali.

---

## Checklist Lepas Setiap Calon

- [ ] Dashboard keluar (task completed)
- [ ] `data/combined/Combined_tiktok_*.csv` wujud
- [ ] `reports/*/dashboard.html` wujud
- [ ] Posts > 20 ATAU comments > 100 = OK
- [ ] Posts < 5 = buat keyword retry

---

## Fail Rujukan

- Registry: `PAS_PN_11_CALON_REGISTRY.csv`
- URL lists: `PAS_PN_11_FB_URLS.txt`, `PAS_PN_11_TIKTOK_URLS.txt`
- Kit lama: `PAS_PN_11_CALON_CRAWL_KIT.txt`
- Cikgu Mala template: `PAS_PN_11_NORMALA_DIRECT_POST_KIT.txt`
