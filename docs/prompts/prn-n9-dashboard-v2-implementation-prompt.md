# Cursor Prompt — PRN Negeri Sembilan War Room Dashboard V2.0

## Tujuan
Bina semula dan naik taraf dashboard PRN Negeri Sembilan sebagai **War Room Dashboard V2.0** yang lengkap, mudah digunakan, mudah difahami, dan terus boleh memandu tindakan harian.

Matlamat utama sistem ini bukan sekadar memaparkan analytics, tetapi menjawab tiga soalan:

1. Apa yang sedang berlaku?
2. Kenapa ini penting?
3. Apa yang perlu dibuat sekarang?

Keutamaan produk:

- Mudah isi data.
- Mudah baca dashboard.
- Mudah ambil tindakan.
- Stabil, modular, dan mudah disambung ke backend sebenar.
- Bahasa Melayu ringkas, jelas, dan tidak teknikal pada UI pengguna.

## Prinsip Produk
Patuh kepada prinsip berikut dalam semua modul:

- Simple on the surface, powerful underneath.
- Satu skrin utama mesti boleh difahami dalam 10-15 saat.
- Setiap insight mesti membawa kepada keputusan atau tindakan.
- Setiap alert mesti ada tindakan, owner, due date, dan status.
- Jangan tambah chart jika chart itu tidak membantu keputusan.
- Jangan tonjolkan istilah teknikal seperti RAG, vector DB, orchestration, atau semantic inference pada UI biasa.
- Kompleksiti sistem berada di belakang tabir.
- Dashboard mesti mobile-friendly untuk petugas lapangan.

Gunakan copy BM mudah seperti:

- Apa yang berlaku
- Kenapa ini penting
- Apa yang perlu dibuat sekarang
- Siapa bertanggungjawab
- Tindakan disyorkan
- Data terakhir dikemas kini
- Perlu semakan semula

## Arahan Penting: Kekalkan Asas Sedia Ada
Dashboard V2.0 mesti dibina atas asas dashboard PRN Negeri Sembilan sedia ada. Jangan rebuild dari kosong kecuali benar-benar perlu.

Wajib dikekalkan:

- Visual identity semasa: dark theme InsightPulse, layout war room, kad KPI, panel, drawer kanan.
- Command Centre sebagai skrin strategik sahaja.
- Panel senario N9: PAS Solo, PAS+MN, UMNO Solo, PH, path to majority.
- DUN Drill-Down: peta 36 DUN, grid kerusi, seat drawer, status seat, action/playbook per DUN.
- Rapid Response.
- Daily Briefing.
- Polling Day Mode.
- Naratif Cina & India di Modul #6 sahaja.
- Culaan Digital di Modul #7 sahaja.
- Data production N9 sedia ada:
  - `n9_production_bundle.json`
  - `n9_social_summary.json`
  - `warroom_dun_N9_production.json`
  - `war_room_intel_N9.json`
  - `pas_target_23_N9.json`
  - `socmed_by_dun_N9.json`
  - `cula_hub_N9.json`
- Skrip rebuild dan packaging sedia ada.

Jangan kembalikan:

- Matriks `Tugasan — 23 Kerusi PAS` ke Command Centre.
- Kad KPI `Keutamaan Operasi` P1/P2 di Command Centre.
- Naratif Cina/India ke Modul 1.
- Data Johor/Melaka dalam versi N9 sahaja, kecuali code path sedia ada yang tidak mengganggu N9.

Prinsip pemisahan modul:

- Command Centre = strategi ringkas dan mudah baca.
- DUN Drill-Down = semak seat dan tindakan taktikal.
- Culaan Digital = isi, upload, paste, semak, dan validate data.
- Pulse Digital = signal detection, bukan culaan sebenar.
- Action Center = pusat kerja dan status tindakan.

## Cadangan Tech Stack
Jika stack sedia ada sudah stabil, kekalkan sebanyak mungkin. Jika refactor diperlukan:

- Frontend: React / TypeScript atau modular HTML/CSS/JS sedia ada.
- Styling: kekalkan dark theme dan komponen visual semasa.
- Charts: Recharts / Chart.js / implementation sedia ada.
- Data table: TanStack Table atau komponen custom ringan.
- Validation: Zod atau validator custom yang jelas.
- Backend/API: struktur compatible dengan Node/FastAPI/Next API, tetapi mock/offline mesti terus berfungsi.

Utamakan clarity over cleverness.

