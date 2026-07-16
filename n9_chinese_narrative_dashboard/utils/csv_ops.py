"""CSV column helpers for operational save/update."""
from __future__ import annotations

import pandas as pd


def coerce_text_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Cast columns to plain text so empty strings can be saved safely."""
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: "" if pd.isna(x) else str(x))
    return out
