"""Ethics notice and audit helpers."""
from __future__ import annotations

import streamlit as st

ETHICS_NOTICE = (
    "Sistem ini menganalisis **naratif awam** dan **isu perkhidmatan awam**. "
    "Ia **tidak** boleh digunakan untuk infer etnik, agama atau kecenderungan undi perseorangan."
)

RESPONSE_NOTICE = (
    "Semua cadangan respons mesti disemak dan diluluskan oleh pegawai bertanggungjawab "
    "sebelum diterbitkan."
)


def render_ethics_notice():
    st.warning(ETHICS_NOTICE)


def render_response_notice():
    st.info(RESPONSE_NOTICE)
