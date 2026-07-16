"""
API Endpoint for analyzing existing CSV files
Allows users to upload or select existing CSV files for analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import shutil
from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard

router = APIRouter()

class AnalyzeCSVRequest(BaseModel):
    csv_path: str
    topic_name: str
    filter_days: Optional[int] = 90

class CSVFileInfo(BaseModel):
    filename: str
    path: str
    size: int
    modified_date: str

@router.get("/api/list-csvs")
async def list_existing_csvs():
    """
    List all available CSV files in data/combined/
    """
    try:
        combined_dir = Path("data/combined")
        
        if not combined_dir.exists():
            return {"csvs": []}
        
        csv_files = []
        for csv_file in combined_dir.glob("*.csv"):
            stats = csv_file.stat()
            csv_files.append({
                "filename": csv_file.name,
                "path": str(csv_file),
                "size": stats.st_size,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "modified_date": stats.st_mtime
            })
        
        # Sort by modified date (newest first)
        csv_files.sort(key=lambda x: x["modified_date"], reverse=True)
        
        return {
            "success": True,
            "count": len(csv_files),
            "csvs": csv_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing CSVs: {str(e)}")

@router.post("/api/analyze-csv")
async def analyze_csv(request: AnalyzeCSVRequest):
    """
    Analyze an existing CSV file with Universal Intelligence Dashboard
    """
    try:
        csv_path = request.csv_path
        topic_name = request.topic_name
        filter_days = request.filter_days or 90
        
        # Validate CSV exists
        if not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")
        
        # Run analysis
        analyzer = UniversalIntelligenceDashboard(csv_path, topic_name=topic_name)
        insights = analyzer.analyze(filter_days=filter_days)
        
        # Export results
        output_dir = Path(f"reports/universal_analysis_{topic_name.replace(' ', '_')}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        analyzer.export_to_json(str(output_dir / "insights.json"))
        analyzer.export_cleaned_data(str(output_dir / "cleaned_data.csv"))
        
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "topic": topic_name,
            "insights": insights,
            "output_dir": str(output_dir),
            "files": [
                str(output_dir / "insights.json"),
                str(output_dir / "cleaned_data.csv")
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a new CSV file for analysis
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": str(file_path),
            "size": file_path.stat().st_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
