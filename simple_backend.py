#!/usr/bin/env python3
"""
Simple InsightPulse Backend - Minimal Working Version
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
import uvicorn
import json
import random
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="InsightPulse Simple API",
    description="Minimal working version",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class AnalysisRequest(BaseModel):
    query: str
    analysis_type: str = "social_listening"
    platforms: List[str] = ["facebook", "instagram", "twitter"]
    max_results_per_platform: int = 1000

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "InsightPulse Simple API",
        "version": "1.0.0",
        "status": "active"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Analysis endpoint
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """Simple analysis endpoint with mock data"""
    
    # Generate mock results
    results = {
        "analysis_id": f"analysis_{random.randint(1000, 9999)}",
        "query": request.query,
        "platforms": request.platforms,
        "status": "completed",
        "results": {
            "total_mentions": random.randint(1000, 10000),
            "sentiment_score": round(random.uniform(0.6, 0.95), 2),
            "engagement": random.randint(5000, 50000),
            "reach": random.randint(10000, 100000),
            "platforms": {
                platform: {
                    "mentions": random.randint(100, 1000),
                    "sentiment": round(random.uniform(0.6, 0.9), 2),
                    "engagement": random.randint(500, 5000)
                } for platform in request.platforms
            },
            "insights": [
                f"Peak activity detected for '{request.query}'",
                f"Positive sentiment dominates with {random.randint(70, 90)}% approval",
                f"Highest engagement in {random.choice(['Selangor', 'KL', 'Johor', 'Penang'])} region",
                f"Growth potential: {random.randint(15, 45)}% increase expected"
            ],
            "analysis_time": f"{random.randint(15, 25)}.{random.randint(1, 9)} seconds",
            "confidence": random.randint(85, 98)
        },
        "created_at": datetime.now().isoformat()
    }
    
    return results

# Keyword breakdown endpoint
@app.post("/keywords/breakdown")
async def keyword_breakdown(request: dict):
    """Simple keyword breakdown"""
    
    query = request.get("query", "")
    words = query.lower().split()
    
    return {
        "original_query": query,
        "keywords": words,
        "expanded_queries": [
            query,
            f'"{query}"',
            f"{query} malaysia",
            f"{query} trending"
        ],
        "total_variations": len(words) * 4,
        "processing_time": "0.5 seconds"
    }

if __name__ == "__main__":
    print("🚀 Starting Simple InsightPulse Backend...")
    print("📊 Backend will run on: http://localhost:8001")
    print("📖 API docs: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False
    )
