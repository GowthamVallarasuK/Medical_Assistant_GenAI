"""
Fixed AI Service Startup Script
"""

import uvicorn
from main_simple import app

if __name__ == "__main__":
    print("🚀 Starting AI Medical Diagnosis Services...")
    print("📊 Health check: http://localhost:8000/health")
    print("🩺 Diagnosis endpoint: http://localhost:8000/ai/diagnosis/process")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
