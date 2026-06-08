#!/usr/bin/env python3
"""
KDEBWM Lightweight Analytics Server
Runs ONLY the KDEBWM dashboard + analytics API on port 8002.
No ML models needed - just analytics from existing CSV data.

Usage:
    python kdebwm_server.py
    Then open: http://localhost:8002/
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KDEBWM Complaint Analytics", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (KDEBWM dashboard)
static_path = Path(__file__).parent / "web_backend" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to KDEBWM dashboard"""
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/static/kdebwm_dashboard.html">
    </head>
    <body>
        <p>Redirecting to <a href="/static/kdebwm_dashboard.html">KDEBWM Dashboard</a>...</p>
    </body>
    </html>
    """


@app.get("/api/list-csvs")
async def list_csvs():
    """List available CSV files in data/combined/"""
    combined_dir = Path("data/combined")
    if not combined_dir.exists():
        return {"success": True, "count": 0, "csvs": []}

    csv_files = []
    for f in sorted(combined_dir.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True):
        stats = f.stat()
        csv_files.append({
            "filename": f.name,
            "path": str(f),
            "size": stats.st_size,
            "size_mb": round(stats.st_size / (1024 * 1024), 2),
            "modified_date": stats.st_mtime
        })

    return {"success": True, "count": len(csv_files), "csvs": csv_files}


class KDEBWMRequest(BaseModel):
    csv_path: str
    filter_days: Optional[int] = 30
    export_results: Optional[bool] = True


@app.post("/api/kdebwm/analyze")
async def analyze_kdebwm(request: KDEBWMRequest):
    """Run KDEBWM complaint analytics"""
    try:
        from backend.services.kdebwm_analytics import KDEBWMComplaintAnalytics

        csv_path = request.csv_path
        filter_days = request.filter_days or 30

        logger.info(f"Analyzing: {csv_path}")

        if not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV not found: {csv_path}")

        analyzer = KDEBWMComplaintAnalytics(csv_path)
        results = analyzer.analyze(filter_days=filter_days)

        if request.export_results:
            out_dir = Path("reports/kdebwm_complaint_analytics")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            analyzer.export_to_json(str(out_dir / f"kdebwm_analytics_{ts}.json"))
            analyzer.export_complaints_csv(str(out_dir / f"kdebwm_complaints_{ts}.csv"))
            with open(out_dir / f"executive_summary_{ts}.txt", 'w') as f:
                f.write(results['executive_summary'])

        return {
            "success": True,
            "message": "KDEBWM analysis complete",
            "results": results,
            "metadata": results['metadata']
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "KDEBWM Analytics Server", "port": 8002}


if __name__ == "__main__":
    print("=" * 60)
    print("KDEBWM Complaint Analytics Server")
    print("=" * 60)
    print("Starting on http://localhost:8002")
    print("Dashboard: http://localhost:8002/static/kdebwm_dashboard.html")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
