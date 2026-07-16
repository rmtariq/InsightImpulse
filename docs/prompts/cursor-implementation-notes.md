# Cursor Implementation Notes — PRN N9 Dashboard V2.0

## Guardrails
- Jangan rebuild dashboard dari kosong.
- Kekalkan dark theme, Command Centre strategik, DUN drawer, Naratif Modul #6 dan Culaan Modul #7.
- Jangan kembalikan matriks `Tugasan — 23 Kerusi PAS` ke Command Centre.
- Jangan kembalikan KPI `Keutamaan Operasi` P1/P2 ke Command Centre.

## Current V2 Tranche
Tranche pertama menambah:

- `data/n9_actions_v2.json`
- `js/action-center.js`
- Modul Action Center
- Modul Pulse Digital
- Panel Top Actions Today di Command Centre
- Rapid Response dan Daily Briefing membaca action data V2 apabila tersedia

## Next Implementation Steps
- Sambungkan action data kepada backend apabila schema stabil.
- Simpan status action secara persistent, bukan session-only.
- Jadikan validation Culaan reusable.
- Tambah export briefing WhatsApp/PDF.
- Tambah owner directory untuk Action Center.

