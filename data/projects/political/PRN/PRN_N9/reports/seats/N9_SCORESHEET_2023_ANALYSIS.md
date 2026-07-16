# Analisis Helaian Mata SPR PRN 2023 (N9) — Cadangan Tambahan untuk PAS

Sumber: 36 Helaian Mata rasmi SPR (Borang SPR 760) PRN DUN N9 ke-15, cetak 12/08/2023.
Diproses: `scripts/parse_n9_scoresheets_2023.py` → totals + pecahan saluran ikut jenis kawasan.
Analisis muafakat: `scripts/analyze_n9_muafakat_2023.py`.

> **Nilai baru:** Buat pertama kali kita ada **undi sebenar setiap calon (termasuk PN/PAS) di SEMUA 36 DUN**,
> bukan sekadar pemenang + majoriti. Ini membolehkan kira **matematik muafakat sebenar (PN+BN vs PH)**
> dan **kebocoran ikut saluran** (Melayu vs Cina vs Ladang-India).

## 1. Realiti 13 kerusi MN (data rasmi, bukan model)

| DUN | Nama | Tier | Pegang 2023 | PN 2023 | Jurang/Maj | Muafakat vs PH | Verdikt data |
|-----|------|------|-------------|--------:|-----------:|---------------:|--------------|
| N25 | Paroi | wajib | **PN (PAS)** | 23,840 | +5,539 | — | Pertahan selesa |
| N31 | Bagan Pinang | wajib | **PN (PAS)** | 10,921 | +3,426 | — | Pertahan selesa |
| N34 | Gemas | wajib | **PN (Bersatu)** | 11,653 | +3,120 | — | Pertahan selesa |
| N20 | Labu | wajib | **PN (Bersatu)** | 11,661 | +1,640 | — | Pertahan (waspada) |
| N05 | Serting | wajib | **PN (PAS)** | 10,312 | **+843** | — | Pertahan TIPIS ⚠ |
| N14 | Ampangan | wajib | PH (PKR) | 5,725 | −329 | **+2,750** | **FLIP KUAT** ✅ |
| N18 | Pilah | wajib | PH (PKR) | 5,143 | −1,079 | −1,079 | Sukar (swing ~540) |
| N04 | Klawang | wajib | PH (Amanah) | 4,021 | −577 | **−213** | Sukar (hampir seri) |
| N13 | Sikamat | wajib | PH (PKR/MB) | 10,068 | −2,662 | −2,662 | Sangat sukar |
| N01 | Chennah | berhasrat | PH (DAP) | 3,688 | −2,200 | −2,200 | Sangat sukar |
| N33 | Sri Tanjung | berhasrat | PH (PKR) | 4,243 | −3,996 | −3,996 | Sangat sukar |
| N36 | Repah | berhasrat | PH (DAP) | 0* | −5,950 | −5,950 | PN tak tanding 2023 |
| N10 | Nilai | berhasrat | PH (DAP) | 8,244 | −10,889 | −9,459 | Hampir mustahil |

\* Repah 2023 = DAP vs MCA (tiada calon PN).

**Implikasi utama:**
- Hanya **1 kerusi PH** yang muafakat (PN+BN) benar-benar menang atas kertas: **N14 Ampangan (+2,750)**.
- **N04 Klawang** hampir seri (−213) — bergantung pada undi ladang India.
- **N18 Pilah** perlu swing ~540 undi (realistik dgn gerak kerja padat).
- **N13 Sikamat, N01 Chennah** = sangat sukar; **N33, N36, N10** = stretch jauh.
- **N05 Serting** menang hanya **843** — kerusi PAS paling terancam, perlu pertahanan agresif.

## 2. Kebocoran ikut jenis kawasan (punca kekalahan PN)

Pecahan saluran menunjukkan PN bocor besar di **saluran Ladang/Tamil (India)** dan **Cina**:

- **N33 Sri Tanjung:** Ladang-India → PH 3,112 vs PN 886 (jurang 2,226 ≈ seluruh majoriti 3,996). Kemenangan PH datang dari estet.
- **N04 Klawang:** Ladang-India → PH 2,082 vs PN 1,051; Melayu pun bocor (PH 2,795 vs PN 2,366).
- **N05 Serting:** Cina → BN 2,096 vs PN 514 (kini BN rakan muafakat — undi ini sepatutnya kekal).
- **N36 Repah:** walaupun saluran Melayu, DAP menang 8,434 vs 4,034 — kubu DAP merentas kaum.

## 3. Cadangan tambahan untuk PAS N9

### A. Penjajaran semula tier (ikut data rasmi, bukan model optimis)
1. **Pertahan keutamaan #1 → N05 Serting (+843)** — kerusi PAS paling tipis. Jangan ambil mudah.
2. **Sasaran flip realistik tunggal → N14 Ampangan** — satu-satunya kerusi PH yang muafakat menang atas kertas (+2,750). Jadikan kerusi “mesti menang” MN.
3. **Swing achievable → N18 Pilah (−1,079), N04 Klawang (−213)** — letak dalam “boleh menang dgn usaha”, bukan “wajib menang”.
4. **Turunkan jangkaan → N13 Sikamat, N01 Chennah, N33, N36, N10** — kekal tanding (politik/nafas), tetapi sumber kempen jangan dibazir di sini; ia stretch.

### B. Strategi lapangan berdasarkan saluran
- **Tutup kebocoran estet (Klawang, Sri Tanjung):** program khusus pekebun/ladang India melalui rakan BN/komponen — tanpa undi estet, flip mustahil.
- **Kunci undi Cina muafakat (Serting):** undi Cina 2023 pergi BN; pastikan mesin BN bawa undi ini ke calon muafakat, bukan tinggal di rumah.
- **GOTV Melayu fokus saluran:** di Pilah & Sikamat, sasarkan saluran Melayu yang turnout rendah; setiap 1% turnout Melayu ≈ ratusan undi.

### C. Tambahan ke dashboard / deck (boleh saya laksanakan)
- Tambah lapisan **“Baseline PN 2023 (rasmi)”** + **“Muafakat vs PH”** ke setiap kad DUN (gantikan anggaran model dgn nombor SPR sebenar).
- Tambah **indikator kebocoran kawasan** (Melayu/Cina/India) per DUN di drawer.
- Selaraskan **win-probability model** supaya tidak melebih-lebih kerusi stretch (N10/N33/N36).

## Fail output
- `reports/seats/n9_scoresheet_2023.csv` — ringkasan rasmi 36 DUN (turnout, undi calon, majoriti, undi rosak).
- `reports/seats/n9_scoresheet_streams_2023.json` — pecahan saluran + jenis kawasan.
- `reports/seats/n9_mn13_muafakat_2023.csv` — matematik muafakat 13 kerusi MN.
