"""Panduan bacaan heatmap Isu — Bahasa Melayu."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def _top_negative_issue(df: pd.DataFrame) -> tuple[str, int]:
    if df.empty or "issue_cluster" not in df.columns or "sentiment" not in df.columns:
        return "—", 0
    neg = df[df["sentiment"].astype(str).str.lower() == "negative"]
    if neg.empty:
        return "—", 0
    top = neg["issue_cluster"].value_counts()
    return str(top.index[0]), int(top.iloc[0])


def _top_platform_for_issue(df: pd.DataFrame, issue: str) -> tuple[str, int]:
    if df.empty or issue == "—" or "platform" not in df.columns:
        return "—", 0
    sub = df[df["issue_cluster"] == issue]
    if sub.empty:
        return "—", 0
    top = sub["platform"].value_counts()
    return str(top.index[0]), int(top.iloc[0])


def render_sentiment_heatmap_guide(df: pd.DataFrame):
    top_issue, top_count = _top_negative_issue(df)
    with st.expander("📖 Cara baca: Isu vs Sentimen", expanded=False):
        st.markdown(
            """
**Apa carta ini tunjuk?**  
Setiap petak = **bilangan catatan** (post/artikel) untuk satu **isu** dan satu **sentimen**.

| Bahagian | Maksud |
|----------|--------|
| **Baris (kiri)** | Kluster isu — contoh *Cost of Living*, *Chinese Education* |
| **Lajur (atas)** | Sentimen — *negative*, *neutral*, *positive* |
| **Warna merah/jingga** | Banyak catatan dalam sel tersebut |
| **Warna hijau** | Sedikit catatan |

**Cara guna operasi**
1. Cari baris dengan petak **merah di lajur negative** → isu yang paling “panas”.
2. Bandingkan dengan *neutral* / *positive* pada isu sama — adakah isu dominan aduan atau perbincangan?
3. Isu negatif tinggi → rujuk halaman **Tindakan Strategik** untuk tindakan susulan.

**Nota etika:** Carta ini analisis **kandungan naratif berbahasa Cina** — bukan etnik individu dan bukan ramalan undi. Sentimen dari model ML; **semakan manusia** diperlukan sebelum tindakan.
            """
        )
        if top_issue != "—":
            st.info(
                f"**Pemerhatian semasa (penapis aktif):** Isu dengan catatan **negatif** terbanyak "
                f"ialah **{top_issue}** ({top_count} catatan). Utamakan semakan fakta dan respons perkhidmatan jika berkaitan."
            )


def render_platform_heatmap_guide(df: pd.DataFrame):
    top_issue, _ = _top_negative_issue(df)
    top_plat, plat_count = _top_platform_for_issue(df, top_issue)
    with st.expander("📖 Cara baca: Isu vs Platform", expanded=False):
        st.markdown(
            """
**Apa carta ini tunjuk?**  
Setiap petak = **bilangan catatan** untuk satu **isu** di satu **platform**.

| Bahagian | Maksud |
|----------|--------|
| **Baris (kiri)** | Kluster isu |
| **Lajur (atas)** | Platform — Facebook, YouTube, Chinese online media, dll. |
| **Biru gelap** | Banyak catatan |
| **Biru cerah / putih** | Sedikit catatan |

**Cara guna operasi**
1. Untuk isu keutamaan (contoh kos sara hidup), lihat **platform biru paling gelap**.
2. Fokus pemantauan dan draf respons pada saluran tersebut (**Pusat Tindak Balas**).
3. Format respons berbeza mengikut platform — ringkas untuk sosial media, penuh untuk kenyataan rasmi.

**Nota:** Nombor berubah mengikut **penapis sidebar** (tarikh, DUN, platform). Pastikan penapis betul sebelum lapor.
            """
        )
        if top_issue != "—" and top_plat != "—":
            st.info(
                f"**Pemerhatian semasa:** Bagi isu **{top_issue}**, platform dengan catatan terbanyak "
                f"ialah **{top_plat}** ({plat_count} catatan). Pertimbangkan pemantauan aktif di saluran ini."
            )


def render_heatmap_reading_summary(df: pd.DataFrame):
    """Ringkasan satu blok di atas kedua-dua heatmap."""
    top_issue, neg_n = _top_negative_issue(df)
    top_plat, plat_n = _top_platform_for_issue(df, top_issue)
    st.caption(
        "💡 **Ringkas:** Carta kiri = isu **mana** yang negatif/neutral/positif · "
        "Carta kanan = isu **mana** paling kuat di **platform mana**. "
        "Klik 📖 di bawah setiap carta untuk panduan penuh."
    )
    if top_issue != "—":
        st.markdown(
            f"| Keutamaan semasa | Platform dominan (isu tersebut) | "
            f"Jumlah catatan (penapis aktif) |\n"
            f"|---|---|---|\n"
            f"| **{top_issue}** ({neg_n} negatif) | **{top_plat}** ({plat_n} catatan) | **{len(df):,}** |"
        )
