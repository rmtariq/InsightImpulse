#!/usr/bin/env python3
"""Build N9 ML predictions JSON for war room dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

from backend.ml.predictive_engine import run_prn_n9_ml  # noqa: E402


def main() -> int:
    result = run_prn_n9_ml(write_output=True)
    if not result.get("success"):
        print(f"FAILED: {result.get('error')}")
        return 1
    print(f"OK — tier={result.get('analytics_tier')} seats={len(result.get('seat_predictions', []))}")
    print(f"Written: {result.get('output_path')}")
    models = result.get("predictive", {}).get("models", {})
    for name, stats in models.items():
        if stats.get("cv_accuracy_mean") is not None:
            print(f"  {name}: CV acc={stats['cv_accuracy_mean']:.1%} F1={stats.get('cv_f1_mean', 0):.1%}")
    actions = result.get("prescriptive_actions") or []
    if actions:
        print(f"Top action: {actions[0].get('title')}")
    import subprocess

    sync = ROOT / "scripts" / "build_n9_daily_ops_sync.py"
    if sync.exists():
        subprocess.run([str(PY), str(sync)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
