#!/usr/bin/env python3
"""
InsightPulse - Simple Test Server
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="InsightPulse Test API")

@app.get("/")
async def root():
    return {
        "message": "✅ InsightPulse API is Working!",
        "project_cost": "RM 3,200,000",
        "status": "Ready for Development",
        "access_urls": {
            "main": "http://localhost:8080",
            "docs": "http://localhost:8080/docs"
        }
    }

@app.get("/test")
async def test():
    return {"test": "success", "message": "API is responding correctly!"}

if __name__ == "__main__":
    print("🚀 Starting InsightPulse Test Server...")
    print("💰 Project Investment: RM 3,200,000")
    print("")
    print("🌐 Try these URLs in your browser:")
    print("   http://localhost:8080")
    print("   http://localhost:8080/docs")
    print("   http://localhost:8080/test")
    print("")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8080,
        reload=False
    )
