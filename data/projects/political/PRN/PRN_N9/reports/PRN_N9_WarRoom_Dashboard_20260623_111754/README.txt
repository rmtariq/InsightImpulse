============================================================
  InsightPulse — PRN Negeri Sembilan War Room Dashboard
  Pakej perkongsian · N9 sahaja
============================================================

Dijana: 2026-06-23 11:18:14 +08

MODUL TERMASUK (7):
  1. Command Centre      — KPI strategik + senario MN/PAS solo
  2. DUN Drill-Down      — Peta 36 kerusi + drawer analitik
  3. Rapid Response      — Amaran + templat respons
  4. Daily Briefing      — Ringkasan harian
  5. Polling Day Mode    — Mod hari mengundi
  6. Naratif Cina & India — Pemantauan komuniti
  7. Culaan Digital      — Paparan data lapangan (baca sahaja tanpa API)

CARA BUKA:
  MAC:     Right-click START_MAC_LINUX.command → Open
  WINDOWS: Double-click START_WINDOWS.bat
  MANUAL:  python3 -m http.server 8080
           kemudian buka http://localhost:8080

NOTA:
  • Pakej ini LOCKED untuk Negeri Sembilan (36 DUN).
  • Perlukan sambungan internet untuk fon & peta Leaflet (CDN).
  • Modul Culaan: hantar borang perlukan server penuh InsightPulse
    (bukan termasuk dalam zip ini) — paparan data sedia ada masih berfungsi.
  • Refresh data: hubungi pasukan InsightPulse untuk bundle terkini.

Pautan pantas:
  Command Centre:  http://localhost:8080/
  Naratif C/I:     http://localhost:8080/?module=narrative&state=N9
  DUN Drill-Down:  http://localhost:8080/?module=dun&state=N9

============================================================
  InsightPulse  |  AI Social Listening Platform
============================================================
