# PRN N9 War Room — Pelaksanaan Fasa A–E

**Versi:** 1.0 · **12 Jun 2026**  
**Dashboard:** `data/projects/political/pas_break_2026/reports/prn-negeri-sembilan-dashboard.html`  
**Tab baru:** **War Room Tindakan** (sidebar)

---

## Ringkasan

| Fasa | Apa | Status |
|------|-----|--------|
| **A** | Playbook rule-based ikut kategori kerusi | ✅ 198 tindakan |
| **B** | Status tindakan + export CSV + drawer kerusi | ✅ localStorage + CSV |
| **C** | Trigger crawl (sentiment, marginal, 3 penjuru) | ✅ auto dari master |
| **D** | Briefing mingguan (RAG/LLM + fallback rule) | ✅ tab Briefing |
| **E** | Agent queue — cadangan menunggu kelulusan | ✅ Luluskan/Tolak |

---

## Fail Utama

| Fail | Fungsi |
|------|--------|
| `scripts/n9_war_room.py` | Jana playbook, trigger, briefing, agent queue |
| `scripts/n9_war_room_dashboard.js` | UI tab War Room |
| `scripts/generate_prn_n9_dashboard.py` | Integrasi + regenerate HTML |
| `reports/n9_war_room.json` | Payload penuh untuk dashboard |
| `reports/n9_war_room_briefing.json` | Briefing mingguan |
| `Master_File/n9_war_room_actions.csv` | Export spreadsheet |

---

## Regenerate

```bash
cd /Users/rmtariq/Documents/InsightPulse
NEImpulse/bin/python scripts/n9_war_room.py
NEImpulse/bin/python scripts/generate_prn_n9_dashboard.py
```

---

## Kategori Kerusi → Playbook

| Kategori | Kerusi | Sumber operasi |
|----------|--------|----------------|
| **Pertahan** | N05, N25, N31 | Digital harian + lapangan + intel 2×/hari |
| **Boleh Menang** | N03, N09, N18 | Ceramah + door-to-door + target swing undi |
| **Sukar** | 6 kerusi | Selective strike — minimum budget |
| **Bukan Fokus** | 24 kerusi | Intel passive sahaja |

---

## Tab War Room — 4 Panel

1. **Playbook Tindakan** — filter kategori/jenis · tandakan status · export CSV  
2. **Isyarat Crawl** — alert sentiment / marginal / 3 penjuru  
3. **Briefing Mingguan** — executive summary + digital/lapangan/intel  
4. **Agent Queue** — cadangan agent · **Luluskan/Tolak** (tiada post automatik)

Status tindakan & kelulusan agent disimpan dalam **localStorage** browser.

---

## LLM (Fasa D)

- Jika `OPENAI_API_KEY` wujud → briefing dijana LLM dengan context kerusi + trigger  
- Jika tiada → fallback template rule-based (sama tab, label `rule_based`)

---

## Prinsip Operasi

1. **Human-in-the-loop** — agent tidak post socmed automatik  
2. **Pisah intel vs operasi** — tab Sentimen = baca; War Room = buat  
3. **Bukan polling** — `pasWinProb` kekal rule-based  
4. Kemaskini playbook selepas **penamaan calon SPR**

---

## Langkah Seterusnya (optional)

- [ ] Sync status tindakan ke server / Google Sheet  
- [ ] Cron regenerate war room 2×/hari semasa kempen  
- [ ] Wire API `/api/prn/n9/war-room` untuk multi-user  
- [ ] Clone modul ke Johor & Melaka dashboard
