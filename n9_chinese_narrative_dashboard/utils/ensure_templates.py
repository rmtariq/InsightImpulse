"""Ensure operational CSV/config templates exist with sample records."""
from __future__ import annotations

import pandas as pd

from utils.storage import CONFIG_DIR, DATA_DIR, config_path, data_path, ensure_dirs, load_csv, save_csv


def _write_if_missing(path, df: pd.DataFrame):
    if not path.exists():
        save_csv(df, path)


def ensure_all_templates():
    ensure_dirs()

    strategic = pd.DataFrame([
        {
            "action_id": "ACT-WATER-N02-FB",
            "issue_cluster": "Water Supply",
            "detected_narrative": "Seremban kawasan X gangguan air 2 hari",
            "narrative_summary": "Gangguan air Seremban",
            "location": "Seremban",
            "dun": "N02",
            "platform": "Facebook",
            "volume": 12,
            "sentiment": "negative",
            "negative_percentage": 78.0,
            "total_engagement": 3400,
            "growth_percentage": 45.0,
            "risk_level": "Medium",
            "evidence_status": "Sebahagian",
            "recommended_action_type": "Respons perkhidmatan",
            "recommended_action": "Semak aduan dengan SYABAS, kenal pasti lokasi terjejas.",
            "recommendation_reason": "Isu bekalan air dengan sentimen negatif tinggi.",
            "responsible_team": "Local Operations",
            "due_date": "2026-06-12",
            "action_status": "Baharu",
            "verification_required": True,
            "notes": "",
            "priority_score": 0.72,
        },
    ])
    _write_if_missing(data_path("strategic_actions.csv"), strategic)

    responses = pd.DataFrame([
        {
            "draft_id": "DRF-001",
            "action_id": "ACT-WATER-N02-FB",
            "original_narrative": "Air putih tiada 2 hari",
            "translated_text": "Tiada air bersih selama 2 hari",
            "source_url": "https://facebook.com/example",
            "issue_cluster": "Water Supply",
            "sentiment": "negative",
            "engagement": 3400,
            "risk_level": "Medium",
            "available_evidence": "Agency notice pending",
            "response_objective": "Memberikan status tindakan",
            "proposed_response": "Pasukan berkaitan sedang menyemak.",
            "draft_social": "",
            "draft_statement": "",
            "draft_faq": "",
            "approval_status": "Menunggu Semakan",
        },
    ])
    _write_if_missing(data_path("response_drafts.csv"), responses)

    complaints = pd.DataFrame([
        {
            "complaint_id": "CMP-001",
            "detected_at": "2026-06-01",
            "issue_type": "gangguan air",
            "description": "Lokasi Taman X tiada air",
            "source_url": "https://facebook.com/example2",
            "platform": "Facebook",
            "location": "Seremban",
            "dun": "N02",
            "district": "Seremban",
            "agency_responsible": "SYABAS",
            "assigned_officer": "",
            "verification_status": "Perlu Disahkan",
            "complaint_status": "Dikesan",
            "action_taken": "",
            "date_action_started": "",
            "date_resolved": "",
            "resolution_evidence": "",
            "public_update_url": "",
            "citizen_feedback": "",
            "post_action_sentiment": "",
        },
    ])
    _write_if_missing(data_path("complaints.csv"), complaints)

    scenarios = pd.DataFrame([
        {"scenario_id": "A", "scenario_name": "Independent party positioning", "dimension": "message clarity", "score": 3, "political_arrangement_status": "Unconfirmed", "notes": ""},
        {"scenario_id": "B", "scenario_name": "Coordinated coalition positioning", "dimension": "message clarity", "score": 4, "political_arrangement_status": "Under discussion", "notes": ""},
    ])
    _write_if_missing(data_path("scenario_scores.csv"), scenarios)

    interventions = pd.DataFrame([
        {
            "intervention_id": "INT-001",
            "action_id": "ACT-WATER-N02-FB",
            "issue_cluster": "Water Supply",
            "location": "Seremban",
            "intervention_type": "Respons perkhidmatan",
            "intervention_date": "2026-06-05",
            "baseline_start": "2026-05-20",
            "baseline_end": "2026-06-04",
            "monitoring_start": "2026-06-06",
            "monitoring_end": "2026-06-12",
            "baseline_volume": 15,
            "post_action_volume": 8,
            "baseline_negative_percentage": 75.0,
            "post_action_negative_percentage": 55.0,
            "baseline_engagement": 4000,
            "post_action_engagement": 2200,
            "baseline_risk_score": 0.7,
            "post_action_risk_score": 0.5,
            "issue_resolution_status": "Dalam pemantauan",
            "result_summary": "Perubahan selepas tindakan — memerlukan semakan lanjut.",
        },
    ])
    _write_if_missing(data_path("interventions.csv"), interventions)

    evidence = pd.DataFrame([
        {
            "evidence_id": "EVD-001",
            "narrative_id": "ACT-WATER-N02-FB",
            "evidence_type": "Agency notice",
            "title": "Notis gangguan bekalan air",
            "source_name": "SYABAS",
            "source_url": "https://syabas.com.my",
            "publication_date": "2026-06-01",
            "retrieved_at": "2026-06-02",
            "evidence_summary": "Notis rasmi gangguan berjadual.",
            "reliability_level": "High",
            "verification_status": "Verified",
            "verified_by": "Fact Checker",
            "supporting_or_contradicting": "Supporting",
            "attachment_path": "",
            "notes": "",
        },
    ])
    _write_if_missing(data_path("evidence_register.csv"), evidence)

    briefs = pd.DataFrame(columns=["brief_date", "brief_html", "generated_by"])
    _write_if_missing(data_path("daily_briefs.csv"), briefs)

    audit = pd.DataFrame(columns=[
        "timestamp", "user_role", "module", "record_id", "action",
        "previous_value", "new_value", "notes",
    ])
    _write_if_missing(data_path("audit_log.csv"), audit)

    playbook_rows = [
        ("Cost of Living", "Harga barang, pendapatan dan kemampuan isi rumah", "Official price data, assistance programme information and eligibility requirements", "Explain available assistance and practical action", "Penjelasan dasar", "Blaming an ethnic, religious or demographic group", "Policy and Communications", "Normal"),
        ("Chinese Education", "Peruntukan sekolah, kebajikan murid dan dasar pendidikan", "Official education policy, allocation records", "Explain policy and open dialogue", "Dialog komuniti terbuka", "Racial stereotyping of communities", "Policy", "Normal"),
        ("SME and Business", "Lesen, kos operasi, bantuan PKS", "License requirements, grant programmes", "Provide verified business support information", "Kandungan penerangan", "Targeting merchants by ethnicity", "Policy", "Normal"),
        ("Local Government Services", "Perkhidmatan tempatan dan aduan harian", "Agency records, service status", "Acknowledge and provide action status", "Respons perkhidmatan", "Blaming local communities", "Local Operations", "Normal"),
        ("Water Supply", "Gangguan air dan bekalan", "Agency notices, repair timeline", "Service update with verified facts", "Respons perkhidmatan", "Unverified outage claims", "Local Operations", "Normal"),
        ("Road and Traffic", "Jalan rosak, kesesakan", "JKR/MBNS records", "Repair status and timeline", "Penyelesaian aduan", "Politicising infrastructure", "Local Operations", "Normal"),
        ("Public Safety", "Jenayah, keselamatan", "PDRM statistics where public", "Inform with verified data", "Kandungan penerangan", "Fear-based messaging", "Communications", "High"),
        ("Employment", "Peluang kerja, upah", "Official labour statistics", "Explain programmes", "Penjelasan dasar", "Demographic targeting", "Policy", "Normal"),
        ("Housing", "Perumahan mampu milik", "Housing agency data", "Explain eligibility and status", "Penjelasan dasar", "Scapegoating", "Policy", "Normal"),
        ("Economic Development", "Pelaburan negeri", "Official economic reports", "Explain development plans", "Sidang media", "Unverified investment claims", "Policy", "Normal"),
        ("State Government Stability", "Kestabilan pentadbiran", "Official statements", "Factual governance update", "Penjelasan dasar", "Personal attacks", "Communications", "High"),
        ("Youth and Undi18", "Penglibatan belia", "Youth programme data", "Inform and invite dialogue", "Dialog komuniti terbuka", "Youth manipulation", "Community Engagement", "Normal"),
        ("Race and Religion", "Naratif sensitif perkauman/agama", "Two independent verified sources minimum", "Fact correction only with evidence", "Semakan fakta", "Any racial or religious attack", "Legal Review", "Critical"),
        ("Misinformation", "Dakwaan tidak disahkan", "Two independent sources", "Correct with evidence only", "Semakan fakta", "Immediate unverified rebuttal", "Fact Checking", "Critical"),
        ("Political Party Narratives", "Parti dan koalisi", "Official party statements", "Policy explanation without attacks", "Penjelasan dasar", "Ethnic or religious persuasion", "Communications", "High"),
    ]
    playbook = pd.DataFrame(playbook_rows, columns=[
        "issue_cluster", "public_concern", "evidence_required", "recommended_response_objective",
        "recommended_action_type", "prohibited_approach", "responsible_team", "review_level",
    ])
    _write_if_missing(config_path("narrative_playbook.csv"), playbook)

    alerts = pd.DataFrame([
        {"rule_id": "R1", "rule_name": "Volume +50%", "condition": "growth_percentage > 50", "threshold": 50, "enabled": True, "notes": "In-dashboard only"},
        {"rule_id": "R2", "rule_name": "Negatif >65%", "condition": "negative_pct > 65", "threshold": 65, "enabled": True, "notes": ""},
        {"rule_id": "R3", "rule_name": "Misinfo engagement", "condition": "misinfo_engagement > 1000", "threshold": 1000, "enabled": True, "notes": ""},
        {"rule_id": "R4", "rule_name": "Race/religion High/Critical", "condition": "risk_level in High,Critical AND issue Race and Religion", "threshold": 0, "enabled": True, "notes": ""},
        {"rule_id": "R5", "rule_name": "Complaint 3+ sources", "condition": "same issue 3 sources", "threshold": 3, "enabled": True, "notes": ""},
        {"rule_id": "R6", "rule_name": "SLA breach", "condition": "open complaint > SLA days", "threshold": 14, "enabled": True, "notes": ""},
        {"rule_id": "R7", "rule_name": "High-risk institution mention", "condition": "candidate/institution in high risk", "threshold": 0, "enabled": True, "notes": ""},
        {"rule_id": "R8", "rule_name": "Duplicate text burst", "condition": "identical text multiple accounts", "threshold": 3, "enabled": True, "notes": ""},
    ])
    _write_if_missing(config_path("alert_rules.csv"), alerts)


def merge_actions(candidates: pd.DataFrame) -> pd.DataFrame:
    """Merge generated candidates with saved strategic_actions.csv."""
    ensure_all_templates()
    saved = load_csv(data_path("strategic_actions.csv"))
    if candidates is None or candidates.empty:
        return saved
    if saved.empty:
        return candidates
    merged = candidates.copy()
    for col in saved.columns:
        if col not in merged.columns:
            merged[col] = ""
    for _, s in saved.iterrows():
        aid = s.get("action_id")
        mask = merged["action_id"] == aid
        if mask.any():
            for c in ["responsible_team", "due_date", "action_status", "notes", "verification_required"]:
                if c in s.index and pd.notna(s[c]) and str(s[c]).strip():
                    merged.loc[mask, c] = s[c]
        else:
            merged = pd.concat([merged, pd.DataFrame([s])], ignore_index=True)
    return merged.sort_values("priority_score", ascending=False) if "priority_score" in merged.columns else merged
