#!/usr/bin/env python3
"""
InsightPulse Frontend Starter
Run this to start the Streamlit frontend
"""

import subprocess
import sys
import os
from pathlib import Path
import time
import requests

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    # Get the project root directory
    project_root = Path(__file__).parent
    frontend_path = project_root / "frontend" / "streamlit_app.py"
    
    print("🎯 Starting InsightPulse Frontend...")
    print(f"📁 Project root: {project_root}")
    print(f"🖥️ Frontend script: {frontend_path}")
    
    # Check if frontend file exists
    if not frontend_path.exists():
        print(f"❌ Frontend file not found: {frontend_path}")
        sys.exit(1)
    
    # Check if backend is running
    print("🔍 Checking backend status...")
    if check_backend():
        print("✅ Backend is running on http://localhost:8000")
    else:
        print("⚠️ Backend not detected. Please start backend first:")
        print("   python start_backend.py")
        print("\n🚀 Starting frontend anyway...")
    
    # Change to project directory
    os.chdir(project_root)
    
    try:
        print("🚀 Starting Streamlit server on http://localhost:8501")
        print("🌐 Frontend will open in your browser automatically")
        print("\n" + "="*50)
        
        # Start the frontend
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(frontend_path), 
            "--server.port", "8501"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend failed to start: {e}")
        print("\n💡 Try installing Streamlit:")
        print("   pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
