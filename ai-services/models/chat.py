"""
Pydantic models for chat functionality
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str = Field(..., description="Message ID")
    type: str = Field(..., description="Message type: user, ai, system, error")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('type')
    def validate_type(cls, v):
        allowed = ['user', 'ai', 'system', 'error']
        if v not in allowed:
            raise ValueError(f'Message type must be one of: {allowed}')
        return v


class ConversationHistory(BaseModel):
    """Conversation history model"""
    session_id: str = Field(..., description="Session identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages")
    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    status: str = Field(default="active", description="Conversation status")
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['active', 'completed', 'abandoned', 'error']
        if v not in allowed:
            raise ValueError(f'Status must be one of: {allowed}')
        return v


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Previous messages")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: ChatMessage = Field(..., description="Response message")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    is_medical_query: bool = Field(default=False, description="Whether this was a medical query")
    requires_doctor: bool = Field(default=False, description="Whether doctor consultation is recommended")
    confidence: float = Field(..., ge=0, le=1, description="Response confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    session_id: str = Field(..., description="Session identifier")


class SymptomClarification(BaseModel):
    """Symptom clarification model"""
    symptom: str = Field(..., description="Symptom name")
    questions: List[str] = Field(..., description="Clarification questions")
    options: List[str] = Field(default_factory=list, description="Possible options")


class MedicalContext(BaseModel):
    """Medical context for chat"""
    current_symptoms: List[str] = Field(default_factory=list, description="Current symptoms")
    medical_history: List[str] = Field(default_factory=list, description="Relevant medical history")
    medications: List[str] = Field(default_factory=list, description="Current medications")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")


class ChatIntent(BaseModel):
    """Chat intent classification"""
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0, le=1, description="Intent confidence")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    medical_relevance: float = Field(..., ge=0, le=1, description="Medical relevance score")


class ChatAnalytics(BaseModel):
    """Chat analytics model"""
    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Total messages")
    user_messages: int = Field(..., description="User messages count")
    ai_messages: int = Field(..., description="AI messages count")
    session_duration: float = Field(..., description="Session duration in seconds")
    medical_queries: int = Field(..., description="Number of medical queries")
    resolved_queries: int = Field(..., description="Number of resolved queries")
    user_satisfaction: Optional[float] = Field(None, ge=1, le=5, description="User satisfaction rating")


class ChatFeedback(BaseModel):
    """Chat feedback model"""
    session_id: str = Field(..., description="Session identifier")
    message_id: Optional[str] = Field(None, description="Specific message ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comment: Optional[str] = Field(None, max_length=500, description="Feedback comment")
    helpful: bool = Field(..., description="Whether the response was helpful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Feedback timestamp")


class ChatTemplate(BaseModel):
    """Chat response template model"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    category: str = Field(..., description="Template category")
    template_text: str = Field(..., description="Template text with placeholders")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Template conditions")
    is_active: bool = Field(default=True, description="Whether template is active")


class QuickResponse(BaseModel):
    """Quick response model"""
    trigger: str = Field(..., description="Trigger phrase or keyword")
    response: str = Field(..., description="Quick response")
    category: str = Field(..., description="Response category")
    confidence_threshold: float = Field(default=0.8, ge=0, le=1, description="Confidence threshold")
    is_medical: bool = Field(default=False, description="Whether this is a medical response")


class EscalationRule(BaseModel):
    """Escalation rule model"""
    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    conditions: Dict[str, Any] = Field(..., description="Escalation conditions")
    actions: List[str] = Field(..., description="Escalation actions")
    priority: int = Field(default=1, ge=1, le=10, description="Rule priority")
    is_active: bool = Field(default=True, description="Whether rule is active")


class ChatSessionSummary(BaseModel):
    """Chat session summary model"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    start_time: datetime = Field(..., description="Session start time")
    end_time: datetime = Field(..., description="Session end time")
    duration: float = Field(..., description="Session duration in seconds")
    message_count: int = Field(..., description="Total message count")
    primary_topics: List[str] = Field(default_factory=list, description="Primary topics discussed")
    symptoms_discussed: List[str] = Field(default_factory=list, description="Symptoms discussed")
    recommendations_given: List[str] = Field(default_factory=list, description="Recommendations provided")
    escalation_triggered: bool = Field(default=False, description="Whether escalation was triggered")
    user_satisfaction: Optional[float] = Field(None, ge=1, le=5, description="User satisfaction")
    resolution_status: str = Field(..., description="Resolution status")
