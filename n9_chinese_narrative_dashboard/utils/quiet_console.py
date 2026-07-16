"""Suppress noisy Streamlit deprecation spam in the terminal."""
from __future__ import annotations

import logging

_QUIET = False

_NOISE = (
    "use_container_width",
    "Please replace `",
    "keyword arguments have been deprecated",
    "Use `config` instead to specify Plotly",
)


class _StreamlitNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(token in msg for token in _NOISE)


def silence_console_noise() -> None:
    global _QUIET
    if _QUIET:
        return
    _QUIET = True
    filt = _StreamlitNoiseFilter()
    for name in (
        "streamlit",
        "streamlit.runtime",
        "streamlit.elements.plotly_chart",
        "streamlit.deprecation_util",
    ):
        logging.getLogger(name).addFilter(filt)
