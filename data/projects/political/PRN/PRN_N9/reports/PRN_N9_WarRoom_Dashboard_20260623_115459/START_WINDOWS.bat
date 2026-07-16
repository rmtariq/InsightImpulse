@echo off
cd /d "%~dp0"
echo.
echo  InsightPulse — PRN Negeri Sembilan War Room
echo  http://localhost:8080
echo  Press CTRL+C to stop
echo.
start "" "http://localhost:8080"
python -m http.server 8080 2>nul || py -3 -m http.server 8080 2>nul || (
  echo ERROR: Python not found. Install from https://python.org
  pause
)
