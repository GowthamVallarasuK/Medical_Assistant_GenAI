"""
Simple AI Service Startup Script
"""

import subprocess
import sys
import time

def check_port(port):
    """Check if port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            s.close()
            return False
        except OSError:
            return True

def start_ai_service():
    """Start AI services with proper error handling"""
    print("🚀 Starting AI Medical Diagnosis Services...")
    
    # Check if port 8000 is available
    if check_port(8000):
        print("❌ Port 8000 is already in use")
        print("🔧 Please stop any existing service first")
        return False
    
    try:
        # Import and run the app
        import uvicorn
        from main_simple import app
        
        print("✅ Starting on http://localhost:8000")
        print("📊 Health check: http://localhost:8000/health")
        print("🩺 Diagnosis endpoint: http://localhost:8000/ai/diagnosis/process")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Make sure FastAPI is installed: pip install fastapi uvicorn")
        return False
    except Exception as e:
        print(f"❌ Startup error: {e}")
        return False

if __name__ == "__main__":
    success = start_ai_service()
    if not success:
        sys.exit(1)
