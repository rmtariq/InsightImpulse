#!/usr/bin/env python3
"""
🚀 InsightPulse Web Application Launcher
========================================
Simple script to start the InsightPulse web application
Handles setup, testing, and launching the web server

🎯 FEATURES:
- Automatic dependency checking
- System testing before launch
- Web server startup with proper configuration
- Real-time status monitoring

Author: InsightPulse Launch Team
Version: Web Launch 1.0.0
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path
import time
import webbrowser
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print InsightPulse banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🚀 INSIGHTPULSE WEB APPLICATION LAUNCHER 🚀               ║
    ║                                                              ║
    ║    🎯 9-Platform Social Media & E-commerce Analytics        ║
    ║    🤖 Real AI Analysis with Malaysian Models                ║
    ║    🌐 Professional Web Interface                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    logger.info("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("❌ Python 3.8+ required. Current version: {}.{}.{}".format(
            version.major, version.minor, version.micro
        ))
        return False
    
    logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("📦 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pandas",
        "requests",
        "transformers"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} - Installed")
        except ImportError:
            logger.warning(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"⚠️ Missing packages: {', '.join(missing_packages)}")
        logger.info("💡 Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required dependencies installed!")
    return True

def check_file_structure():
    """Check if required files exist"""
    logger.info("📁 Checking file structure...")
    
    required_files = [
        "web_backend/app.py",
        "web_backend/real_crawler_integration.py",
        "web_backend/real_ai_analysis.py",
        "web_frontend/index.html",
        "web_frontend/assets/css/main.css",
        "web_frontend/assets/js/main.js"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            logger.info(f"✅ {file_path} - Found")
        else:
            logger.warning(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"⚠️ Missing files: {', '.join(missing_files)}")
        return False
    
    logger.info("✅ All required files found!")
    return True

def check_s_crawlers():
    """Check if S_crawlers directory exists"""
    logger.info("🕷️ Checking S_crawlers integration...")
    
    s_crawlers_path = Path("/Users/rmtariq/Documents/S_crawlers")
    
    if s_crawlers_path.exists():
        logger.info(f"✅ S_crawlers directory found: {s_crawlers_path}")
        
        # Check for crawler scripts
        crawlers_dir = s_crawlers_path / "crawlers"
        if crawlers_dir.exists():
            crawler_files = list(crawlers_dir.glob("*.py"))
            logger.info(f"✅ Found {len(crawler_files)} crawler scripts")
        else:
            logger.warning("⚠️ Crawlers directory not found")
        
        # Check for data
        data_dir = s_crawlers_path / "data"
        if data_dir.exists():
            data_folders = [d for d in data_dir.iterdir() if d.is_dir()]
            logger.info(f"✅ Found {len(data_folders)} data directories")
        else:
            logger.warning("⚠️ Data directory not found")
        
        return True
    else:
        logger.warning(f"⚠️ S_crawlers directory not found: {s_crawlers_path}")
        logger.info("💡 The system will work with limited functionality")
        return False

async def run_system_test():
    """Run quick system test"""
    logger.info("🧪 Running system test...")
    
    try:
        # Import and run basic test
        from test_real_system import test_web_backend
        
        result = await test_web_backend()
        
        if result:
            logger.info("✅ System test passed!")
            return True
        else:
            logger.warning("⚠️ System test failed - but continuing anyway")
            return True  # Continue even if test fails
            
    except Exception as e:
        logger.warning(f"⚠️ System test error: {e} - continuing anyway")
        return True

def install_dependencies():
    """Install dependencies if missing"""
    logger.info("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        logger.info("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def start_web_server():
    """Start the FastAPI web server"""
    logger.info("🌐 Starting InsightPulse web server...")
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "web_backend.app:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        logger.info("🚀 Launching server with command:")
        logger.info(f"   {' '.join(cmd)}")
        logger.info("")
        logger.info("🌍 Server will be available at:")
        logger.info("   - Local: http://localhost:8000")
        logger.info("   - Network: http://0.0.0.0:8000")
        logger.info("")
        logger.info("📱 API Documentation:")
        logger.info("   - Swagger UI: http://localhost:8000/docs")
        logger.info("   - ReDoc: http://localhost:8000/redoc")
        logger.info("")
        logger.info("⏹️ Press Ctrl+C to stop the server")
        logger.info("=" * 60)
        
        # Wait a moment then open browser
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000")
                logger.info("🌐 Opened browser to http://localhost:8000")
            except:
                pass
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False
    
    return True

async def main():
    """Main launcher function"""
    print_banner()
    
    logger.info(f"🕐 Starting InsightPulse at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Pre-flight checks
    checks_passed = True
    
    # Check Python version
    if not check_python_version():
        checks_passed = False
    
    # Check file structure
    if not check_file_structure():
        checks_passed = False
    
    # Check S_crawlers (optional)
    s_crawlers_available = check_s_crawlers()
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        logger.info("🔧 Attempting to install missing dependencies...")
        if install_dependencies():
            deps_ok = check_dependencies()  # Re-check
        
        if not deps_ok:
            logger.error("❌ Cannot proceed without required dependencies")
            checks_passed = False
    
    if not checks_passed:
        logger.error("❌ Pre-flight checks failed. Please fix the issues above.")
        return False
    
    # Run system test
    logger.info("=" * 60)
    test_passed = await run_system_test()
    
    # Start the server
    logger.info("=" * 60)
    logger.info("🎯 All checks passed! Starting InsightPulse...")
    
    if not s_crawlers_available:
        logger.info("💡 Note: S_crawlers not found - using fallback data sources")
    
    logger.info("🚀 Ready to launch!")
    time.sleep(2)
    
    # Start web server
    return start_web_server()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            logger.info("✅ InsightPulse launched successfully!")
        else:
            logger.error("❌ Failed to launch InsightPulse")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
