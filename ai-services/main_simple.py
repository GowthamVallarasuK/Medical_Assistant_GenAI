"""
Simplified AI Services for testing
"""

import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

import base64

app = FastAPI(title="AI Medical Diagnosis API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class FileInfo(BaseModel):
    filename: str
    original_name: str
    file_type: str
    file_size: int
    content: str = None  # base64 encoded string from frontend

class DiagnosisRequest(BaseModel):
    message: str
    session_id: str
    files: List[FileInfo] = []

class DiagnosisResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    risk_level: str
    risk_score: float
    symptoms: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]
    recommendations: List[str]
    precautions: List[str]
    medications: List[Dict[str, Any]]
    lifestyle_advice: List[Dict[str, Any]]
    follow_up: Dict[str, Any]
    emergency_alert: Dict[str, Any]
    uploaded_files: List[Dict[str, Any]]
    ai_agents: Dict[str, Dict[str, Any]]
    processing_time: float

# Simple symptom database
SYMPTOM_KEYWORDS = {
    "headache": ["headache", "head pain", "migraine"],
    "fever": ["fever", "temperature", "hot"],
    "cough": ["cough", "coughing"],
    "fatigue": ["fatigue", "tired", "exhausted"],
    "nausea": ["nausea", "queasy", "sick"],
    "vomiting": ["vomiting", "vomit", "throwing up"],
    "chest pain": ["chest pain", "chest discomfort"],
    "shortness of breath": ["shortness of breath", "breathless"],
    "abdominal pain": ["abdominal pain", "stomach pain"],
    "dizziness": ["dizziness", "dizzy", "lightheaded"],
    "sore throat": ["sore throat", "throat pain"],
}

# Simple condition database
CONDITIONS = {
    "common_cold": {
        "name": "Common Cold",
        "symptoms": ["cough", "sore throat", "fatigue", "headache"],
        "risk_level": "low",
        "confidence": 0.8
    },
    "flu": {
        "name": "Influenza (Flu)",
        "symptoms": ["fever", "cough", "fatigue", "muscle pain"],
        "risk_level": "medium",
        "confidence": 0.7
    },
    "migraine": {
        "name": "Migraine",
        "symptoms": ["headache", "nausea", "dizziness"],
        "risk_level": "medium",
        "confidence": 0.6
    },
    "hypertension": {
        "name": "Hypertension",
        "symptoms": ["headache", "dizziness", "chest pain"],
        "risk_level": "high",
        "confidence": 0.5
    }
}

def extract_text_from_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Extract text from uploaded file"""
    try:
        if "pdf" in content_type.lower() or filename.lower().endswith(".pdf"):
            try:
                import pdfplumber
                from io import BytesIO
                with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages)
            except ImportError:
                pass
            try:
                import fitz
                from io import BytesIO
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                text = "\n".join(page.get_text() for page in doc)
                doc.close()
                return text
            except ImportError:
                return "PDF parsing library not installed."
        elif "image" in content_type.lower():
            try:
                import pytesseract
                from PIL import Image
                from io import BytesIO
                return pytesseract.image_to_string(Image.open(BytesIO(file_bytes)))
            except ImportError:
                return "OCR library not installed."
        else:
            return file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"File extraction error: {str(e)}"


def extract_symptoms(message: str) -> List[Dict[str, Any]]:
    """Extract symptoms from message"""
    symptoms = []
    message_lower = message.lower()
    
    for symptom_name, keywords in SYMPTOM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                symptoms.append({
                    "name": symptom_name,
                    "severity": "moderate",
                    "duration": None,
                    "description": keyword
                })
                break  # Only add each symptom once
    
    return symptoms

def generate_diagnosis(symptoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate diagnosis based on symptoms"""
    if not symptoms:
        return {
            "primary_condition": "Unknown",
            "alternative_conditions": [],
            "confidence": 0.1,
            "icd10_code": "",
            "medical_specialty": "General Practice"
        }
    
    symptom_names = [s["name"] for s in symptoms]
    best_match = None
    best_score = 0
    
    for condition_id, condition_data in CONDITIONS.items():
        score = 0
        for symptom in symptom_names:
            if symptom in condition_data["symptoms"]:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = condition_id
    
    if best_match:
        condition = CONDITIONS[best_match]
        return {
            "primary_condition": condition["name"],
            "alternative_conditions": [],
            "confidence": condition["confidence"] * (best_score / len(symptom_names)),
            "icd10_code": "",
            "medical_specialty": "General Practice"
        }
    
    return {
        "primary_condition": "Unknown",
        "alternative_conditions": [],
        "confidence": 0.3,
        "icd10_code": "",
        "medical_specialty": "General Practice"
    }

