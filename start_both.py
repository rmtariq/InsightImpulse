#!/usr/bin/env python3
"""
InsightPulse Complete Starter
Run this to start both backend and frontend automatically
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

def start_backend():
    """Start backend in a separate thread"""
    project_root = Path(__file__).parent
    backend_path = project_root / "backend" / "api.py"
    
    print("🔧 Starting backend...")
    os.chdir(project_root)
    
    try:
        subprocess.run([sys.executable, str(backend_path)], check=True)
    except Exception as e:
        print(f"❌ Backend error: {e}")

def main():
    project_root = Path(__file__).parent
    frontend_path = project_root / "frontend" / "streamlit_app.py"
    
    print("🎯 InsightPulse - Complete Startup")
    print("="*50)
    
    # Check if files exist
    backend_path = project_root / "backend" / "api.py"
    if not backend_path.exists():
        print(f"❌ Backend not found: {backend_path}")
        sys.exit(1)
    
    if not frontend_path.exists():
        print(f"❌ Frontend not found: {frontend_path}")
        sys.exit(1)
    
    # Start backend in background thread
    print("🚀 Step 1: Starting backend...")
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    for i in range(30):  # Wait up to 30 seconds
        if check_backend():
            print("✅ Backend is ready!")
            break
        time.sleep(1)
        print(f"   Checking... ({i+1}/30)")
    else:
        print("⚠️ Backend taking longer than expected, starting frontend anyway...")
    
    # Start frontend
    print("🚀 Step 2: Starting frontend...")
    os.chdir(project_root)
    
    try:
        print("🌐 Opening InsightPulse at http://localhost:8501")
        print("\n" + "="*50)
        print("🎯 InsightPulse is starting...")
        print("📊 Backend: http://localhost:8000")
        print("🖥️ Frontend: http://localhost:8501")
        print("="*50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(frontend_path), 
            "--server.port", "8501"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 InsightPulse stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
