"""Translation utilities — BM for Chinese-language narrative text."""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import streamlit as st

_CJK = re.compile(r"[\u4e00-\u9fff]")
_PLACEHOLDER = re.compile(r"^\[BM\]", re.IGNORECASE)


# Fallback BM for common Chinese templates (when CSV/API unavailable)
STATIC_ZH_BM: dict[str, str] = {
    "森美兰州选临近，芙蓉市区塞车问题又严重了，停车位不够。": (
        "PRN Negeri Sembilan hampir — kesesakan trafik di Seremban teruk, tempat letak kereta tidak mencukupi."
    ),
    "汝来工厂区物价上涨，中小企业老板叫苦。华社关注生活费。": (
        "Kawasan kilang Nilai — harga barang naik, pemilik PKS merungut; komuniti Cina prihatin kos sara hidup."
    ),
    "马口小贩反映市议会执法太严，生意难做。": (
        "Penjaja Bahau keluh penguatkuasaan majlis perbandaran terlalu ketat, sukar berniaga."
    ),
    "波德申旅游季，本地商家希望州政府多宣传。": (
        "Musim pelancongan Port Dickson — peniaga tempatan harap kerajaan negeri lebih promosi."
    ),
    "芦骨华人区水供不稳定，居民投诉多次。": (
        "Kawasan Lukut — bekalan air tidak stabil, penduduk adu berkali-kali."
    ),
    "行动党在森州的表现，华社有不同看法。": (
        "Prestasi DAP di Negeri Sembilan — komuniti Cina ada pelbagai pandangan."
    ),
    "马华能否在州选中重新获得代表性？": (
        "Bolehkah MCA regain representasi dalam PRN negeri?"
    ),
    "年轻首投族更关注就业和房价。": (
        "Pengundi muda first-time lebih fokus pekerjaan dan harga rumah."
    ),
    "独中拨款和华文教育仍是热点。": (
        "Peruntukan sekolah Cina independen dan pendidikan Cina masih isu panas."
    ),
    "假消息说某候选人退选，请勿转发。": (
        "Maklumat palsu kata calon tarik diri — jangan kongsi."
    ),
    "PH和BN合作讨论，网上议论纷纷。": (
        "Perbincangan kerjasama PH dan BN — perdebatan sengit dalam talian."
    ),
    "伊党因素让部分选民担忧。": (
        "Faktor PAS membuat sebahagian pengundi bimbang."
    ),
    # Johor — sampel crawl PRN
    "柔佛州选临近，新山市区塞车严重。": (
        "PRN Johor hampir — kesesakan trafik di pusat bandar JB teruk."
    ),
    "士古来工厂区物价上涨，商家叫苦。": (
        "Kawasan kilang Skudai — harga barang naik, peniaga merungut."
    ),
    "Stulang 区水供不稳定，居民投诉。": (
        "Kawasan Stulang — bekalan air tidak stabil, penduduk membuat aduan."
    ),
    "华文教育拨款仍是热点。": (
        "Peruntukan pendidikan Cina masih isu hangat."
    ),
    "DAP Johor perlu fokus perkhidmatan bandar.": (
        "DAP Johor perlu fokus perkhidmatan bandar."
    ),
}

STATIC_EN_BM: dict[str, str] = {
    "Chinese community in Negeri Sembilan discusses local council performance.": (
        "Komuniti Cina di Negeri Sembilan bincang prestasi majlis perbandaran tempatan."
    ),
    "SME owners in Nilai worry about rising costs ahead of state election.": (
        "Pemilik PKS di Nilai bimbang kos naik menjelang PRN negeri."
    ),
    "Chinese school funding remains a key narrative online.": (
        "Peruntukan sekolah Cina kekal naratif utama dalam talian."
    ),
    "Traffic congestion in Seremban city centre frustrates residents.": (
        "Kesesakan trafik di pusat bandar Seremban kecewakan penduduk."
    ),
    "Chinese community in Johor discusses local council performance.": (
        "Komuniti Cina di Johor bincang prestasi majlis perbandaran tempatan."
    ),
    "SME owners in Kulai worry about rising costs.": (
        "Pemilik PKS di Kulai bimbang kos sara hidup naik."
    ),
    "PRN Johor: komuniti Cina bincang kos sara hidup di JB.": (
        "PRN Johor: komuniti Cina bincang kos sara hidup di JB."
    ),
}


def has_chinese(text: object) -> bool:
    return bool(_CJK.search(str(text or "")))


def is_placeholder_translation(value: object, post_text: object = "") -> bool:
    s = str(value or "").strip()
    if not s or s.lower() in ("nan", "none", "—", "-"):
        return True
    if _PLACEHOLDER.match(s):
        return True
    if post_text and s == str(post_text).strip():
        return False
    return False


