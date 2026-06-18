PRN Digital Culaan — Template Files
=====================================

DOCX (borang cetak + panduan):
  BORANG_CULAAN_DIGITAL_PRN.docx

CSV (upload batch ke War Room):
  TEMPLATE_culaan_KOSONG.csv     — header sahaja (isi harian)
  TEMPLATE_culaan.csv            — contoh umum
  TEMPLATE_culaan_N9.csv         — contoh Negeri Sembilan
  TEMPLATE_culaan_Johor.csv      — contoh Johor
  TEMPLATE_culaan_Melaka.csv     — contoh Melaka

Jana semula template:
  python3 scripts/generate_culaan_templates.py
  (perlukan python-docx — atau guna .venv_cula/bin/python)

Muat turun dari War Room (server mesti hidup):
  /api/cula/template.docx
  /api/cula/template-empty.csv
  /api/cula/template-N9.csv  (atau Johor / Melaka)

Aliran:
  1. Petugas isi DOCX/Excel ikut format
  2. HQ Save As CSV
  3. War Room → Muat Naik Batch → dashboard update
