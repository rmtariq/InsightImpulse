"""Daily executive brief generator (Bahasa Melayu)."""
from __future__ import annotations

from datetime import datetime

import pandas as pd


def generate_brief(posts: pd.DataFrame, actions: pd.DataFrame, complaints: pd.DataFrame, state: str = "") -> str:
    today = datetime.now().strftime("%d %B %Y")
    if state:
        sub = posts[posts["state"] == state] if posts is not None and "state" in posts.columns else posts
    else:
        sub = posts
    n_posts = len(sub) if sub is not None and not sub.empty else 0
    neg_pct = 0.0
    if sub is not None and not sub.empty and "sentiment" in sub.columns:
        neg_pct = (sub["sentiment"].astype(str).str.lower() == "negative").mean() * 100

    top_issues = []
    if sub is not None and not sub.empty and "issue_cluster" in sub.columns:
        top_issues = sub["issue_cluster"].value_counts().head(5).index.tolist()

    rising = ""
    if sub is not None and not sub.empty and "growth_flag" in sub.columns:
        rising_df = sub[sub["growth_flag"] == True]  # noqa: E712
        if not rising_df.empty and "issue_cluster" in rising_df.columns:
            rising = rising_df["issue_cluster"].mode().iloc[0] if len(rising_df) else ""

    areas = []
    if sub is not None and not sub.empty and "constituency" in sub.columns:
        areas = sub["constituency"].value_counts().head(3).index.tolist()

    risks = []
    if sub is not None and not sub.empty and "risk_level" in sub.columns:
        risks = sub[sub["risk_level"].isin(["High", "Critical"])]["issue_cluster"].unique().tolist()[:5]

    misinfo = []
    if sub is not None and not sub.empty and "misinformation_flag" in sub.columns:
        m = sub[sub["misinformation_flag"] == True]  # noqa: E712
        if not m.empty:
            misinfo = m["post_text"].head(3).tolist()

    pending = []
    if actions is not None and not actions.empty and "action_status" in actions.columns:
        pending = actions[~actions["action_status"].isin(["Selesai", "Tidak Memerlukan Tindakan"])]["action_id"].head(5).tolist()

    title_state = f" — {state}" if state else " — N9 · Johor · Melaka"
    lines = [
        f"# Ringkasan Eksekutif Harian{title_state}",
        f"**Tarikh:** {today}",
        "",
        "---",
        "",
        "## 1. Ringkasan situasi",
        f"**[Analitik]** {n_posts} catatan naratif berbahasa Cina diperhatikan dalam tempoh penapisan semasa.",
        "",
        "## 2. Lima isu utama",
    ]
    for i, iss in enumerate(top_issues[:5], 1):
        lines.append(f"{i}. **[Persepsi awam / analitik]** {iss}")
    if not top_issues:
        lines.append("*Tiada data isu tersedia.*")

    lines += [
        "",
        "## 3. Naratif paling meningkat",
        f"**[Analitik]** {rising or 'Tiada peningkatan ketara diperhatikan.'}",
        "",
        "## 4. Kawasan paling terkesan",
        ", ".join(areas) if areas else "Tiada data kawasan.",
        "",
        "## 5. Sentimen keseluruhan",
        f"**[Analitik]** Peratus negatif: {neg_pct:.1f}%",
        "",
        "## 6. Risiko utama",
    ]
    for r in risks:
        lines.append(f"- **[Analitik]** {r}")
    if not risks:
        lines.append("*Tiada risiko tinggi/kritikal dalam penapisan semasa.*")

    lines += ["", "## 7. Dakwaan yang memerlukan semakan fakta"]
    for m in misinfo:
        lines.append(f"- **[Belum disahkan]** {str(m)[:120]}…")
    if not misinfo:
        lines.append("*Tiada dakwaan maklumat salah dalam penapisan.*")

    lines += ["", "## 8. Aduan perkhidmatan"]
    nc = len(complaints) if complaints is not None and not complaints.empty else 0
    lines.append(f"**[Fakta operasi]** {nc} aduan direkod / dikesan.")

    lines += ["", "## 9. Cadangan tindakan 24 jam"]
    if actions is not None and not actions.empty:
        for _, a in actions.head(5).iterrows():
            lines.append(f"- **[Cadangan — semakan manusia wajib]** {a.get('action_id', '')}: {a.get('recommended_action', '')[:100]}")
    else:
        lines.append("*Tiada tindakan strategik direkod.*")

    lines += ["", "## 10. Tindakan tertunggak"]
    for p in pending:
        lines.append(f"- {p}")
    if not pending:
        lines.append("*Tiada tindakan tertunggak.*")

    lines += [
        "",
        "## 11. Pemerhatian selepas tindakan terdahulu",
        "**[Analitik]** Perubahan selepas tindakan — hubungan masa yang diperhatikan; memerlukan semakan lanjut. "
        "Jangan tafsir sebagai hubungan sebab-akibat tanpa reka bentuk data yang menyokong.",
        "",
        "---",
        "*Nota: Laporan membezakan fakta disahkan, persepsi awam, dakwaan belum disahkan, pemerhatian analitik dan cadangan tindakan.*",
    ]
    return "\n".join(lines)
