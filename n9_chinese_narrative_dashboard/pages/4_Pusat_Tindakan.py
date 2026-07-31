"""Pusat Tindakan — Kanban + Table + Copy panel."""
from __future__ import annotations

import streamlit as st

from components.dashboard_shell import init_dashboard, load_dashboard_data, render_page_shell
from components.negeri_selector import get_selected_negeri
from components.ui.action_center import get_kit_items, render_copy_panel, render_kanban_view, render_table_view
from components.ui.cards import empty_state
from utils.action_engine import ACTION_STATUS, TEAMS, build_action_candidates
from utils.alert_engine import evaluate_alerts
from utils.ensure_templates import merge_actions
from utils.storage import data_path, load_csv, save_csv
from utils.csv_ops import coerce_text_columns

init_dashboard("Pusat Tindakan", "Pusat Tindakan")
render_page_shell("Pusat Tindakan")

df, filtered, _ = load_dashboard_data()
if filtered is None or filtered.empty:
    empty_state("✅", "Tiada Tindakan", "Tiada data untuk dijadikan tindakan.")
    st.stop()

for a in evaluate_alerts(filtered, load_csv(data_path("complaints.csv"))):
    if a["level"] in ("critical", "warning"):
        st.warning(f"⚠️ {a['msg']}")

actions = merge_actions(build_action_candidates(filtered))
negeri = get_selected_negeri()
kit_items = get_kit_items(df, negeri)

view = st.radio("Paparan", ["📋 Table View", "📌 Kanban View", "✍️ Cadangan Posting"], horizontal=True)

if view == "📋 Table View":
    if actions.empty:
        empty_state("📋", "Tiada Tindakan", "Laraskan penapis atau tambah data.")
    else:
        render_table_view(actions)
        st.markdown("#### Kemaskini")
        aid = st.selectbox("Pilih tindakan", actions["action_id"].tolist())
        row = actions[actions["action_id"] == aid].iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            team = st.selectbox("Pasukan", TEAMS)
        with c2:
            due = st.text_input("Tarikh akhir", value=str(row.get("due_date", "")))
        with c3:
            status = st.selectbox("Status", ACTION_STATUS)
        if st.button("Simpan", type="primary"):
            saved = load_csv(data_path("strategic_actions.csv"))
            if saved.empty:
                saved = actions.copy()
            saved = coerce_text_columns(saved, list(saved.columns))
            mask = saved["action_id"] == aid
            if mask.any():
                saved.loc[mask, "responsible_team"] = team
                saved.loc[mask, "due_date"] = due
                saved.loc[mask, "action_status"] = status
            save_csv(saved, data_path("strategic_actions.csv"))
            st.success("Disimpan.")
            st.rerun()

elif view == "📌 Kanban View":
    render_kanban_view(actions)

else:
    if not kit_items:
        empty_state("✍️", "Tiada Copy", "Jana data atau laporan terlebih dahulu.")
    else:
        labels = [f"{i['priority']} — {i['issue']} ({i['location']})" for i in kit_items]
        idx = st.selectbox("Pilih isu untuk cadangan posting", range(len(labels)), format_func=lambda i: labels[i])
        render_copy_panel(kit_items[idx])
        item = kit_items[idx]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("⬇️ Copy BM", item.get("copy_bm_social", ""), file_name="copy_bm.txt")
        with c2:
            st.download_button("⬇️ Copy 中文", item.get("copy_zh_social", ""), file_name="copy_zh.txt")
        with c3:
            if st.button("✅ Mark Reviewed"):
                st.success("Ditanda untuk semakan — belum diterbitkan.")
