"""Audit log for operational changes."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.storage import data_path, load_csv, save_csv

COLUMNS = [
    "timestamp", "user_role", "module", "record_id", "action",
    "previous_value", "new_value", "notes",
]


def log_action(
    user_role: str,
    module: str,
    record_id: str,
    action: str,
    previous_value: str = "",
    new_value: str = "",
    notes: str = "",
) -> None:
    path = data_path("audit_log.csv")
    df = load_csv(path, COLUMNS)
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_role": user_role,
        "module": module,
        "record_id": record_id,
        "action": action,
        "previous_value": str(previous_value)[:500],
        "new_value": str(new_value)[:500],
        "notes": notes,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_csv(df, path)
