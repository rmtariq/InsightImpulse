#!/usr/bin/env python3
"""
InsightPulse Backend Starter
Run this to start the FastAPI backend server
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the project root directory
    project_root = Path(__file__).parent
    backend_path = project_root / "backend" / "api.py"
    
    print("🎯 Starting InsightPulse Backend...")
    print(f"📁 Project root: {project_root}")
    print(f"🔧 Backend script: {backend_path}")
    
    # Check if backend file exists
    if not backend_path.exists():
        print(f"❌ Backend file not found: {backend_path}")
        sys.exit(1)
    
    # Change to project directory
    os.chdir(project_root)
    
    try:
        print("🚀 Starting FastAPI server on http://localhost:8000")
        print("📊 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        print("\n" + "="*50)
        
        # Start the backend
        subprocess.run([sys.executable, str(backend_path)], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
