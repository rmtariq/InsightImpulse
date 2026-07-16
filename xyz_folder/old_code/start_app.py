#!/usr/bin/env python3
"""
InsightPulse App Starter
========================

Easy script to start both the backend API and frontend dashboard.

Usage:
    python start_app.py

Author: InsightPulse Team
"""

import subprocess
import time
import sys
import os
import signal
import webbrowser
from pathlib import Path

def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting InsightPulse Backend API...")
    
    # Find available port
    api_port = 8002
    while not check_port_available(api_port):
        api_port += 1
    
    cmd = [
        sys.executable, "-c",
        f"""
import uvicorn
from backend.api import app
print('📍 API available at: http://127.0.0.1:{api_port}')
print('📚 API Documentation: http://127.0.0.1:{api_port}/docs')
uvicorn.run(app, host='127.0.0.1', port={api_port}, log_level='info')
        """
    ]
    
    backend_process = subprocess.Popen(cmd, cwd=Path.cwd())
    print(f"✅ Backend started on port {api_port}")
    return backend_process, api_port

def start_frontend(api_port):
    """Start the Streamlit frontend"""
    print("🖥️ Starting InsightPulse Dashboard...")
    
    # Find available port
    frontend_port = 8501
    while not check_port_available(frontend_port):
        frontend_port += 1
    
    # Update API URL in frontend
    frontend_file = Path("frontend/streamlit_app.py")
    if frontend_file.exists():
        content = frontend_file.read_text()
        content = content.replace(
            'API_BASE_URL = "http://127.0.0.1:8001"',
            f'API_BASE_URL = "http://127.0.0.1:{api_port}"'
        )
        frontend_file.write_text(content)
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "frontend/streamlit_app.py", 
        "--server.port", str(frontend_port),
        "--server.headless", "true"
    ]
    
    frontend_process = subprocess.Popen(cmd, cwd=Path.cwd())
    print(f"✅ Dashboard started on port {frontend_port}")
    return frontend_process, frontend_port

def main():
    """Main startup function"""
    print("🎯 InsightPulse App Starter")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend/api.py").exists():
        print("❌ Error: Please run this script from the InsightPulse directory")
        print("   Current directory:", Path.cwd())
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend
        backend_process, api_port = start_backend()
        processes.append(backend_process)
        
        # Wait for backend to start
        print("⏳ Waiting for backend to start...")
        time.sleep(5)
        
        # Start frontend
        frontend_process, frontend_port = start_frontend(api_port)
        processes.append(frontend_process)
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to start...")
        time.sleep(5)
        
        # Open browsers
        print("\n🌐 Opening web interfaces...")
        webbrowser.open(f"http://localhost:{frontend_port}")
        time.sleep(2)
        webbrowser.open(f"http://127.0.0.1:{api_port}/docs")
        
        print("\n" + "=" * 50)
        print("🎉 InsightPulse is now running!")
        print("=" * 50)
        print(f"📊 Dashboard:     http://localhost:{frontend_port}")
        print(f"🔧 API:           http://127.0.0.1:{api_port}")
        print(f"📚 API Docs:      http://127.0.0.1:{api_port}/docs")
        print(f"❤️  Health Check: http://127.0.0.1:{api_port}/health")
        print("=" * 50)
        print("⏹️  Press Ctrl+C to stop all services")
        print()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down InsightPulse...")
            
    except Exception as e:
        print(f"❌ Error starting InsightPulse: {e}")
    
    finally:
        # Clean up processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
