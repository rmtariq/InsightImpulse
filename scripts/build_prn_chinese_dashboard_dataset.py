#!/usr/bin/env python3
"""Build combined 3-state CSV for the Chinese narrative Streamlit dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "n9_chinese_narrative_dashboard"
sys.path.insert(0, str(DASH))

from utils.build_dataset import build_dataset  # noqa: E402


def main() -> int:
    df = build_dataset()
    print(f"✅ Built {len(df):,} rows")
    if "state" in df.columns:
        print(df["state"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