## Pelaksanaan Berfasa
Laksanakan V2.0 secara berfasa supaya dashboard tidak rosak.

### Fasa 1 — Stabilkan Struktur Semasa
- Jangan ubah visual utama tanpa sebab.
- Pisahkan data loading, scoring, action generation, validation, dan UI rendering.
- Pastikan dashboard N9 sedia ada masih berfungsi selepas setiap perubahan.
- Pastikan Command Centre kekal ringkas.

### Fasa 2 — Mudahkan Input Data
Bina flow Culaan Lapangan yang paling mudah:

1. Isi / upload / paste.
2. Semak preview.
3. Validasi jelas.
4. Hantar.
5. Papar ringkasan berjaya/gagal.

### Fasa 3 — Action Center
- Semua insight penting mesti menghasilkan action.
- Action mesti ada owner, due date, priority, status, category, dan evidence.
- Action Center mesti menjadi pusat kerja harian HQ/admin/pasukan lapangan.

### Fasa 4 — Pulse Digital
- Bezakan jelas daripada Culaan Lapangan.
- Label sebagai `Pulse Digital / Signal Detection`, bukan undi sebenar.
- Hasilkan cadangan tindakan digital berdasarkan signal.

### Fasa 5 — AI/RAG Stub
- Sediakan struktur sahaja dahulu.
- Jangan paparkan istilah teknikal AI pada UI.
- Semua output AI masa depan mesti berasaskan evidence/context.

## Modul Wajib

### 1. Command Centre
Command Centre ialah skrin strategik utama. Ia mesti boleh difahami dalam 10-15 saat.

Paparkan:

- KPI negeri / target kerusi / path to majority.
- Status data terakhir: lapangan + digital.
- 5 DUN paling kritikal hari ini.
- 5 isu paling panas.
- Top Actions Today.
- Alert / exception penting.
- Perubahan 24 jam / 72 jam.

Setiap kad mesti ada:

- Tajuk ringkas.
- Satu angka/status utama.
- Ringkasan 1 ayat.
- CTA seperti `Lihat DUN`, `Buka tindakan`, `Semak isu`.

Jangan masukkan jadual tugas panjang dalam Command Centre.

### 2. Culaan Lapangan
Modul input culaan mesti sangat mudah untuk petugas lapangan dan HQ.

Sediakan 3 mode:

- Borang Lapangan Harian.
- Upload CSV Batch.
- Paste WhatsApp Format.

Medan minimum:

- `tarikh_lawatan`
- `kod_dun`
- `nama_dun`
- `udm`
- `lokaliti`
- `pdm`
- `pelapor_id`
- `jenis_aktiviti`
- `rumah_dilawati`
- `cula_baharu`
- `bulan`
- `condong`
- `pagar`
- `dacing`
- `isu_utama`
- `mood_lapangan`
- `tahap_keyakinan_pelapor`
- `cadangan_tindakan_segera`
- `catatan`

Ciri wajib:

- Helper text jelas.
- Validator inline.
- Preview sebelum submit/upload.
- Upload result summary.
- Template CSV boleh dimuat turun.
- Parser WhatsApp: satu baris = satu laporan PDM.

Validation wajib:

- Semua medan wajib mesti diisi.
- Kod DUN mesti wujud dalam master data.
- PDM mesti sah untuk DUN berkenaan.
- `cula_baharu = bulan + condong + pagar + dacing`.
- `rumah_dilawati >= cula_baharu`.
- Tarikh mesti format sah.
- CSV mesti semak header dan encoding asas.
- WhatsApp paste mesti tunjuk baris mana gagal.

Contoh mesej ralat:

- Jumlah pecahan tidak sama dengan cula baharu.
- Kod DUN tidak ditemui.
- PDM ini tidak sepadan dengan DUN dipilih.
- Baris 4 gagal dibaca. Sila semak format WhatsApp.

### 3. Pulse Digital / Socmed Seed
Modul ini mesti berasingan daripada Culaan Lapangan.

Tujuan:

- Daftar post / soalan / seed content per DUN/lokaliti.
- Simpan URL post dan maklumat crawl.
- Papar sentiment, emotion, issue cluster, engagement, dan risk.
- Jana cadangan tindakan digital.

Medan minimum:

