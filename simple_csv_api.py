#!/usr/bin/env python3
"""
Simple CSV Analysis API Server
Lightweight server with just the CSV analysis endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from typing import Optional
import uvicorn
import json

app = FastAPI(title="CSV Analysis API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "web_frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CSV Analysis API"}

@app.get("/")
async def read_root():
    return FileResponse("web_frontend/index.html")

@app.get("/api/list-csvs")
async def list_existing_csvs():
    """List all available CSV files in data/combined/"""
    try:
        combined_dir = Path("data/combined")
        
        if not combined_dir.exists():
            return {"success": True, "count": 0, "csvs": []}
        
        csv_files = []
        for csv_file in combined_dir.glob("*.csv"):
            stats = csv_file.stat()
            csv_files.append({
                "filename": csv_file.name,
                "path": str(csv_file),
                "size": stats.st_size,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "modified_date": stats.st_mtime,
                "modified_date_str": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Sort by modified date (newest first)
        csv_files.sort(key=lambda x: x["modified_date"], reverse=True)
        
        return {
            "success": True,
            "count": len(csv_files),
            "csvs": csv_files
        }
    
    except Exception as e:
        print(f"Error listing CSVs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing CSVs: {str(e)}")

@app.post("/api/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload a CSV file to data/combined/"""
    try:
        # Validate file is CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Create directory if doesn't exist
        upload_dir = Path("data/combined")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"✅ Uploaded CSV: {file_path} ({len(content)} bytes)")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        }
    
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

class AnalyzeCSVRequest(BaseModel):
    csv_path: str
    topic_name: str
    filter_days: Optional[int] = 90

@app.post("/api/analyze-csv")
async def analyze_csv_file(request: AnalyzeCSVRequest):
    """Analyze an existing CSV file with Enhanced Intelligence + OpenAI"""
    try:
        import pandas as pd
        from backend.services.csv_cleaner import clean_csv
        from backend.services.universal_intelligence_dashboard import UniversalIntelligenceDashboard
        from backend.services.enhanced_intelligence import EnhancedIntelligence

        csv_path = request.csv_path
        topic_name = request.topic_name
        filter_days = request.filter_days or 90

        print(f"📊 Analyzing CSV: {csv_path} for topic: {topic_name}")

        # Validate CSV exists
        if not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")

        # Step 1: Clean the CSV
        print("🧹 Cleaning CSV...")
        clean_path, clean_df = clean_csv(csv_path, topic_name, output_dir='data/cleanCSV')
        print(f"✅ Cleaned: {clean_path} ({len(clean_df)} records)")

        # Step 2: Run basic analysis on cleaned data
        print("📊 Running basic analysis...")
        analyzer = UniversalIntelligenceDashboard(clean_path, topic_name=topic_name)
        basic_insights = analyzer.analyze(filter_days=filter_days)

        # Step 3: Enhanced analysis with sentiment/emotion breakdown
        print("🎯 Running enhanced analysis...")

        # Load the analyzed data
        analyzed_csv = str(Path(f"reports/universal_analysis_{topic_name.replace(' ', '_')}") / "cleaned_data.csv")
        if Path(analyzed_csv).exists():
            analyzed_df = pd.read_csv(analyzed_csv)
        else:
            analyzed_df = clean_df

        enhanced = EnhancedIntelligence(analyzed_df, topic_name)
        enhanced_insights = enhanced.generate_full_analysis()

        # Step 4: Generate AI-powered strategic insights
        print("🤖 Generating AI insights with GPT-4...")
        ai_insights = await enhanced.generate_ai_insights()

        # Combine all insights
        combined_insights = {
            **basic_insights,
            'enhanced_analysis': enhanced_insights,
            'ai_insights': ai_insights
        }

        # Export results
        output_dir = Path(f"reports/clean_analysis_{topic_name.replace(' ', '_')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save combined insights
        with open(output_dir / "insights.json", 'w', encoding='utf-8') as f:
            json.dump(combined_insights, f, indent=2, ensure_ascii=False)

        analyzer.export_cleaned_data(str(output_dir / "analyzed_data.csv"))

        print(f"✅ Complete analysis saved to: {output_dir}")

        return {
            "success": True,
            "message": "Enhanced analysis completed successfully",
            "topic": topic_name,
            "insights": combined_insights,
            "output_dir": str(output_dir),
            "clean_csv": clean_path,
            "files": {
                "insights_json": str(output_dir / "insights.json"),
                "analyzed_csv": str(output_dir / "analyzed_data.csv"),
                "clean_csv": clean_path
            }
        }

    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting CSV Analysis API on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
