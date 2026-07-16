#!/usr/bin/env python3
"""
PRN War Room LIVE — dashboard + Digital Culaan + Action Center API.

Usage:
  python3 scripts/prn_digital_cula_server.py [--port 8080]

Endpoints:
  POST   /api/cula/submit
  GET    /api/cula/submissions?state=N9&status=pending|verified|rejected|all
  PATCH  /api/cula/review
  GET    /api/cula/hub?state=N9
  GET    /api/cula/duns?state=N9
  POST   /api/cula/rebuild?state=N9
  GET    /api/cula-socmed/plan?state=N9&kod_dun=N10&trek=lokaliti
  GET    /api/cula-socmed/seeds?state=N9
  POST   /api/cula-socmed/seed
  PATCH  /api/cula-socmed/seed
  GET    /api/cula-socmed/due?state=N9
  POST   /api/cula-socmed/crawl
  GET    /api/cula-socmed/hub?state=N9
  GET    /api/action-center?state=N9
  POST   /api/action-center/action
  PATCH  /api/action-center/action
  GET    /api/pulse-digital?state=N9
  GET    /api/ml/predict/prn_n9?refresh=0|1   (ML analytics — SVM/RF/DT)
  POST   /api/content/generate   (Content Studio: FB/IG, TikTok, prompt video — templat + hook LLM/RAG)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from digital_cula_lib import (  # noqa: E402
    STATES,
    add_submission,
    bulk_import,
    init_all_states,
    load_dun_catalog,
    parse_csv_upload,
    parse_whatsapp_lines,
    read_submissions,
    rebuild_hub,
    review_submission,
    template_csv_text,
)
from digital_cula_socmed_lib import (  # noqa: E402
    create_seed,
    get_plan,
    list_due,
    load_seeds,
    rebuild_socmed_hub,
    trigger_crawl,
    update_seed,
)

PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype"
PRN_REACT = PROTO / "insightpulse" / "prn-monitoring"
LIVE_ROOT = ROOT / "data/projects/political/PRN/warroom_live"
ACTION_STATUSES = {"baru", "sedang_dibuat", "siap", "ditangguh"}


def now_myt_iso() -> str:
    # Store a simple local timestamp; dashboard is operated in MYT.
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def action_source_path(state: str) -> Path:
    state_key = "n9" if state == "N9" else state.lower()
    candidate = PROTO / "data" / f"{state_key}_actions_v2.json"
    if candidate.exists():
        return candidate
    return PROTO / "data" / "n9_actions_v2.json"


def action_status_path(state: str) -> Path:
    return LIVE_ROOT / state / "action_status.json"


def custom_actions_path(state: str) -> Path:
    return LIVE_ROOT / state / "custom_actions.json"


def cula_generated_actions_path(state: str) -> Path:
    return LIVE_ROOT / state / "cula_generated_actions.json"


ISSUE_LABEL_BM = {
    "Cost of Living": "Kos Sara Hidup",
    "SME and Business": "PKS & Perniagaan",
    "Local Government Services": "Perkhidmatan Kerajaan Tempatan",
    "Employment": "Pekerjaan",
    "Candidate Performance": "Prestasi Calon",
    "Misinformation": "Salah Maklumat",
    "DAP Performance": "Prestasi DAP",
    "Chinese Education": "Pendidikan Cina",
    "PAS Factor": "Faktor PAS",
}


def _issue_bm(label: str) -> str:
    return ISSUE_LABEL_BM.get(label or "", label or "Isu Komuniti")


def _llm_ready() -> bool:
    """RAG + VectorDB + LLM hook flag. Set salah satu env var untuk aktif."""
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("PRN_LLM_ENDPOINT")
    )


def generate_content_pack(item: dict) -> dict:
    """Template-based content generator (offline, copy & paste ready).

    Titik integrasi masa depan:
      1. Embed `item` + evidence ke VectorDB, dapatkan konteks RAG terdekat.
      2. Hantar konteks + template ke LLM (lihat lib/ai/content-generator.js).
      3. Kembalikan output LLM dengan ai_ready=True.
    Buat masa ini kita pulangkan templat berstruktur supaya pasukan boleh terus guna.
    """
    dun = item.get("dun") or "N9"
    seat = item.get("seat") or item.get("nama_dun") or ""
    raw_issue = (
        item.get("issue_cluster")
        or (str(item.get("title") or "").split("—")[0].strip())
        or item.get("category")
        or "Isu Komuniti"
    )
    issue = _issue_bm(raw_issue)
    platform = item.get("platform") or "Facebook"
    sentiment = item.get("sentiment_summary") or item.get("sentiment") or "campuran"
    recommended = (
        item.get("recommended_action")
        or (item.get("recommended_steps") or ["Sediakan respons komunikasi yang jelas."])[0]
    )
    label = seat or dun
    tags = " ".join(
        t for t in [
            "#PRNNegeriSembilan", "#N9", f"#{dun}" if dun else "",
            f"#{seat.replace(' ', '')}" if seat else "",
        ] if t
    )
    fb_ig = "\n".join([
        f"Kami dengar suara warga {label} tentang {issue.lower()}.",
        "",
        "Apa yang kami buat:",
        "• [Isi 1 fakta/inisiatif sebenar di sini]",
        "• [Isi 1 lagi langkah konkrit]",
        "",
        "Apa anda boleh buat:",
        "👉 [CTA: hadir program / hubungi pejabat khidmat / kongsi maklumat sahih]",
        "",
        tags,
    ])
    tiktok = "\n".join([
        f"JUDUL: {issue} — {label}",
        "FORMAT: 9:16 · 25–35 saat · sari kata BM",
        "",
        f'[0–3s] HOOK: "{issue} — kami ambil tindakan"',
        "[3–10s] MASALAH: nyatakan isu rakyat secara jujur.",
        "[10–20s] JAWAPAN: tunjuk apa yang sedang dibuat — [isi fakta].",
        f"[20–27s] BUKTI: rakam aktiviti sebenar di {label}.",
        '[27–32s] CTA: "Sertai kami. Sebarkan maklumat yang sahih."',
        "",
        f"Caption: {issue} di {label}. {recommended}",
        tags,
    ])
    video_prompt = "\n".join([
        "Cipta video pendek menegak (9:16), 30 saat, gaya dokumentari komuniti Malaysia.",
        f"Lokasi: {label}, Negeri Sembilan. Subjek: {issue.lower()}.",
        "Nada: harapan, mesra, beramanah.",
        "Babak: (1) lokasi tempatan, (2) teks isu, (3) aktiviti tindakan, (4) CTA.",
        "Elakkan: dakwaan tidak disahkan, imej sensitif.",
    ])
    insight = "\n".join([
        f"Apa berlaku: Signal {issue} di {label} · sentimen {sentiment}.",
        "Kenapa penting: boleh mempengaruhi persepsi pengundi jika tidak dijawab.",
        f"Tindakan disyorkan: {recommended}",
        "KPI: engagement, anjakan sentimen, komen positif 24–48 jam.",
    ])
    return {
        "mode": "template",
        "ai_ready": _llm_ready(),
        "platform": platform,
        "insight": insight,
        "fb_ig": fb_ig,
        "tiktok": tiktok,
        "video_prompt": video_prompt,
        "hashtags": tags,
    }


def load_action_center(state: str) -> dict:
    base = read_json(action_source_path(state), {"meta": {}, "actions": [], "pulseDigital": [], "programOps": [], "dailyBriefing": {}})
    statuses = read_json(action_status_path(state), {"actions": {}})
    cula_gen = read_json(cula_generated_actions_path(state), {"actions": []})
    custom = read_json(custom_actions_path(state), {"actions": []})
    by_id: dict = {}
    for action in list(base.get("actions") or []):
        aid = action.get("id")
        if aid:
            by_id[aid] = dict(action)
    for action in list(cula_gen.get("actions") or []):
        aid = action.get("id")
        if aid:
            by_id[aid] = dict(action)
    for action in list(custom.get("actions") or []):
        aid = action.get("id")
        if aid:
            by_id[aid] = dict(action)
    status_map = statuses.get("actions") or {}
    merged = []
    for action in by_id.values():
        row = dict(action)
        live = status_map.get(row.get("id")) or {}
        if live:
            row.update({k: v for k, v in live.items() if v not in (None, "")})
        merged.append(row)
    payload = dict(base)
    payload["actions"] = merged
    payload["live"] = {
        "enabled": True,
        "state": state,
        "status_store": str(action_status_path(state).relative_to(ROOT)),
        "custom_store": str(custom_actions_path(state).relative_to(ROOT)),
        "cula_store": str(cula_generated_actions_path(state).relative_to(ROOT)),
        "cula_actions_count": len(cula_gen.get("actions") or []),
        "updated": now_myt_iso(),
    }
    return payload


def update_action_status(state: str, action_id: str, patch: dict) -> dict:
    store = read_json(action_status_path(state), {"actions": {}})
    actions = store.setdefault("actions", {})
    current = actions.setdefault(action_id, {})
    current.update(
        {
            "status": patch.get("status") or current.get("status") or "baru",
            "status_note": patch.get("status_note") or patch.get("note") or current.get("status_note", ""),
            "impact_result": patch.get("impact_result") or current.get("impact_result", ""),
            "updated_by": patch.get("updated_by") or patch.get("owner") or current.get("updated_by", "war-room"),
            "updated_at": now_myt_iso(),
        }
    )
    write_json(action_status_path(state), store)
    return current


class WarRoomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROTO), **kwargs)

    def log_message(self, fmt, *args):
        if str(args[0]).startswith("GET /api/") or "POST /api/" in str(args):
            super().log_message(fmt, *args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_bytes(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_prn_react(self, parsed_path: str) -> bool:
        """Serve built React PRN Monitoring app (SPA)."""
        prefix = "/insightpulse/prn-monitoring"
        if not parsed_path.startswith(prefix):
            return False
        if parsed_path == prefix:
            self.send_response(301)
            self.send_header("Location", prefix + "/")
            self.end_headers()
            return True
        rel = parsed_path[len(prefix) :].lstrip("/") or "index.html"
        target = (PRN_REACT / rel).resolve()
        root = PRN_REACT.resolve()
        if not str(target).startswith(str(root)):
            self._send_json(403, {"ok": False, "error": "Forbidden"})
            return True
        if target.is_file():
            ctype = "application/octet-stream"
            if target.suffix == ".html":
                ctype = "text/html; charset=utf-8"
            elif target.suffix == ".js":
                ctype = "application/javascript; charset=utf-8"
            elif target.suffix == ".css":
                ctype = "text/css; charset=utf-8"
            elif target.suffix == ".json":
                ctype = "application/json; charset=utf-8"
            self._send_bytes(200, target.read_bytes(), ctype)
            return True
        index = PRN_REACT / "index.html"
        if index.is_file():
            self._send_bytes(200, index.read_bytes(), "text/html; charset=utf-8")
            return True
        self._send_json(404, {"ok": False, "error": "PRN React dashboard not built. Run: bash scripts/build_prn_react_dashboard.sh"})
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if self._serve_prn_react(parsed.path):
            return

        if parsed.path == "/api/cula/duns":
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            catalog = load_dun_catalog(state)
            duns = [{"kod_dun": k, "name": v} for k, v in sorted(catalog.items())]
            return self._send_json(200, {"ok": True, "state": state, "duns": duns})

        if parsed.path == "/api/cula/hub":
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            hub = rebuild_hub(state)
            return self._send_json(200, {"ok": True, "hub": hub, "action_center": True})

        if parsed.path == "/api/cula/submissions":
            state = (qs.get("state") or ["N9"])[0]
            status = (qs.get("status") or ["all"])[0].lower()
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            rows = read_submissions(state)
            if status != "all":
                rows = [r for r in rows if (r.get("status") or "pending").lower() == status]
            rows = list(reversed(rows))
            return self._send_json(200, {"ok": True, "state": state, "submissions": rows})

        if parsed.path == "/api/cula/template.csv" or parsed.path == "/api/cula/template-empty.csv":
            name = "TEMPLATE_culaan_KOSONG.csv" if "empty" in parsed.path else "TEMPLATE_culaan.csv"
            fpath = ROOT / "data/projects/political/PRN/digital_cula" / name
            body = fpath.read_bytes() if fpath.exists() else template_csv_text().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path.startswith("/api/cula/template-") and parsed.path.endswith(".csv"):
            state = parsed.path.replace("/api/cula/template-", "").replace(".csv", "")
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            fpath = ROOT / f"data/projects/political/PRN/digital_cula/TEMPLATE_culaan_{state}.csv"
            if not fpath.exists():
                return self._send_json(404, {"ok": False, "error": "Template tidak dijumpai"})
            body = fpath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="TEMPLATE_culaan_{state}.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/cula/template.docx":
            docx_path = ROOT / "data/projects/political/PRN/digital_cula/BORANG_CULAAN_DIGITAL_PRN.docx"
            if not docx_path.exists():
                self._send_json(404, {"ok": False, "error": "DOCX belum dijana. Jalankan: python3 scripts/generate_culaan_templates.py"})
                return
            body = docx_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.send_header("Content-Disposition", 'attachment; filename="BORANG_CULAAN_DIGITAL_PRN.docx"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/ml/predict/prn_n9":
            refresh = (qs.get("refresh") or ["0"])[0].lower() in ("1", "true", "yes")
            ml_json = PROTO / "data" / "n9_ml_predictions.json"
            try:
                if refresh:
                    sys.path.insert(0, str(ROOT))
                    from backend.ml.predictive_engine import run_prn_n9_ml
                    result = run_prn_n9_ml(write_output=True)
                    return self._send_json(200, {"success": True, "source": "fresh", "result": result})
                if ml_json.exists():
                    cached = json.loads(ml_json.read_text(encoding="utf-8"))
                    return self._send_json(200, {"success": True, "source": "cache", "result": cached})
                sys.path.insert(0, str(ROOT))
                from backend.ml.predictive_engine import run_prn_n9_ml
                result = run_prn_n9_ml(write_output=True)
                return self._send_json(200, {"success": True, "source": "fresh", "result": result})
            except Exception as exc:
                return self._send_json(500, {"success": False, "error": str(exc)})

        if parsed.path == "/api/health":
            return self._send_json(200, {"ok": True, "service": "prn-digital-cula", "states": list(STATES)})

        if parsed.path == "/api/action-center":
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            payload = load_action_center(state)
            return self._send_json(200, {"ok": True, "state": state, "data": payload})

        if parsed.path == "/api/pulse-digital":
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            payload = load_action_center(state)
            seeds = []
            try:
                seeds = load_seeds(state)
            except Exception:
                seeds = []
            return self._send_json(
                200,
                {
                    "ok": True,
                    "state": state,
                    "pulseDigital": payload.get("pulseDigital") or [],
                    "seeds": list(reversed(seeds)),
                    "live": payload.get("live") or {},
                },
            )

        if parsed.path == "/api/cula-socmed/plan":
            state = (qs.get("state") or ["N9"])[0]
            kod = (qs.get("kod_dun") or ["N01"])[0]
            trek = (qs.get("trek") or ["lokaliti"])[0]
            plan = get_plan(state, kod, trek)
            code = 200 if plan.get("ok") else 400
            return self._send_json(code, plan)

        if parsed.path == "/api/cula-socmed/seeds":
            state = (qs.get("state") or ["N9"])[0]
            seeds = load_seeds(state)
            return self._send_json(200, {"ok": True, "state": state, "seeds": list(reversed(seeds))})

        if parsed.path == "/api/cula-socmed/due":
            state = (qs.get("state") or ["N9"])[0]
            due = list_due(state)
            return self._send_json(200, {"ok": True, "state": state, "due": due, "count": len(due)})

        if parsed.path == "/api/cula-socmed/hub":
            state = (qs.get("state") or ["N9"])[0]
            hub = rebuild_socmed_hub(state)
            return self._send_json(200, {"ok": True, "hub": hub})

        if parsed.path in ("/dashboard/n9-full", "/dashboard/n9-full.html"):
            dash = ROOT / "data/projects/political/PRN/PRN_N9/reports/dashboards/prn-negeri-sembilan-dashboard.html"
            if dash.exists():
                body = dash.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return self._send_json(404, {"ok": False, "error": "Dashboard tidak dijumpai"})

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/cula/submit":
            body = self._read_json()
            state = body.get("state") or "N9"
            if state not in STATES:
                return self._send_json(400, {"ok": False, "errors": ["Negeri tidak sah"]})
            reviewer = body.get("reviewer") or body.get("pelapor_id") or body.get("uploader") or "HQ"
            row, errors = add_submission(state, body, auto_verify=True, reviewer=reviewer)
            if errors:
                return self._send_json(400, {"ok": False, "errors": errors, "submission": row})
            msg = "Data diterima — Command Center & Action Center dikemaskini."
            return self._send_json(201, {"ok": True, "submission": row, "message": msg, "action_center": True})

        if parsed.path == "/api/cula/upload":
            body = self._read_json()
            state = body.get("state") or "N9"
            uploader = body.get("uploader") or ""
            mode = body.get("mode") or "csv"  # csv | whatsapp
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            if mode == "whatsapp":
                items = parse_whatsapp_lines(
                    body.get("text") or "",
                    default_tarikh=body.get("tarikh_lawatan") or "",
                    default_pelapor=uploader,
                )
            else:
                items = parse_csv_upload(body.get("csv") or "")
            if not items:
                return self._send_json(400, {"ok": False, "error": "Tiada baris data dijumpai."})
            result = bulk_import(
                state,
                items,
                uploader=uploader,
                auto_verify=True,
                default_tarikh=body.get("tarikh_lawatan") or "",
            )
            return self._send_json(200, result)

        if parsed.path.startswith("/api/cula/rebuild"):
            qs = parse_qs(urlparse(self.path).query)
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            hub = rebuild_hub(state)
            return self._send_json(200, {"ok": True, "hub": hub, "action_center": True})

        if parsed.path == "/api/cula-socmed/seed":
            body = self._read_json()
            state = body.get("state") or "N9"
            row, errors = create_seed(state, body)
            if errors:
                return self._send_json(400, {"ok": False, "errors": errors})
            return self._send_json(201, {"ok": True, "seed": row, "message": "Seed direkod — tandakan posted bila siap hantar."})

        if parsed.path == "/api/cula-socmed/crawl":
            body = self._read_json()
            state = body.get("state") or "N9"
            result = trigger_crawl(
                state,
                seed_ids=body.get("seed_ids"),
                all_ready=bool(body.get("all_ready")),
            )
            code = 200 if result.get("ok") else 503
            return self._send_json(code, result)

        if parsed.path == "/api/action-center/action":
            body = self._read_json()
            state = body.get("state") or "N9"
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            title = (body.get("title") or "").strip()
            if not title:
                return self._send_json(400, {"ok": False, "error": "Tajuk tindakan wajib diisi"})
            custom = read_json(custom_actions_path(state), {"actions": []})
            seq = len(custom.get("actions") or []) + 1
            action = {
                "id": body.get("id") or f"ACT-{state}-LIVE-{seq:03d}",
                "title": title,
                "category": body.get("category") or "lapangan",
                "priority": body.get("priority") or "p2",
                "status": body.get("status") or "baru",
                "owner": body.get("owner") or "HQ Operasi",
                "due": body.get("due") or "Hari ini",
                "dun": body.get("dun") or state,
                "seat": body.get("seat") or "",
                "locality": body.get("locality") or "",
                "reason": body.get("reason") or "Tindakan dimasukkan manual oleh war room.",
                "evidence": body.get("evidence") or ["Input manual war room"],
                "recommended_steps": body.get("recommended_steps") or ["Tetapkan owner", "Laksanakan", "Rekod impak"],
                "impact_metric": body.get("impact_metric") or "Impak tindakan direkod",
                "created_at": now_myt_iso(),
                "created_by": body.get("created_by") or body.get("owner") or "war-room",
            }
            custom.setdefault("actions", []).append(action)
            write_json(custom_actions_path(state), custom)
            return self._send_json(201, {"ok": True, "state": state, "action": action})

        if parsed.path == "/api/content/generate":
            body = self._read_json()
            item = body.get("item") or {}
            if not isinstance(item, dict) or not item:
                return self._send_json(400, {"ok": False, "error": "item diperlukan"})
            content = generate_content_pack(item)
            return self._send_json(200, {"ok": True, "content": content})

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/cula/review":
            body = self._read_json()
            state = body.get("state") or "N9"
            sub_id = body.get("id") or ""
            status = body.get("status") or ""
            reviewer = body.get("reviewer") or ""
            note = body.get("reviewer_note") or ""
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            row, err = review_submission(state, sub_id, status, reviewer, note)
            if err:
                return self._send_json(400, {"ok": False, "error": err})
            return self._send_json(200, {"ok": True, "submission": row})
        if parsed.path == "/api/cula-socmed/seed":
            body = self._read_json()
            seed_id = body.get("id") or ""
            state = body.get("state") or "N9"
            row, err = update_seed(state, seed_id, body)
            if err:
                return self._send_json(400, {"ok": False, "error": err})
            return self._send_json(200, {"ok": True, "seed": row})
        if parsed.path == "/api/action-center/action":
            body = self._read_json()
            state = body.get("state") or "N9"
            action_id = body.get("id") or ""
            status = body.get("status") or ""
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            if not action_id:
                return self._send_json(400, {"ok": False, "error": "ID tindakan wajib diisi"})
            if status and status not in ACTION_STATUSES:
                return self._send_json(400, {"ok": False, "error": "Status tindakan tidak sah"})
            live = update_action_status(state, action_id, body)
            return self._send_json(200, {"ok": True, "state": state, "id": action_id, "status": live})
        self._send_json(404, {"ok": False, "error": "Not found"})


def main() -> None:
    parser = argparse.ArgumentParser(description="PRN War Room + Digital Culaan API")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    init_all_states()
    for st in STATES:
        try:
            rebuild_socmed_hub(st)
        except Exception:
            pass

    server = ThreadingHTTPServer((args.host, args.port), WarRoomHandler)
    print(f"PRN War Room + Digital Culaan API")
    print(f"  War Room:  http://{args.host}:{args.port}/")
    print(f"  Culaan:    http://{args.host}:{args.port}/?module=cula")
    print(f"  API:       http://{args.host}:{args.port}/api/health")
    print(f"  Data: data/projects/political/PRN/digital_cula/{{N9,Johor,Melaka}}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