- `tarikh_post`
- `kod_dun`
- `udm`
- `lokaliti`
- `platform`
- `akaun_poster`
- `jenis_stimulus`
- `teks_stimulus`
- `url_post`
- `crawl_due_at`
- `jumlah_respons`
- `jumlah_komen`
- `jumlah_share`
- `sentiment_summary`
- `emotion_summary`
- `issue_cluster`
- `confidence_score`
- `recommended_action`

Penting:

- Letak badge visual `Pulse Digital`.
- Jelaskan bahawa ini signal digital, bukan culaan lapangan sebenar.

### 4. Action Center
Action Center menghimpunkan semua tindakan daripada seluruh sistem.

Setiap action card mesti ada:

- Tajuk tindakan.
- Kategori tindakan.
- DUN / lokaliti terlibat.
- Sebab tindakan dicadangkan.
- Evidence.
- Priority.
- Owner.
- Due time / due date.
- Status: baru / sedang dibuat / siap / ditangguh.
- Impact / result selepas tindakan.

Filter wajib:

- By DUN.
- By owner.
- By priority.
- By category.
- By status.

Kategori tindakan:

- Lapangan.
- Digital.
- Rapid response.
- Program.
- Influencer / stakeholder.
- Telekonferens / koordinasi.
- GOTV / pengukuhan penyokong.

### 5. Rapid Response
Paparkan:

- Isu semasa.
- Tahap risiko.
- Sumber / bukti utama.
- Cadangan respons awal.
- Talking points ringkas.
- Format tindakan disyorkan.

Jenis tindakan:

- Post klarifikasi.
- Video pendek.
- Tele-briefing dalaman.
- Semakan fakta.
- Jurucakap.
- Monitor impak selepas respons.

### 6. DUN Drill-Down
Setiap DUN mesti memaparkan:

- Status seat.
- Trend lapangan.
- Trend digital.
- Isu utama.
- Mood / sentiment.
- Readiness jentera.
- Action list untuk seat tersebut.
- Sejarah tindakan dan impak.

Seat drawer mesti kekal mudah: ringkasan, sebab penting, tindakan seterusnya.

### 7. Program Ops
Sediakan tracking program lapangan:

- Ceramah umum.
- Ceramah kelompok.
- Dialog komuniti.
- Program belia.
- Lawatan bertema.
- Ziarah / outreach.
- Follow-up selepas program.

### 8. Daily Briefing
Briefing harian mesti boleh dijana daripada data mock/production.

Paparkan:

- Apa berubah hari ini.
- Seat paling kritikal.
- Isu paling panas.
- Tindakan 24 jam akan datang.
- Amaran dan peluang.

## Trigger-to-Action Engine
Bina rules engine mudah di `lib/actions/` atau struktur setara.

Trigger yang perlu disokong:

- Sentimen negatif naik mendadak.
- Isu tertentu melonjak 24 jam.
- Cula manual menunjukkan kenaikan pagar/undecided.
- DUN kritikal tiada input lapangan terbaru.
- Engagement digital tinggi tetapi conversion lapangan lemah.
- Naratif negatif di komuniti tertentu meningkat.
- Program sudah dibuat tetapi impak lemah.
- Confidence data rendah.

Setiap trigger mesti hasilkan:

- `reason`
- `evidence`
- `severity`
- `confidence`
- `recommended_actions`

Contoh output:

- Turunkan calon ke Lokaliti A dalam 24 jam.
- Sediakan post klarifikasi BM malam ini.
- Panggil telekonferens ketua PDM jam 9 malam.
- Buat video pendek menjawab isu kos sara hidup.

## Action Taxonomy
Sokong kategori tindakan berikut:

- Lawatan Lapangan: door-to-door, walkabout, ziarah tokoh komuniti, spot check PDM, lawatan bertema isu.
- Telekonferens / Koordinasi: briefing jentera, telekonferens ketua PDM, townhall maya, training volunteer/PACA, internal crisis briefing.
- Social Media: post kempen, post klarifikasi, CTA hadir program, infografik, myth vs fact, community-specific copy.
- Video / Audio: TikTok pendek, Reels/Shorts, explainer issue, street interview, podcast/klip santai.
- Influencer / Stakeholder Outreach: micro-influencer lokal, admin komuniti, tokoh setempat, surrogate speaker, kolaborasi live.
- Program Lapangan: ceramah umum, ceramah kelompok, dialog meja bulat, program komuniti, program belia, follow-up.
- Pengukuhan Penyokong / GOTV: follow-up atas pagar, WhatsApp reminder, volunteer mobilization, PACA readiness, transport, first-time voter activation.
- Rapid Response: semakan fakta, draft klarifikasi, agihan jurucakap, monitor impak.

