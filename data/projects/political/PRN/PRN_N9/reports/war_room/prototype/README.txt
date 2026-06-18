============================================================
  InsightPulse War Room - PRN Negeri Sembilan
  Local Installation - How to Open
============================================================

The HTML file cannot be opened by double-clicking directly,
because modern browsers block JavaScript modules loaded from
the local file system (file://) for security reasons.

You need to serve it via a tiny local web server. Here are
3 easy ways to do it - pick the one that fits your setup:

------------------------------------------------------------
 METHOD 1: ONE-CLICK LAUNCHER  (easiest)
------------------------------------------------------------

  WINDOWS:
     Double-click  START_WINDOWS.bat

  MAC:
     Right-click   START_MAC_LINUX.command  -> Open
     (Mac warns the first time only - then it works)

  LINUX:
     Double-click  START_MAC_LINUX.command
     or run from terminal:  ./START_MAC_LINUX.command

  Then open your browser at:   http://localhost:8080

  Requires Python (already installed on Mac/Linux; for
  Windows install from https://python.org if missing).

------------------------------------------------------------
 METHOD 2: COMMAND LINE  (if Method 1 doesn't work)
------------------------------------------------------------

  Open a terminal in this folder and run ONE of these:

    Python 3:   python3 -m http.server 8080
    Python 2:   python  -m SimpleHTTPServer 8080
    Node.js:    npx serve -p 8080
    PHP:        php -S localhost:8080

  Then open:   http://localhost:8080

------------------------------------------------------------
 METHOD 3: VS CODE LIVE SERVER  (developer-friendly)
------------------------------------------------------------

  1. Open this folder in VS Code (you already use it)
  2. Install the "Live Server" extension
  3. Right-click index.html  ->  "Open with Live Server"

  Browser opens automatically.

------------------------------------------------------------
 STOPPING THE SERVER
------------------------------------------------------------

  Press CTRL+C in the terminal window where the server
  is running.

------------------------------------------------------------
 ABOUT THIS PROTOTYPE
------------------------------------------------------------

This is a CLICKABLE MOCKUP for pitching the Election War
Room concept to stakeholders. All data shown is realistic
mock data - no real backend, no API calls, no live feeds.

Modules (index.html — default, 7 modules):
  1. Command Center       - Strategic overview
  2. DUN Drill-Down       - 36 N9 state seats
  3. Rapid Response       - Alerts + bilingual templates
  4. Daily Briefing       - 7am auto-generated briefing
  5. War-Game Simulator   - Coalition scenarios
  6. Polling Day Mode     - T-72h activation UI
  7. Naratif Cina & India - Community narrative monitoring
                            (action queue, issue heatmap, drafts)

Deep-link to Module #7:
  http://localhost:8080/?module=narrative&state=N9

State toggle loads DUN maps for all three states:
  N9     — 36 kerusi + geolokasi rasmi/semi-rasmi (from geoloc report)
  Melaka — 28 kerusi + geolokasi JAPERUN (readiness layer)
  Johor  — 56 kerusi + geolokasi proksi (prn_johor_geolokasi_war_room.xlsx)

Rebuild geo datasets after updating source files:
  python3 scripts/build_warroom_geoloc_dataset.py

Source files copied to prototype/data/:
  source_geoloc_report.docx
  source_prn_johor_geolokasi_war_room.xlsx
  prn_geoloc_johor.csv

Original React build (6 modules only):
  http://localhost:8080/react/index.html

------------------------------------------------------------
 INSIGHTPULSE REPO SYNC  (Jun 2026)
------------------------------------------------------------

Also in repo:
  index_legacy_narrative_shell.html  — mobile-first narrative mock
  react/                             — original React bundle (6 mod)

Production narrative dashboard (live crawl data):
  n9_chinese_narrative_dashboard/app.py  (Streamlit)

Quick start from repo root:
  bash scripts/start_prn_warroom_prototype.sh

  IMPORTANT: Use the script above (not plain python -m http.server).
  The launcher runs War Room UI + Digital Culaan API together.

Modul #8 — Culaan Digital (N9, Johor, Melaka):
  http://localhost:8080/?module=cula

  Tab 1 — Borang Lapangan: sukarelawan hantar delta harian
  Tab 2 — Semakan PDM:     ketua PDM lulus / tolak (VERIFIED masuk agregat)
  Tab 3 — Ringkasan DUN:  KPI + jadual BKC per kerusi

  Data disimpan ke:
    data/projects/political/PRN/digital_cula/N9/submissions.csv
    data/projects/political/PRN/digital_cula/Johor/submissions.csv
    data/projects/political/PRN/digital_cula/Melaka/submissions.csv
    (+ cula_hub.json + prototype/data/cula_hub_{state}.json)

  Rebuild hub manually:
    python3 scripts/digital_cula_lib.py

Or double-click START_MAC_LINUX.command in this folder.
  (Update START script to call prn_digital_cula_server.py if needed.)

============================================================
  InsightPulse  |  AI Social Listening Platform
============================================================
