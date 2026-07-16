============================================================
  InsightPulse War Room LIVE - PRN Negeri Sembilan
  Local Installation - How to Operate
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

  Open a terminal at the InsightPulse repo root and run:

    bash scripts/start_prn_warroom_live.sh

  Then open:   http://localhost:8080

  Do not use plain `python -m http.server` for daily operations.
  Plain static hosting opens the UI but disables live APIs.

------------------------------------------------------------
 METHOD 3: VS CODE LIVE SERVER  (developer-friendly)
------------------------------------------------------------

  Use VS Code/Cursor for editing only. For operation, start:

    bash scripts/start_prn_warroom_live.sh

  Then browse to http://localhost:8080.

------------------------------------------------------------
 STOPPING THE SERVER
------------------------------------------------------------

  Press CTRL+C in the terminal window where the server
  is running.

------------------------------------------------------------
 ABOUT THIS LIVE DASHBOARD
------------------------------------------------------------

This is the local live War Room dashboard for PRN Negeri
Sembilan. It runs a static UI together with a Python API
server for Digital Culaan, Socmed Seed, Action Center status,
and live JSON persistence.

Modules (index.html — default, 9 modules):
  1. Command Center       - Strategic overview (+ coalition summary)
  2. DUN Drill-Down       - Seat map, grid, drawer drill-down
  3. Action Center        - Owner, due date, priority, status
  4. Pulse Digital        - Signal detection (not field cula)
  5. Rapid Response       - Alerts + response actions
  6. Daily Briefing       - 7am briefing from action data
  7. Polling Day Mode     - T-72h activation UI
  8. Naratif Cina & India - Community narrative monitoring
  9. Culaan Digital       - Field form, batch upload, PDM review

Live data stores:
  data/projects/political/PRN/digital_cula/{state}/submissions.csv
  data/projects/political/PRN/warroom_live/{state}/action_status.json
  data/projects/political/PRN/warroom_live/{state}/custom_actions.json

Action Center API:
  GET    /api/action-center?state=N9
  POST   /api/action-center/action
  PATCH  /api/action-center/action

Deep-link to Module #6 (Naratif):
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
  bash scripts/start_prn_warroom_live.sh

  IMPORTANT: Use the script above (not plain python -m http.server).
  The launcher runs War Room UI + Digital Culaan + Action Center APIs together.

Modul #7 — Culaan Digital (N9, Johor, Melaka):
  http://localhost:8080/?module=cula

  Tab 1 — Borang Lapangan: sukarelawan hantar delta harian
  Tab 2 — Semakan PDM:     ketua PDM lulus / tolak (VERIFIED masuk agregat)
  Tab 3 — Socmed Seed:     rancang post DUN/UMDAP/isu → daftar URL → crawl sentiment
  Tab 4 — Ringkasan DUN:  KPI + jadual BKC per kerusi (Command Center)

  Socmed seed URL:
    http://localhost:8080/?module=cula&tab=socmed

  Data disimpan ke:
    data/projects/political/PRN/digital_cula/N9/submissions.csv
    data/projects/political/PRN/digital_cula/Johor/submissions.csv
    data/projects/political/PRN/digital_cula/Melaka/submissions.csv
    (+ cula_hub.json + prototype/data/cula_hub_{state}.json)

  Rebuild hub manually:
    python3 scripts/digital_cula_lib.py

  Rebuild socmed per DUN (after master crawl refresh):
    python3 scripts/build_warroom_socmed_by_dun.py
    → prototype/data/socmed_by_dun_N9.json

Or double-click START_MAC_LINUX.command in this folder.
  (Update START script to call prn_digital_cula_server.py if needed.)

============================================================
  InsightPulse  |  AI Social Listening Platform
============================================================
