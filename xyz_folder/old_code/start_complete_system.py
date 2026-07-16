#!/usr/bin/env python3
"""
Complete InsightPulse System Starter
Integrates 7-platform crawlers with enhanced analytics
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path
import requests

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_existing_backend():
    """Start the existing backend API"""
    project_root = Path(__file__).parent
    backend_path = project_root / "backend" / "api.py"
    
    print("🔧 Starting existing backend API...")
    os.chdir(project_root)
    
    try:
        subprocess.run([sys.executable, str(backend_path)], check=True)
    except Exception as e:
        print(f"❌ Backend error: {e}")

def start_enhanced_frontend():
    """Start the enhanced frontend"""
    project_root = Path(__file__).parent
    frontend_path = project_root / "enhanced_web_app.py"
    
    print("🚀 Starting enhanced frontend...")
    os.chdir(project_root)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(frontend_path), 
            "--server.port", "8501"
        ], check=True)
    except Exception as e:
        print(f"❌ Frontend error: {e}")

def main():
    print("🎯 InsightPulse - Complete 7-Platform System")
    print("="*60)
    print("🕷️ Integrating existing crawlers with enhanced analytics")
    print("📊 Platforms: Facebook, Instagram, X, TikTok, Google, News, Lowyat")
    print("="*60)
    
    project_root = Path(__file__).parent
    
    # Check if required files exist
    backend_path = project_root / "backend" / "api.py"
    enhanced_frontend = project_root / "enhanced_web_app.py"
    
    if not backend_path.exists():
        print(f"❌ Backend not found: {backend_path}")
        print("💡 Make sure you're in the InsightPulse project directory")
        sys.exit(1)
    
    if not enhanced_frontend.exists():
        print(f"❌ Enhanced frontend not found: {enhanced_frontend}")
        sys.exit(1)
    
    # Check for crawler data
    data_path = project_root / "data" / "smart_crawlers"
    if not data_path.exists():
        print("⚠️ Warning: No crawler data directory found")
        print("💡 Run crawlers first to see real data")
    else:
        # Count available data
        platforms = ["facebook", "instagram", "x", "tiktok", "google", "news", "lowyat"]
        available_data = []
        for platform in platforms:
            platform_path = data_path / platform
            if platform_path.exists() and list(platform_path.glob("*.csv")):
                available_data.append(platform)
        
        print(f"📊 Found data for {len(available_data)} platforms: {', '.join(available_data)}")
    
    # Start backend in background
    print("\n🚀 Step 1: Starting backend API...")
    backend_thread = threading.Thread(target=start_existing_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend
    print("⏳ Waiting for backend to start...")
    for i in range(30):
        if check_backend():
            print("✅ Backend API is ready!")
            break
        time.sleep(1)
        print(f"   Checking... ({i+1}/30)")
    else:
        print("⚠️ Backend taking longer than expected, starting frontend anyway...")
    
    # Start enhanced frontend
    print("\n🚀 Step 2: Starting enhanced frontend...")
    print("\n" + "="*60)
    print("🎯 InsightPulse Enhanced System Starting...")
    print("🔧 Backend API: http://localhost:8000")
    print("🖥️ Enhanced Frontend: http://localhost:8501")
    print("📊 Features:")
    print("   • Real-time 7-platform data analysis")
    print("   • Live crawler status monitoring")
    print("   • Advanced sentiment analysis")
    print("   • Interactive data exploration")
    print("   • Automated report generation")
    print("="*60)
    
    try:
        start_enhanced_frontend()
    except KeyboardInterrupt:
        print("\n🛑 InsightPulse stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
