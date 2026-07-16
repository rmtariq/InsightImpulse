# PRN N9 — TUGASAN HARIAN ANDA (Step 1 → Dashboard)

**Masa total:** ~20–30 min/hari (pre-penamaan) · ~45 min/hari (kempen penuh)

---

## STEP 1 — Buka terminal (folder projek)

```bash
cd /Users/rmtariq/Documents/InsightPulse
```

---

## STEP 2 — Crawl BERITA (percuma, tanpa app)

**Pilihan A — BM + PRN asas (~5 min):**
```bash
NEImpulse/bin/python scripts/crawl_prn_n9_news.py
```

**Pilihan B — BM + Cina + Tamil + Ekonomi (~10 min):**
```bash
NEImpulse/bin/python scripts/crawl_prn_n9_news_multilingual.py
```

Query siap dalam: `reference/PRN_N9_NEWS_QUERIES_SIAP_GUNA.txt`

---

## STEP 3 — Crawl SOCMED (app InsightPulse) — 2× seminggu pre-penamaan, 1×/hari kempen

```bash
./start_full_app.sh
```

1. Browser → InsightPulse UI  
2. Project: **pas_break_2026**  
3. Paste **1 query** dari: `reference/PRN_N9_SOCMED_QUERIES_SIAP_GUNA.txt`  
4. Platform: `news, facebook, x, tiktok` (ikut query)  
5. **dataset_size: 2000**  
6. Klik crawl → tunggu siap  

Query ikut **DUN + kawasan + isu lokal** — rotate 6 kerusi kritikal.

---

## STEP 4 — Merge data ke master (jika ada crawl socmed baru)

```bash
NEImpulse/bin/python scripts/merge_exco_incremental.py
```

*(Langkau jika hanya crawl berita script hari ini)*

---

## STEP 5 — Refresh War Room + Dashboard

**Satu command (semua sekali):**
```bash
bash scripts/run_prn_n9_daily.sh
```

**Atau manual:**
```bash
NEImpulse/bin/python scripts/n9_war_room.py
NEImpulse/bin/python scripts/generate_prn_n9_dashboard.py
```

---

## STEP 6 — Buka dashboard

Fail:
`data/projects/political/pas_break_2026/reports/prn-negeri-sembilan-dashboard.html`

Tab **「Hari Ini」**:
- 6 tindakan kerusi  
- Tick siap  
- **Copy ke WhatsApp**

---

## STEP 7 — Hantar WhatsApp ke koordinator petugas

**Tiada daftar nombor / bot.**

1. Klik **Copy ke WhatsApp** (atau buka `reports/n9_hari_ini_whatsapp.txt`)  
2. Paste ke chat **Koordinator Petugas** (WhatsApp Web/phone)  
3. Koordinator forward ke group N05, N25, N09, dll.  
4. Template lengkap: `reference/PRN_N9_WHATSAPP_TEMPLATES.txt`  

Petugas reply **DONE** bila siap.

---

## JADUAL RINGKAS

| Hari | Anda buat |
|------|-----------|
| **Isnin** | Berita multilingual + regenerate + WhatsApp |
| **Selasa** | Socmed app — query umum NS |
| **Rabu** | Regenerate + WhatsApp |
| **Khamis** | Berita + socmed 1 kerusi |
| **Jumaat** | Regenerate + template strategi mingguan |
| **Sabtu/Ahad** | Socmed kerusi Boleh Menang |

**Selepas penamaan 18 Jul:** Step 2 + 3 + 5 + 7 **setiap hari**.