def lookup_static_bm(post: str) -> Optional[str]:
    """Match known Chinese/English template → BM."""
    post = str(post or "").strip()
    if not post:
        return None
    base = re.split(r"\s+#|\s+—|\(", post, maxsplit=1)[0].strip()
    if base in STATIC_ZH_BM:
        suffix = post[len(base):].strip()
        bm = STATIC_ZH_BM[base]
        if suffix.startswith("#"):
            bm += f" ({suffix[1:].strip()})"
        elif suffix.startswith("("):
            bm += f" {suffix}"
        return bm
    for zh, bm in STATIC_ZH_BM.items():
        if zh in post:
            return bm
    base_en = re.split(r"\s+—", post, maxsplit=1)[0].strip()
    if base_en in STATIC_EN_BM:
        return STATIC_EN_BM[base_en]
    for en, bm in STATIC_EN_BM.items():
        if en in post:
            return bm
    return None


def needs_bm_translation(row: pd.Series | dict) -> bool:
    if isinstance(row, pd.Series):
        row = row.to_dict()
    post = str(row.get("post_text") or "").strip()
    if not post:
        return False
    lang = str(row.get("language_detected") or "").lower()
    existing = row.get("translated_text_bm")
    if not is_placeholder_translation(existing, post):
        return False
    if lang == "ms" and not has_chinese(post):
        return False
    return has_chinese(post) or lang.startswith("zh") or lang == "mixed" or lang == "en"


@st.cache_data(ttl=86400, show_spinner=False)
def translate_text(text: str, target: str = "ms", source: str = "auto") -> str:
    text = str(text or "").strip()
    if not text:
        return ""
    static = lookup_static_bm(text)
    if static and target == "ms":
        return static
    try:
        from deep_translator import GoogleTranslator
        if has_chinese(text):
            src = "zh-CN"
        elif source != "auto":
            src = source
        else:
            src = "auto"
        return GoogleTranslator(source=src, target=target).translate(text[:4800])
    except Exception as exc:
        static = lookup_static_bm(text)
        if static:
            return static
        # Fallback OpenAI jika deep_translator tiada
        try:
            import os
            key = os.getenv("OPENAI_API_KEY")
            if key:
                from openai import OpenAI
                client = OpenAI(api_key=key)
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Terjemah teks berikut ke Bahasa Melayu (ringkas, satu perenggan). "
                                "Jawab terjemahan sahaja, tiada nota.\n\n" + text[:2000]
                            ),
                        }
                    ],
                    max_tokens=500,
                    temperature=0.2,
                )
                out = (resp.choices[0].message.content or "").strip()
                if out:
                    return out
        except Exception:
            pass
        # Akhir: papar asal, bukan mesej ralat teknikal
        if has_chinese(text):
            return text
        return f"(Terjemahan gagal — semak sambungan internet: {exc})"


def resolve_bm_translation(row: pd.Series | dict, auto_translate: bool = True) -> str:
    if isinstance(row, pd.Series):
        row = row.to_dict()
    post = str(row.get("post_text") or "").strip()
    lang = str(row.get("language_detected") or "").lower()
    existing = str(row.get("translated_text_bm") or "").strip()

    if lang == "ms" and post and not has_chinese(post):
        return post

    if existing and not is_placeholder_translation(existing, post):
        return existing

    if not post:
        return "—"

    static = lookup_static_bm(post)
    if static:
        return static

    if auto_translate and needs_bm_translation(row):
        return translate_text(post, target="ms")

    if has_chinese(post):
        return "(Terjemahan belum tersedia — hidupkan Auto-terjemah)"
    if lang == "en":
        return translate_text(post, target="ms") if auto_translate else post
    return post


def enrich_translations(
    df: pd.DataFrame,
    auto_translate: bool = True,
    max_auto: int = 200,
) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    if "translated_text_bm" not in out.columns:
        out["translated_text_bm"] = ""

    # Bersihkan placeholder dalam CSV supaya tidak dipaparkan mentah
    ph = out["translated_text_bm"].astype(str).str.match(r"^\[BM\]", na=False)
    out.loc[ph, "translated_text_bm"] = ""

    pending: list = []
    display_vals = []
    for i, row in out.iterrows():
        bm = resolve_bm_translation(row, auto_translate=False)
        if (
            bm.startswith("(")
            or bm.startswith("—")
            or is_placeholder_translation(bm, row.get("post_text"))
        ):
            pending.append(i)
        display_vals.append(bm)
    out["display_translation_bm"] = display_vals

    if auto_translate and pending:
        to_do = pending[:max_auto]
        if to_do:
            with st.spinner(f"Menterjemah {len(to_do)} hantaran ke BM…"):
                for i in to_do:
                    out.at[i, "display_translation_bm"] = resolve_bm_translation(
                        out.loc[i], auto_translate=True
                    )
    return out


def posts_display_columns(
    df: pd.DataFrame,
    show_translation: bool = True,
    extra: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Build display dataframe — Terjemahan BM sentiasa dikira semula (elak cache/placeholder)."""
    if df is None or df.empty:
        return df
    work = df.copy()
    auto = st.session_state.get("auto_translate_bm", True)

    base_extra = extra or ["platform", "account_name", "sentiment", "engagement_total", "source_url"]
    out_cols = {}
    if "post_text" in work.columns:
        out_cols["Teks Asal"] = work["post_text"]

    if show_translation:
        out_cols["Terjemahan BM"] = work.apply(
            lambda r: resolve_bm_translation(r, auto_translate=auto), axis=1
        )

    for c in base_extra:
        if c in work.columns:
            out_cols[c] = work[c]

    return pd.DataFrame(out_cols)
