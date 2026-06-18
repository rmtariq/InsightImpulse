#!/usr/bin/env bash
# Launch PRN War Room prototype + Digital Culaan API (N9, Johor, Melaka)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"
echo "Starting War Room + Digital Culaan API on http://localhost:${PORT}"
echo "  Modul Culaan: ?module=cula"
echo "  Data CSV:     data/projects/political/PRN/digital_cula/"
exec python3 "$ROOT/scripts/prn_digital_cula_server.py" --port "$PORT"
