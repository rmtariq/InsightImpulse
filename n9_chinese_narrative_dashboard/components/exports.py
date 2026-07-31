"""Download helpers for CSV/Excel/HTML."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st


def download_csv_button(df: pd.DataFrame, filename: str, label: str = "⬇️ Muat Turun CSV"):
    if df is None or df.empty:
        st.caption("Tiada data untuk dimuat turun.")
        return
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        width="stretch",
    )


def download_excel_button(df: pd.DataFrame, filename: str, label: str = "⬇️ Muat Turun Excel"):
    if df is None or df.empty:
        st.caption("Tiada data untuk dimuat turun.")
        return
    buf = io.BytesIO()
    try:
        df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            label,
            data=buf.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
    except Exception as exc:
        st.error(f"Ralat Excel: {exc}")


def download_html_button(html: str, filename: str, label: str = "⬇️ Muat Turun HTML"):
    st.download_button(
        label,
        data=html.encode("utf-8"),
        file_name=filename,
        mime="text/html",
        width="stretch",
    )
