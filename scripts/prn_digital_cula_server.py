#!/usr/bin/env python3
"""
PRN War Room — static prototype + Digital Culaan API (N9, Johor, Melaka).

Usage:
  python3 scripts/prn_digital_cula_server.py [--port 8080]

Endpoints:
  POST   /api/cula/submit
  GET    /api/cula/submissions?state=N9&status=pending|verified|rejected|all
  PATCH  /api/cula/review
  GET    /api/cula/hub?state=N9
  GET    /api/cula/duns?state=N9
  POST   /api/cula/rebuild?state=N9
"""
from __future__ import annotations

import argparse
import json
import sys
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

PROTO = ROOT / "data/projects/political/PRN/PRN_N9/reports/war_room/prototype"


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

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

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
            return self._send_json(200, {"ok": True, "hub": hub})

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

        if parsed.path == "/api/health":
            return self._send_json(200, {"ok": True, "service": "prn-digital-cula", "states": list(STATES)})

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/cula/submit":
            body = self._read_json()
            state = body.get("state") or "N9"
            if state not in STATES:
                return self._send_json(400, {"ok": False, "errors": ["Negeri tidak sah"]})
            auto = bool(body.get("auto_verify"))
            reviewer = body.get("reviewer") or body.get("pelapor_id") or ""
            row, errors = add_submission(state, body, auto_verify=auto, reviewer=reviewer)
            if errors:
                return self._send_json(400, {"ok": False, "errors": errors, "submission": row})
            msg = "Disahkan & dashboard dikemaskini." if auto else "Dihantar — menunggu semakan PDM."
            return self._send_json(201, {"ok": True, "submission": row, "message": msg})

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
            result = bulk_import(state, items, uploader=uploader, auto_verify=True)
            return self._send_json(200, result)

        if parsed.path.startswith("/api/cula/rebuild"):
            qs = parse_qs(urlparse(self.path).query)
            state = (qs.get("state") or ["N9"])[0]
            if state not in STATES:
                return self._send_json(400, {"ok": False, "error": "Negeri tidak sah"})
            hub = rebuild_hub(state)
            return self._send_json(200, {"ok": True, "hub": hub})

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
        self._send_json(404, {"ok": False, "error": "Not found"})


def main() -> None:
    parser = argparse.ArgumentParser(description="PRN War Room + Digital Culaan API")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    init_all_states()

    server = ThreadingHTTPServer((args.host, args.port), WarRoomHandler)
    print(f"PRN War Room + Digital Culaan API")
    print(f"  UI:  http://{args.host}:{args.port}/")
    print(f"  API: http://{args.host}:{args.port}/api/health")
    print(f"  Data: data/projects/political/PRN/digital_cula/{{N9,Johor,Melaka}}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
