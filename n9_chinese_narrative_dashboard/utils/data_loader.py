"""Load CSV datasets with caching and fallbacks."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.data_cleaner import clean_posts, data_quality_report
from utils.sample_data_generator import ensure_sample_data

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

POSTS_3NEGERI = DATA_DIR / "prn_chinese_narrative_posts_3negeri.csv"
POSTS_MAIN = DATA_DIR / "n9_chinese_narrative_posts.csv"
POSTS_SAMPLE = DATA_DIR / "sample_n9_chinese_narrative_posts.csv"

SEED_FILES = {
    "Negeri Sembilan": DATA_DIR / "n9_prn_social_media_crawler_seed_list.csv",
    "Johor": DATA_DIR / "johor_prn_social_media_crawler_seed_list.csv",
    "Melaka": DATA_DIR / "melaka_prn_social_media_crawler_seed_list.csv",
}


def _posts_path() -> Path:
    ensure_sample_data()
    if POSTS_3NEGERI.exists():
        return POSTS_3NEGERI
    if POSTS_MAIN.exists():
        return POSTS_MAIN
    if POSTS_SAMPLE.exists():
        return POSTS_SAMPLE
    try:
        from utils.build_dataset import build_dataset
        build_dataset()
        if POSTS_3NEGERI.exists():
            return POSTS_3NEGERI
    except Exception:
        pass
    from utils.sample_data_generator import generate_posts
    generate_posts(180).to_csv(POSTS_SAMPLE, index=False)
    return POSTS_SAMPLE


@st.cache_data(show_spinner="Memuatkan data naratif berbahasa Cina…")
def _load_posts_cached(file_path: str, mtime: float) -> pd.DataFrame:
    """Cache invalidated when CSV file changes (mtime)."""
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception:
        df = pd.read_csv(POSTS_SAMPLE, low_memory=False)
    return clean_posts(df)


def load_posts() -> pd.DataFrame:
    path = _posts_path()
    return _load_posts_cached(str(path.resolve()), path.stat().st_mtime)


def load_seed_list() -> pd.DataFrame:
    ensure_sample_data()
    parts = []
    for state, path in SEED_FILES.items():
        if path.exists():
            df = pd.read_csv(path, low_memory=False)
            if "state" not in df.columns:
                df["state"] = state
            parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def get_data_source_label() -> str:
    path = _posts_path()
    if path == POSTS_3NEGERI:
        return POSTS_3NEGERI.name
    if path == POSTS_MAIN:
        return POSTS_MAIN.name
    return f"{POSTS_SAMPLE.name} (sample)"


def get_quality_report(df: pd.DataFrame) -> dict:
    return data_quality_report(df)
