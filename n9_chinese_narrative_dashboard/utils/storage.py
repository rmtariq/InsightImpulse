"""Safe CSV/JSON storage for operational data."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    ensure_dirs()
    if not path.exists():
        return pd.DataFrame(columns=columns or [])
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception:
        return pd.DataFrame(columns=columns or [])
    if columns:
        for c in columns:
            if c not in df.columns:
                df[c] = ""
    return df


def save_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def data_path(name: str) -> Path:
    return DATA_DIR / name


def config_path(name: str) -> Path:
    return CONFIG_DIR / name
