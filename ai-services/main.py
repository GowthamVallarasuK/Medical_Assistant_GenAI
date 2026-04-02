"""
Agentic AI Medical Diagnosis System - Main FastAPI Application
Multi-agent system for collaborative medical diagnosis assistance
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from agents.orchestrator import OrchestratorAgent
from agents.symptom_analyzer import SymptomAnalyzerAgent
from agents.diagnosis_generator import DiagnosisGeneratorAgent
from agents.report_analyzer import ReportAnalyzerAgent
from agents.recommendation_agent import RecommendationAgent
from utils.logger import setup_logger, log_ai_service
from utils.config import Settings
from utils.auth import verify_token
from models.diagnosis import DiagnosisRequest, DiagnosisResponse
from models.chat import ChatRequest, ChatResponse

# Configuration
settings = Settings()
security = HTTPBearer()

# Setup logging
logger = setup_logger(__name__)

# Global agent instances
orchestrator: OrchestratorAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting Agentic AI Medical Diagnosis System...")
    
    global orchestrator
    
    try:
        # Initialize all agents
        logger.info("🤖 Initializing AI agents...")
        
        symptom_analyzer = SymptomAnalyzerAgent()
        diagnosis_generator = DiagnosisGeneratorAgent()
        report_analyzer = ReportAnalyzerAgent()
        recommendation_agent = RecommendationAgent()
        
        # Initialize orchestrator with all agents
        orchestrator = OrchestratorAgent(
            symptom_analyzer=symptom_analyzer,
            diagnosis_generator=diagnosis_generator,
            report_analyzer=report_analyzer,
            recommendation_agent=recommendation_agent
        )
        
        # Warm up models
        await orchestrator.warm_up()
        
        logger.info("✅ All AI agents initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI agents: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Agentic AI Medical Diagnosis System...")
        if orchestrator:
            await orchestrator.cleanup()
        logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Agentic AI Medical Diagnosis API",
    description="Multi-agent AI system for collaborative medical diagnosis assistance",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token and extract user information"""
    try:
        payload = await verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check if the API and AI agents are healthy"""
    try:
        agent_status = await orchestrator.health_check() if orchestrator else {}
        
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0",
            "agents": agent_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Main diagnosis endpoint
@app.post("/ai/diagnosis/process", response_model=DiagnosisResponse, tags=["Diagnosis"])
async def process_diagnosis(
    request: DiagnosisRequest
):
    user = {"id": "anonymous"}
    """
    Process medical diagnosis request through the multi-agent system
    
    This is the main endpoint that orchestrates all AI agents:
    1. Symptom Analyzer - Extracts symptoms from text
    2. Report Analyzer - Analyzes uploaded medical reports
    3. Diagnosis Generator - Generates possible diagnoses
    4. Recommendation Agent - Provides recommendations
    5. Orchestrator - Coordinates all agents and produces final response
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        log_ai_service("orchestrator", "diagnosis_started", {
            "user_id": user.get("id"),
            "session_id": request.session_id,
            "message_length": len(request.message),
            "has_files": len(request.files) > 0
        })
        
        # Process through orchestrator
        # Decode base64 file content before passing to agents
        files_for_agents = []
        for f in request.files:
            file_dict = f.dict()
            if f.content:
                import base64
                try:
                    file_dict["content"] = base64.b64decode(f.content)
                except Exception:
                    file_dict["content"] = b""
            files_for_agents.append(file_dict)

        result = await orchestrator.process_diagnosis(
            message=request.message,
            files=files_for_agents,
            user_id=user.get("id"),
            session_id=request.session_id
        )
        result["session_id"] = request.session_id
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        log_ai_service("orchestrator", "diagnosis_completed", {
            "user_id": user.get("id"),
            "session_id": request.session_id,
            "processing_time": processing_time,
            "risk_level": result.get("risk_level", "unknown")
        })
        
        return DiagnosisResponse(**result)
        
    except Exception as e:
        logger.error(f"Diagnosis processing failed: {e}")
        log_ai_service("orchestrator", "diagnosis_failed", {
            "user_id": user.get("id"),
            "session_id": request.session_id,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to process diagnosis. Please try again."
        )


# Chat endpoint for conversational interaction
@app.post("/ai/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_ai(
    request: ChatRequest
):
    user = {"id": "anonymous"}
    """
    Chat with AI assistant for medical guidance
    
    This endpoint provides a conversational interface for medical queries,
    symptom clarification, and general health guidance.
    """
    try:
        log_ai_service("chat", "chat_started", {
            "user_id": user.get("id"),
            "message_length": len(request.message),
            "has_history": len(request.conversation_history) > 0
        })
        
        # Process chat through orchestrator
        response = await orchestrator.process_chat(
            message=request.message,
            conversation_history=request.conversation_history,
            user_id=user.get("id")
        )
        
        log_ai_service("chat", "chat_completed", {
            "user_id": user.get("id"),
            "response_length": len(response.get("response", ""))
        })
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat message. Please try again."
        )


