#!/usr/bin/env bash
# Jalankan dashboard — guna venv projek (elak amaran Streamlit lama dari NEImpulse)
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/streamlit run app.py
