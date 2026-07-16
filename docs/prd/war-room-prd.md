# PRD — PRN Negeri Sembilan War Room V2.0

## Objektif
War Room V2.0 membantu HQ, admin, petugas lapangan dan pasukan komunikasi membuat keputusan harian dengan cepat.

North star:

1. Mudah isi data.
2. Mudah baca dashboard.
3. Mudah ambil tindakan.

## Modul
- Command Centre: ringkasan strategik, senario, isu panas dan Top Actions Today.
- DUN Drill-Down: peta 36 DUN, drawer seat, status, bukti dan tindakan.
- Action Center: pusat tugasan dengan owner, due date, priority, status dan evidence.
- Pulse Digital: signal detection online, bukan culaan lapangan.
- Culaan Digital: borang, CSV batch dan WhatsApp paste.
- Rapid Response: tindakan isu viral / negatif.
- Daily Briefing: ringkasan 24 jam dan tindakan seterusnya.

## Aliran Data
Input utama:

- Culaan lapangan: rumah dilawati, cula baharu, pecahan bulan/condong/pagar/dacing, isu dan catatan.
- Pulse digital: seed/post URL, platform, engagement, sentiment, issue cluster.
- Naratif komuniti: isu Cina/India dan tindakan komunikasi.
- Model DUN: pasWinProb, scenario PAS solo, PAS+MN dan path to majority.

Output utama:

- Action card yang boleh terus dilaksanakan.
- Briefing harian.
- DUN drawer dengan tindakan seat-level.

## Validation Rules
- Kod DUN mesti wujud dalam master data.
- PDM/lokaliti mesti sepadan dengan DUN jika master data tersedia.
- `cula_baharu = bulan + condong + pagar + dacing` jika pecahan diisi.
- `rumah_dilawati >= cula_baharu`.
- CSV mesti ada header/kolum wajib.
- WhatsApp paste: satu baris = satu laporan PDM; baris gagal mesti ditunjukkan dengan mesej BM jelas.

## Acceptance Criteria
- Command Centre boleh difahami dalam 10-15 saat.
- Setiap insight penting ada action.
- Action Center boleh filter by priority, category dan status.
- Pulse Digital jelas dilabel sebagai signal, bukan undi/cula sebenar.
- UI kekal BM mudah dan tidak menonjolkan istilah teknikal.

