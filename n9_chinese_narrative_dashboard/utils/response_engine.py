"""Draft public response generation (manual review only)."""
from __future__ import annotations

RESPONSE_OBJECTIVES = [
    "Memaklumkan", "Menjelaskan", "Membetulkan fakta", "Mengakui masalah",
    "Memberikan status tindakan", "Mengumumkan penyelesaian", "Mengajak dialog",
    "Menjawab soalan lazim",
]


def pick_objective(issue_cluster: str, sentiment: str, risk: str) -> str:
    ic = str(issue_cluster).lower()
    if "misinformation" in ic or risk in ("High", "Critical"):
        return "Membetulkan fakta"
    if str(sentiment).lower() == "negative":
        return "Mengakui masalah"
    if ic in ("water supply", "road and traffic", "local government services"):
        return "Memberikan status tindakan"
    return "Menjelaskan"


def draft_social(issue: str, action: str, location: str) -> str:
    return (
        f"Kami sedar kebimbangan awam berkaitan {issue}"
        f"{f' di {location}' if location else ''}. "
        f"{action or 'Pasukan berkaitan sedang menyemak maklumat dan akan mengemas kini apabila fakta disahkan.'} "
        "Sila rujuk saluran rasmi untuk maklumat terkini."
    )


def draft_statement(issue: str, narrative: str, action: str) -> str:
    return (
        f"Kenyataan Penerangan — Isu: {issue}\n\n"
        f"Naratif awam yang diperhatikan: {narrative[:200]}…\n\n"
        "Kedudukan rasmi: Kerajaan Negeri Sembilan mengambil serius maklum balas awam. "
        f"{action or 'Semakan dalaman sedang dijalankan.'}\n\n"
        "Maklumat yang belum disahkan tidak akan dikongsi sebagai fakta. "
        "Semua cadangan respons mesti diluluskan pegawai bertanggungjawab sebelum diterbitkan."
    )


def draft_faq(issue: str, action: str) -> str:
    return (
        f"Soalan Lazim — {issue}\n\n"
        f"1. Apakah isu yang dilaporkan?\n   {issue}\n\n"
        f"2. Apakah tindakan kerajaan?\n   {action or 'Semakan sedang dijalankan; kemas kini akan dikeluarkan.'}\n\n"
        "3. Di manakah saya boleh dapat maklumat rasmi?\n   Saluran rasmi agensi negeri dan kerajaan tempatan."
    )


def build_drafts(row: dict) -> dict:
    issue = row.get("issue_cluster", "Isu awam")
    loc = row.get("location", "") or row.get("dun", "")
    narrative = row.get("detected_narrative", row.get("post_text", ""))
    action = row.get("recommended_action", row.get("action_taken", ""))
    obj = pick_objective(issue, row.get("sentiment", ""), row.get("risk_level", "Low"))
    return {
        "response_objective": obj,
        "draft_social": draft_social(issue, action, loc),
        "draft_statement": draft_statement(issue, narrative, action),
        "draft_faq": draft_faq(issue, action),
        "approval_status": "Menunggu Semakan",
    }
