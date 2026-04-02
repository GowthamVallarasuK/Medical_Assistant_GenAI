"""
Pydantic models for diagnosis requests and responses
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class FileInfo(BaseModel):
    """File information model"""
    filename: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    content: Optional[str] = Field(None, description="Base64 encoded file content from frontend")


class SymptomInfo(BaseModel):
    """Symptom information model"""
    name: str = Field(..., description="Symptom name")
    severity: str = Field(..., description="Severity level: mild, moderate, severe")
    duration: Optional[str] = Field(None, description="Duration description")
    description: Optional[str] = Field(None, description="Additional description")
    
    @validator('severity')
    def validate_severity(cls, v):
        allowed = ['mild', 'moderate', 'severe']
        if v not in allowed:
            raise ValueError(f'Severity must be one of: {allowed}')
        return v


class DiagnosisInfo(BaseModel):
    """Diagnosis information model"""
    primary_condition: str = Field(..., description="Primary diagnosed condition")
    alternative_conditions: List[str] = Field(default_factory=list, description="Alternative possible conditions")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage (0-100)")
    icd10_code: Optional[str] = Field(None, description="ICD-10 code")
    medical_specialty: Optional[str] = Field(None, description="Relevant medical specialty")


class MedicationInfo(BaseModel):
    """Medication information model"""
    name: str = Field(..., description="Medication name")
    dosage: Optional[str] = Field(None, description="Dosage information")
    frequency: Optional[str] = Field(None, description="Frequency of administration")
    duration: Optional[str] = Field(None, description="Duration of treatment")
    notes: Optional[str] = Field(None, description="Additional notes")


class LifestyleAdvice(BaseModel):
    """Lifestyle advice model"""
    category: str = Field(..., description="Category: diet, exercise, sleep, stress, hygiene, other")
    advice: str = Field(..., description="Advice text")
    
    @validator('category')
    def validate_category(cls, v):
        allowed = ['diet', 'exercise', 'sleep', 'stress', 'hygiene', 'other']
        if v not in allowed:
            raise ValueError(f'Category must be one of: {allowed}')
        return v


class FollowUpInfo(BaseModel):
    """Follow-up information model"""
    recommended: bool = Field(default=False, description="Whether follow-up is recommended")
    timeframe: Optional[str] = Field(None, description="Recommended timeframe")
    with_doctor: bool = Field(default=False, description="Whether to see a doctor")
    urgency: Optional[str] = Field(None, description="Urgency level")


class EmergencyAlert(BaseModel):
    """Emergency alert model"""
    triggered: bool = Field(default=False, description="Whether emergency alert was triggered")
    reason: Optional[str] = Field(None, description="Reason for emergency alert")
    actions: List[str] = Field(default_factory=list, description="Recommended actions")


class AgentProcessingInfo(BaseModel):
    """Agent processing information model"""
    processed: bool = Field(default=False, description="Whether agent processed the request")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    confidence: Optional[float] = Field(None, description="Processing confidence")


class DiagnosisRequest(BaseModel):
    """Diagnosis request model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's symptom description")
    session_id: str = Field(..., description="Session identifier")
    files: List[FileInfo] = Field(default_factory=list, description="Uploaded files")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class DiagnosisResponse(BaseModel):
    """Diagnosis response model"""
    success: bool = Field(..., description="Whether processing was successful")
    response: str = Field(..., description="Formatted response message")
    session_id: str = Field(..., description="Session identifier")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    symptoms: List[SymptomInfo] = Field(default_factory=list, description="Extracted symptoms")
    diagnosis: DiagnosisInfo = Field(..., description="Diagnosis information")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    precautions: List[str] = Field(default_factory=list, description="Precautions")
    medications: List[MedicationInfo] = Field(default_factory=list, description="Medication suggestions")
    lifestyle_advice: List[LifestyleAdvice] = Field(default_factory=list, description="Lifestyle advice")
    follow_up: FollowUpInfo = Field(default_factory=FollowUpInfo, description="Follow-up information")
    emergency_alert: EmergencyAlert = Field(default_factory=EmergencyAlert, description="Emergency alert information")
    uploaded_files: List[Dict[str, Any]] = Field(default_factory=list, description="Processed file information")
    ai_agents: Dict[str, AgentProcessingInfo] = Field(default_factory=dict, description="AI agent processing info")
    processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        allowed = ['low', 'medium', 'high']
        if v not in allowed:
            raise ValueError(f'Risk level must be one of: {allowed}')
        return v


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Chat response message")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    is_medical_query: bool = Field(default=False, description="Whether this was a medical query")
    requires_doctor: bool = Field(default=False, description="Whether doctor consultation is recommended")
    confidence: float = Field(..., ge=0, le=1, description="Response confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ReportAnalysisRequest(BaseModel):
    """Report analysis request model"""
    file_content: bytes = Field(..., description="File content")
    filename: str = Field(..., description="File name")
    content_type: str = Field(..., description="MIME type")
    user_id: str = Field(..., description="User identifier")


class ReportAnalysisResponse(BaseModel):
    """Report analysis response model"""
    success: bool = Field(..., description="Whether analysis was successful")
    extracted_text: str = Field(..., description="Extracted text from report")
    key_findings: List[str] = Field(default_factory=list, description="Key medical findings")
    lab_values: List[Dict[str, Any]] = Field(default_factory=list, description="Laboratory values")
    abnormalities: List[str] = Field(default_factory=list, description="Detected abnormalities")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations from report")
    confidence: float = Field(..., ge=0, le=1, description="Analysis confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class SymptomSuggestionRequest(BaseModel):
    """Symptom suggestion request model"""
    query: str = Field(..., min_length=1, max_length=100, description="Partial symptom query")


class SymptomSuggestionResponse(BaseModel):
    """Symptom suggestion response model"""
    query: str = Field(..., description="Original query")
    suggestions: List[str] = Field(default_factory=list, description="Symptom suggestions")
    categories: List[str] = Field(default_factory=list, description="Symptom categories")


class RiskAssessmentRequest(BaseModel):
    """Risk assessment request model"""
    symptoms: List[str] = Field(..., min_items=1, description="List of symptoms")


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response model"""
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    urgency: str = Field(..., description="Urgency level")
    concerns: List[str] = Field(default_factory=list, description="Primary concerns")
    recommendations: List[str] = Field(default_factory=list, description="Immediate recommendations")
    confidence: float = Field(..., ge=0, le=1, description="Assessment confidence")


class DoctorRecommendationRequest(BaseModel):
    """Doctor recommendation request model"""
    diagnosis: Dict[str, Any] = Field(..., description="Diagnosis information")
    user_location: Optional[str] = Field(None, description="User location for local recommendations")
    insurance: Optional[str] = Field(None, description="Insurance information")


class DoctorRecommendationResponse(BaseModel):
    """Doctor recommendation response model"""
    specialties: List[str] = Field(..., description="Recommended medical specialties")
    urgency: str = Field(..., description="Recommended urgency")
    reasoning: str = Field(..., description="Reasoning for recommendations")
    local_options: List[Dict[str, Any]] = Field(default_factory=list, description="Local doctor options")
    questions_to_ask: List[str] = Field(default_factory=list, description="Questions to ask the doctor")
    preparation: List[str] = Field(default_factory=list, description="Preparation for visit")


class EmergencyAssessmentRequest(BaseModel):
    """Emergency assessment request model"""
    symptoms: List[str] = Field(..., min_items=1, description="List of symptoms")
    duration: Optional[str] = Field(None, description="Symptom duration")
    severity: Optional[str] = Field(None, description="Perceived severity")


class EmergencyAssessmentResponse(BaseModel):
    """Emergency assessment response model"""
    is_emergency: bool = Field(..., description="Whether this is an emergency")
    urgency_level: str = Field(..., description="Urgency level")
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions to take")
    emergency_services: bool = Field(default, description="Whether to call emergency services")
    reasoning: str = Field(..., description="Reasoning for assessment")
    confidence: float = Field(..., ge=0, le=1, description="Assessment confidence")