def assess_risk(diagnosis: Dict[str, Any], symptoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess risk level"""
    primary_condition = diagnosis["primary_condition"].lower()
    risk_level = "low"
    
    # Check for high-risk conditions
    if "hypertension" in primary_condition:
        risk_level = "high"
    elif "migraine" in primary_condition or "flu" in primary_condition:
        risk_level = "medium"
    
    # Check for high-risk symptoms
    symptom_names = [s["name"] for s in symptoms]
    high_risk_symptoms = ["chest pain", "shortness of breath"]
    if any(symptom in symptom_names for symptom in high_risk_symptoms):
        risk_level = "high"
    
    risk_scores = {"low": 25, "medium": 55, "high": 85}
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_scores.get(risk_level, 30),
        "urgency": "routine" if risk_level == "low" else "within 48 hours" if risk_level == "medium" else "immediate"
    }

def generate_recommendations(diagnosis: Dict[str, Any], risk_level: str) -> List[str]:
    """Generate recommendations"""
    recommendations = [
        "Rest and stay hydrated",
        "Monitor symptoms closely",
        "Over-the-counter medications may help with symptom relief"
    ]
    
    primary_condition = diagnosis["primary_condition"].lower()
    if "cold" in primary_condition or "flu" in primary_condition:
        recommendations.extend([
            "Gargle with warm salt water for sore throat",
            "Use a humidifier to ease congestion"
        ])
    elif "migraine" in primary_condition:
        recommendations.extend([
            "Rest in a dark, quiet room",
            "Avoid bright lights and loud noises"
        ])
    
    if risk_level == "high":
        recommendations.insert(0, "Seek immediate medical attention")
    elif risk_level == "medium":
        recommendations.insert(0, "Consult with a healthcare provider")
    
    return recommendations[:5]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.post("/ai/diagnosis/process", response_model=DiagnosisResponse)
async def process_diagnosis(request: DiagnosisRequest):
    """Process diagnosis request"""
    start_time = time.time()
    
    try:
        # Extract symptoms from message
        symptoms = extract_symptoms(request.message)

        # Process uploaded files and extract additional symptoms from text
        file_analysis_summary = []
        for file_info in request.files:
            if file_info.content:
                try:
                    file_bytes = base64.b64decode(file_info.content)
                    extracted = extract_text_from_file(file_bytes, file_info.filename, file_info.file_type)
                    file_analysis_summary.append(extracted[:300])  # first 300 chars
                    # Also extract symptoms from file text
                    file_symptoms = extract_symptoms(extracted)
                    for s in file_symptoms:
                        if not any(existing["name"] == s["name"] for existing in symptoms):
                            symptoms.append(s)
                except Exception:
                    pass
        
        # Generate diagnosis
        diagnosis = generate_diagnosis(symptoms)
        
        # Assess risk
        risk_assessment = assess_risk(diagnosis, symptoms)
        
        # Generate recommendations
        recommendations = generate_recommendations(diagnosis, risk_assessment["risk_level"])
        
        # Generate response
        file_note = f" Analyzed {len(request.files)} uploaded file(s)." if request.files else ""
        response_text = f"Based on your symptoms{', medical reports,' if request.files else ''} I've identified **{diagnosis['primary_condition']}** as the most likely condition."
        response_text += f" Confidence level: {diagnosis['confidence']*100:.0f}%."
        response_text += f" Risk Level: {risk_assessment['risk_level'].upper()}."
        response_text += f"{file_note} Recommendations: {recommendations[0] if recommendations else 'Rest and monitor symptoms'}."
        
        processing_time = time.time() - start_time
        files_processed = len([f for f in request.files if f.content])
        
        return DiagnosisResponse(
            success=True,
            response=response_text,
            session_id=request.session_id,
            risk_level=risk_assessment["risk_level"],
            risk_score=risk_assessment["risk_score"],
            symptoms=symptoms,
            diagnosis=diagnosis,
            recommendations=recommendations,
            precautions=["Monitor symptoms closely", "Seek medical attention if symptoms worsen"],
            medications=[],
            lifestyle_advice=[],
            follow_up={"recommended": True, "timeframe": "1 week", "with_doctor": False, "urgency": "routine"},
            emergency_alert={"triggered": False, "reason": "", "actions": []},
            uploaded_files=[{"filename": f.filename, "analysis": {"extracted": s}} for f, s in zip(request.files, file_analysis_summary)],
            ai_agents={
                "symptom_analyzer": {"processed": True, "processing_time": 0.1, "confidence": 0.7},
                "diagnosis_generator": {"processed": True, "processing_time": 0.1, "confidence": diagnosis["confidence"]},
                "report_analyzer": {"processed": files_processed > 0, "processing_time": 0.1 * files_processed, "confidence": 0.7 if files_processed > 0 else 0},
                "recommendation_agent": {"processed": True, "processing_time": 0.1, "confidence": 0.8},
                "orchestrator": {"total_processing_time": processing_time, "workflow_steps": ["symptom_analysis", "diagnosis_generation", "recommendation_generation"], "final_confidence": diagnosis["confidence"]}
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        print(f"Error processing diagnosis: {e}")
        raise HTTPException(status_code=500, detail="Failed to process diagnosis")

@app.post("/ai/chat")
async def chat_with_ai(message: str):
    """Chat endpoint"""
    return {
        "response": "I'm here to help with your medical concerns. Please describe your symptoms in detail.",
        "suggestions": ["Describe your symptoms", "Upload medical reports", "Ask about conditions"],
        "is_medical_query": True,
        "requires_doctor": False,
        "confidence": 0.8,
        "processing_time": 0.1
    }

if __name__ == "__main__":
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)
