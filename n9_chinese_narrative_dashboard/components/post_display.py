"""Bilingual post display helpers."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.translator import is_placeholder_translation, posts_display_columns, resolve_bm_translation


def _bm_for_row(row: pd.Series) -> str:
    auto = st.session_state.get("auto_translate_bm", True)
    for col in ("display_translation_bm", "translated_text_bm"):
        val = row.get(col)
        if val and not is_placeholder_translation(val, row.get("post_text")):
            return str(val)
    return resolve_bm_translation(row, auto_translate=auto)


def render_bilingual_post(row: pd.Series, key: str = ""):
    """Card: original + BM translation."""
    post = str(row.get("post_text") or "")
    bm = _bm_for_row(row)

    st.markdown(f"**Teks asal:** {post}")
    st.markdown(f"**Terjemahan BM:** {bm}")
    meta = []
    if row.get("platform"):
        meta.append(str(row["platform"]))
    if row.get("sentiment"):
        meta.append(f"sentimen: {row['sentiment']}")
    if row.get("engagement_total"):
        meta.append(f"engagement: {row['engagement_total']}")
    if meta:
        st.caption(" · ".join(meta))
    url = row.get("source_url")
    if url and str(url).startswith("http"):
        st.markdown(f"[Pautan sumber]({url})")


def render_posts_table(
    df: pd.DataFrame,
    n: int = 10,
    sort_col: str = "engagement_total",
    extra_cols: list[str] | None = None,
):
    """Table with original + BM columns."""
    if df is None or df.empty:
        st.info("Tiada hantaran.")
        return
    show = st.session_state.get("show_translation_bm", True)
    sub = df.nlargest(n, sort_col) if sort_col in df.columns else df.head(n)
    st.dataframe(
        posts_display_columns(sub, show_translation=show, extra=extra_cols),
        width="stretch",
        hide_index=True,
    )
