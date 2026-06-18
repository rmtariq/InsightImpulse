@echo off
REM ============================================================
REM  InsightPulse War Room - Local Launcher (Windows)
REM ============================================================
REM  Double-click this file to start the War Room on your PC.
REM  Requires Python (most Windows PCs have it; if not, install
REM  from https://python.org or use the Node version below).
REM ============================================================

echo.
echo  ============================================================
echo   InsightPulse War Room - Starting local server...
echo  ============================================================
echo.
echo   Open your browser at:  http://localhost:8080
echo.
echo   Press CTRL+C to stop the server when done.
echo  ============================================================
echo.

cd /d "%~dp0"

REM Try Python 3 first
python -m http.server 8080 2>nul
if %errorlevel% neq 0 (
    REM Try py launcher
    py -3 -m http.server 8080 2>nul
)
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python not found.
    echo  Install Python from https://python.org or run:
    echo     npx serve -p 8080
    echo  in this folder if you have Node.js installed.
    echo.
    pause
)