# Report analysis endpoint
@app.post("/ai/reports/analyze", tags=["Reports"])
async def analyze_medical_report(
    file: bytes = b"",
    filename: str = "",
    content_type: str = "",
):
    user = {"id": "anonymous"}
    """
    Analyze uploaded medical report using OCR and NLP
    
    This endpoint specifically handles medical report analysis,
    extracting relevant medical information from uploaded documents.
    """
    try:
        log_ai_service("report_analyzer", "analysis_started", {
            "user_id": user.get("id"),
            "filename": filename,
            "file_size": len(file),
            "content_type": content_type
        })
        
        # Analyze report through report analyzer agent
        result = await orchestrator.report_analyzer.analyze_report(
            file_content=file,
            filename=filename,
            content_type=content_type,
            user_id=user.get("id")
        )
        
        log_ai_service("report_analyzer", "analysis_completed", {
            "user_id": user.get("id"),
            "filename": filename,
            "extracted_findings": len(result.get("key_findings", []))
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Report analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze medical report. Please try again."
        )


# Symptom suggestions endpoint
@app.get("/ai/symptoms/suggest", tags=["Symptoms"])
async def suggest_symptoms(
    q: str,
):
    """
    Get symptom suggestions based on partial input
    
    This endpoint provides autocomplete suggestions for symptoms
    as the user types, helping them describe their condition better.
    """
    try:
        suggestions = await orchestrator.symptom_analyzer.suggest_symptoms(q)
        
        return {
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Symptom suggestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get symptom suggestions. Please try again."
        )


# Health risk assessment endpoint
@app.post("/ai/risk/assess", tags=["Risk"])
async def assess_health_risk(
    symptoms: list[str],
):
    """
    Assess health risk based on provided symptoms
    
    This endpoint provides a quick risk assessment based on symptoms,
    helping users understand the urgency of their condition.
    """
    try:
        risk_assessment = await orchestrator.diagnosis_generator.assess_risk(symptoms)
        
        return risk_assessment
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assess health risk. Please try again."
        )


# Doctor recommendations endpoint
@app.post("/ai/doctors/recommend", tags=["Recommendations"])
async def recommend_doctors(
    diagnosis: dict,
):
    """
    Get doctor recommendations based on diagnosis
    
    This endpoint provides recommendations for appropriate medical
    specialists based on the diagnosis results.
    """
    try:
        recommendations = await orchestrator.recommendation_agent.recommend_doctors(
            diagnosis=diagnosis,
            user_id=user.get("id")
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Doctor recommendation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get doctor recommendations. Please try again."
        )


# Emergency assessment endpoint
@app.post("/ai/emergency/assess", tags=["Emergency"])
async def assess_emergency(
    symptoms: list[str],
):
    """
    Assess if symptoms require emergency medical attention
    
    This endpoint quickly evaluates whether symptoms indicate
    a medical emergency that requires immediate attention.
    """
    try:
        emergency_assessment = await orchestrator.assess_emergency(symptoms)
        
        return emergency_assessment
        
    except Exception as e:
        logger.error(f"Emergency assessment failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assess emergency status. Please try again."
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "error": str(exc) if settings.debug else None
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
