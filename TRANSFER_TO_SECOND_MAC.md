# InsightPulse — Panduan Pindah ke MacBook Kedua

Panduan ini untuk pindahkan app InsightPulse ke **Raja's MacBook Pro (2)** dan setup crawl **dua mesin serentak** dengan **API Apify yang sama**.

---

## 1. Buat fail ZIP (MacBook pertama — Mac anda sekarang)

```bash
cd ~/Documents/InsightPulse
chmod +x scripts/package_insightpulse_for_transfer.sh
./scripts/package_insightpulse_for_transfer.sh
```

Fail ZIP akan muncul di **Downloads**:
`InsightPulse_APP_Transfer_YYYYMMDD_HHMMSS.zip` (~80–150 MB)

**Apa yang disertakan:**
- Kod app (backend, frontend, scripts)
- Struktur projek `data/projects/` termasuk PRN N9 War Room
- `requirements.txt`, skrip start/stop
- `.env.example` (template — **bukan** API keys sebenar)

**Apa yang TIDAK disertakan (sengaja):**
- `.env` — API keys (Apify, OpenAI, dll.)
- `.venv` — virtual environment (buat semula di Mac kedua)
- `data/combined`, `data/analyzed` — CSV crawl besar (boleh crawl semula)

---

## 2. Hantar ke MacBook kedua

Pilih **satu** cara:

| Kaedah | Langkah |
|--------|---------|
| **AirDrop** | Finder → Downloads → klik kanan ZIP → Share → AirDrop → Raja's MacBook Pro (2) |
| **iCloud Drive** | Seret ZIP ke iCloud Drive → buka di Mac kedua |
| **USB / External drive** | Copy ZIP ke drive → plug ke Mac kedua |

**API keys (.env) — hantar BERASINGAN & SELAMAT:**
```bash
# Mac pertama — copy .env ke Desktop (jangan masuk zip)
cp ~/Documents/InsightPulse/.env ~/Desktop/InsightPulse_env_COPY.txt
```
Hantar `InsightPulse_env_COPY.txt` via AirDrop. **Padam selepas Mac kedua setup siap.**

---

## 3. Setup di Raja's MacBook Pro (2)

### 3.1 Extract ZIP
```bash
cd ~/Documents
unzip ~/Downloads/InsightPulse_APP_Transfer_*.zip -d InsightPulse
cd InsightPulse
```

### 3.2 Python & virtual environment
```bash
# Pastikan Python 3.10+ ada
python3 --version

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 API keys
```bash
cp .env.example .env
# Edit .env — paste APIFY_API_TOKEN & keys lain dari fail yang dihantar
nano .env
```

Minimum dalam `.env`:
```
APIFY_API_TOKEN=your_token_here
APIFY_PROXY_PASSWORD=your_proxy_password
```

### 3.4 Start InsightPulse
```bash
chmod +x start_insightpulse.sh stop_insightpulse.sh
./start_insightpulse.sh
```

Buka: **http://localhost:8001**

### 3.5 War Room Dashboard PRN N9 (optional)
```bash
cd data/projects/political/PRN/PRN_N9/reports/war_room/prototype
python3 -m http.server 8080
```
Buka: **http://localhost:8080**

---

## 4. Crawl serentak — DUA MacBook, SATU API Apify

### ✅ BOLEH — dengan syarat

Kedua-dua Mac **boleh guna APIFY_API_TOKEN yang sama** serentak. Apify urus run di cloud — setiap mesin hantar run berasingan.

| Aspek | Penjelasan |
|-------|------------|
| **Billing** | Semua run dari kedua Mac dicaj ke **akaun Apify yang sama** |
| **Concurrency** | Had bergantung plan Apify (Free ~25 CU/bulan, Paid lebih tinggi) |
| **Backend** | Setiap Mac ada server sendiri `localhost:8001` — **tiada konflik port** |
| **Data** | CSV simpan dalam folder InsightPulse **masing-masing Mac** |

### ✅ Cara terbaik — bahagikan kerja

| MacBook | Tugasan contoh |
|---------|----------------|
| **Mac 1 (utama)** | PRN N9 keywords K1–K3, poll Facebook, sync dashboard |
| **Mac 2 (Raja)** | PRN N9 keywords K4–K5, Shawn Loh / China Press, Johor crawl |

**Elak:** crawl **keyword + platform yang sama** pada kedua Mac pada masa yang sama → buang kredit Apify & data duplicate.

### ⚠️ Perhatian penting

1. **Monitor kredit Apify** — login [console.apify.com](https://console.apify.com) → Usage
2. **Jangan duplicate crawl** — guna senarai keyword berbeza per Mac
3. **Sync dashboard** — jalankan `python scripts/sync_n9_jobs_dashboard.py` pada **satu Mac sahaja** (Mac utama), kemudian copy folder `data/projects/political/PRN/PRN_N9/reports/war_room/prototype/data/` ke Mac lain jika perlu
4. **Port 8001** — jika dua Mac dalam rangkaian yang sama, mereka independent; tiada isu
5. **Plan Free Apify** — crawl serentak berat mungkin habiskan quota cepat; cadang **stagger** (Mac 1 pagi, Mac 2 petang) atau upgrade plan

### Contoh workflow harian

```
08:00  Mac 1 → crawl "Monarki Adat N9" (FB + TikTok)
08:00  Mac 2 → crawl "Shawn Loh China Press" (News + X)
       ↓ (serentak — keyword BERBEZA ✅)
10:00  Mac 1 → sync dashboard + review ML
10:30  Mac 2 → hantar CSV ke Mac 1 via AirDrop / shared folder
11:00  Mac 1 → merge + sync_n9_jobs_dashboard.py
```

---

## 5. Semak app berjalan

```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/projects
```

---

## 6. Troubleshooting

| Masalah | Penyelesaian |
|---------|--------------|
| `pip install` gagal | `xcode-select --install` kemudian cuba semula |
| Port 8001 sudah digunakan | `./stop_insightpulse.sh` atau `lsof -ti:8001 \| xargs kill -9` |
| Apify "Failed to fetch" | Backend masih proses — tunggu; refresh UI; semak `csv_api.log` |
| Dashboard tak update | Crawl UI ≠ War Room — jalankan `sync_n9_jobs_dashboard.py` |
| `.env` missing | Copy dari `.env.example` dan isi token |

---

## Ringkasan pantas

1. `./scripts/package_insightpulse_for_transfer.sh` → ZIP di Downloads
2. AirDrop/iCloud ke Raja's MacBook Pro (2)
3. Hantar `.env` secara berasingan (selamat)
4. Setup venv + `pip install -r requirements.txt`
5. Crawl serentak **OK** — bahagikan keyword, monitor kredit Apify