## Master Data & Mock Data
Sediakan mock/master data realistik untuk demo penuh.

Fail disaran:

- `data/master/dun.json`
- `data/master/udm.json`
- `data/master/lokaliti.json`
- `data/master/pdm.json`
- `data/mock/culaan-lapangan.json`
- `data/mock/pulse-digital.json`
- `data/mock/actions.json`
- `data/mock/rapid-response.json`
- `data/mock/program-ops.json`
- `data/mock/daily-briefing.json`

Jika project kekal pada struktur static prototype, boleh letakkan data setara dalam `prototype/data/` dengan nama yang jelas dan dokumentasi mapping.

## AI / Agentic / RAG / Vector Stub
Bina folder dan stub implementation untuk future integration, tetapi UI kekal simple.

Fail disaran:

- `lib/ai/insight-generator.ts`
- `lib/ai/action-recommender.ts`
- `lib/rag/retrieval.ts`
- `lib/rag/context-builder.ts`
- `lib/vector/indexing.ts`
- `lib/vector/search.ts`
- `lib/scoring/seat-priority.ts`
- `lib/scoring/issue-heat.ts`
- `lib/scoring/confidence.ts`

Setiap fail perlu ada:

- Interface type yang kemas.
- Stub functions.
- Komen ringkas bagaimana ia akan digunakan.

AI output masa depan mesti ada:

- `summary`
- `why_it_matters`
- `confidence`
- `recommended_actions`
- `supporting_evidence`

## Komponen UI Reusable
Sediakan komponen reusable atau pattern setara:

- PageHeader
- SectionCard
- MetricCard
- StatusBadge
- ActionCard
- AlertCard
- EmptyState
- UploadPanel
- CSVPreviewTable
- ValidationSummary
- WhatsAppPastePanel
- SeatPriorityTable
- IssueHeatList
- DailyBriefingCard
- DunInsightPanel

Semua komponen mesti responsive, konsisten, mesra dark theme, dan mudah dibaca.

## Dokumen Wajib
Cipta atau kemas kini dokumen berikut:

- `docs/prd/war-room-prd.md`
- `docs/playbooks/action-playbook.md`
- `docs/playbooks/rapid-response-playbook.md`
- `docs/prompts/agent-prompts.md`
- `docs/prompts/cursor-implementation-notes.md`

Kandungan minimum:

- Objektif modul.
- Aliran data.
- Validation rules.
- Action taxonomy.
- Trigger-to-action examples.
- Future AI/RAG notes.

## Acceptance Criteria
V2.0 dianggap berjaya apabila:

- Pengguna baru boleh faham fungsi utama skrin dalam masa singkat.
- Petugas lapangan boleh isi borang tanpa latihan teknikal berat.
- HQ boleh upload CSV dan paste WhatsApp dengan validasi jelas.
- Command Centre terus menunjukkan apa yang penting dan apa tindakan utama.
- Action Center menyatukan semua tugasan dan status.
- Pulse Digital jelas dibezakan daripada Culaan Lapangan.
- Semua data mock boleh menghidupkan demo end-to-end.
- Struktur code modular dan mudah disambung ke backend sebenar.
- Ada asas AI/RAG/Vector dalam bentuk stub architecture.
- UI tidak memaparkan istilah teknikal berat kepada pengguna biasa.
- Tiada placeholder seperti `TODO`, `coming soon`, atau `dummy section` pada UI.

## Gaya Kerja Kepada Cursor
Laksanakan secara menyeluruh tetapi berdisiplin.

Jangan hanya ubah kosmetik. Buat pembaikan pada:

- Struktur aplikasi.
- Modul dan navigation.
- Forms.
- Parsing.
- Validation.
- Mock data.
- Scoring.
- Action generation.
- Docs.

Apabila perlu membuat trade-off, pilih penyelesaian yang:

1. Lebih jelas.
2. Lebih stabil.
3. Lebih mudah digunakan.
4. Lebih mudah diselenggara.

Jangan jadikan sistem complicated pada permukaan. Anggap pengguna ialah petugas politik, admin, dan penyelia operasi yang perlukan maklumat cepat serta tindakan jelas.

## Ringkasan North Star
Setiap skrin mesti menjawab:

1. Apa berlaku?
2. Kenapa penting?
3. Apa perlu dibuat sekarang?

