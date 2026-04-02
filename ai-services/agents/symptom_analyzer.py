"""
Symptom Analyzer Agent - Extracts and analyzes symptoms from user input
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional
import spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from .base_agent import BaseAgent
from ..utils.logger import log_ai_service, log_error
from ..utils.config import settings


class SymptomAnalyzerAgent(BaseAgent):
    """
    Symptom Analyzer Agent
    
    This agent is responsible for:
    - Extracting symptoms from natural language text
    - Classifying symptom severity
    - Identifying symptom duration
    - Structuring symptom information for downstream processing
    """
    
    def __init__(self):
        super().__init__("symptom_analyzer")
        self.nlp = None
        self.tokenizer = None
        self.model = None
        self.symptom_keywords = self._load_symptom_keywords()
        self.severity_indicators = self._load_severity_indicators()
        self.duration_patterns = self._load_duration_patterns()
        
    async def _initialize(self) -> bool:
        """Initialize NLP models and symptom database"""
        try:
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Download if not available
                from spacy.cli import download
                download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            # Load transformer model for symptom classification
            model_name = "dmis-lab/biobert-base-cased-v1.1"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Set to evaluation mode
            self.model.eval()
            
            log_ai_service(self.name, "nlp_models_loaded", {
                "spacy_model": "en_core_web_sm",
                "transformer_model": model_name
            })
            
            return True
            
        except Exception as e:
            log_error(e, {"context": "Symptom analyzer initialization"})
            return False
    
    def _load_symptom_keywords(self) -> Dict[str, List[str]]:
        """Load symptom keyword mappings"""
        return {
            "headache": ["headache", "head pain", "migraine", "cephalgia", "head hurts"],
            "fever": ["fever", "temperature", "hot", "febrile", "pyrexia"],
            "cough": ["cough", "coughing", "hacking", "dry cough", "wet cough"],
            "fatigue": ["fatigue", "tired", "exhausted", "weary", "lethargic"],
            "nausea": ["nausea", "queasy", "sick to stomach", "nauseous"],
            "vomiting": ["vomiting", "vomit", "throwing up", "emesis"],
            "chest pain": ["chest pain", "chest discomfort", "chest tightness"],
            "shortness of breath": ["shortness of breath", "dyspnea", "breathless", "can't breathe"],
            "abdominal pain": ["abdominal pain", "stomach pain", "belly pain"],
            "dizziness": ["dizziness", "dizzy", "lightheaded", "vertigo"],
            "sore throat": ["sore throat", "throat pain", "pharyngitis"],
            "muscle pain": ["muscle pain", "myalgia", "body aches", "muscle aches"],
            "joint pain": ["joint pain", "arthralgia", "joint ache"],
            "rash": ["rash", "skin rash", "eruption", "hives"],
            "diarrhea": ["diarrhea", "diarrhoea", "loose stools", "watery stool"]
        }
    
    def _load_severity_indicators(self) -> Dict[str, List[str]]:
        """Load severity indicator keywords"""
        return {
            "mild": ["mild", "slight", "minor", "light", "low", "a little"],
            "moderate": ["moderate", "medium", "some", "somewhat", "average"],
            "severe": ["severe", "extreme", "intense", "bad", "terrible", "awful", "unbearable"]
        }
    
    def _load_duration_patterns(self) -> List[re.Pattern]:
        """Load regex patterns for duration extraction"""
        patterns = [
            re.compile(r"(\d+)\s*days?", re.IGNORECASE),
            re.compile(r"(\d+)\s*weeks?", re.IGNORECASE),
            re.compile(r"(\d+)\s*months?", re.IGNORECASE),
            re.compile(r"(\d+)\s*hours?", re.IGNORECASE),
            re.compile(r"(\d+)\s*minutes?", re.IGNORECASE),
            re.compile(r"a\s+few\s+days?", re.IGNORECASE),
            re.compile(r"several\s+days?", re.IGNORECASE),
            re.compile(r"about\s+a\s+week", re.IGNORECASE),
            re.compile(r"since\s+(yesterday|today|last week)", re.IGNORECASE),
            re.compile(r"for\s+(\d+)\s+(days?|weeks?|months?)", re.IGNORECASE)
        ]
        return patterns
    
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user message to extract symptoms"""
        message = data.get("message", "")
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        try:
            # Extract symptoms using NLP
            extracted_symptoms = await self._extract_symptoms(message)
            
            # Analyze severity for each symptom
            for symptom in extracted_symptoms:
                symptom["severity"] = self._analyze_severity(message, symptom["name"])
                symptom["duration"] = self._extract_duration(message, symptom["name"])
            
            # Generate structured output
            result = {
                "symptoms": extracted_symptoms,
                "primary_complaint": self._identify_primary_complaint(message, extracted_symptoms),
                "symptom_count": len(extracted_symptoms),
                "extraction_confidence": self._calculate_extraction_confidence(extracted_symptoms),
                "processed_message": message,
                "analysis_metadata": {
                    "nlp_entities": self._extract_nlp_entities(message),
                    "medical_terms": self._extract_medical_terms(message)
                }
            }
            
            log_ai_service(self.name, "symptoms_extracted", {
                "user_id": user_id,
                "session_id": session_id,
                "symptom_count": len(extracted_symptoms),
                "primary_complaint": result["primary_complaint"]
            })
            
            return result
            
        except Exception as e:
            log_error(e, {
                "context": "Symptom extraction",
                "user_id": user_id,
                "session_id": session_id
            })
            raise
    
    async def _extract_symptoms(self, message: str) -> List[Dict[str, Any]]:
        """Extract symptoms from message using NLP"""
        symptoms = []
        message_lower = message.lower()
        
        # Use keyword matching first
        for symptom_category, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Find the context around the symptom
                    context = self._extract_symptom_context(message, keyword)
                    
                    symptoms.append({
                        "name": symptom_category,
                        "matched_keyword": keyword,
                        "context": context,
                        "confidence": self._calculate_symptom_confidence(message, keyword),
                        "severity": None,  # Will be filled later
                        "duration": None   # Will be filled later
                    })
        
        # Use spaCy for additional extraction
        if self.nlp:
            doc = self.nlp(message)
            
            # Look for medical entities
            for ent in doc.ents:
                if ent.label_ in ["DISEASE", "SYMPTOM", "CONDITION"]:
                    # Check if already captured
                    if not any(s["name"] == ent.text.lower() for s in symptoms):
                        symptoms.append({
                            "name": ent.text.lower(),
                            "matched_keyword": ent.text,
                            "context": ent.sent.text,
                            "confidence": 0.8,  # NLP confidence
                            "severity": None,
                            "duration": None,
                            "entity_type": ent.label_
                        })
        
        # Remove duplicates and sort by confidence
        unique_symptoms = []
        seen = set()
        
        for symptom in sorted(symptoms, key=lambda x: x["confidence"], reverse=True):
            symptom_key = symptom["name"].lower()
            if symptom_key not in seen:
                seen.add(symptom_key)
                unique_symptoms.append(symptom)
        
        return unique_symptoms
    
    def _extract_symptom_context(self, message: str, keyword: str) -> str:
        """Extract context around a symptom keyword"""
        # Find the keyword position
        keyword_lower = keyword.lower()
        message_lower = message.lower()
        index = message_lower.find(keyword_lower)
        
        if index == -1:
            return ""
        
        # Extract context (50 characters before and after)
        start = max(0, index - 50)
        end = min(len(message), index + len(keyword) + 50)
        
        context = message[start:end].strip()
        
        # Try to extract complete sentences
        if "." in context:
            sentences = context.split(".")
            for sentence in sentences:
                if keyword_lower in sentence.lower():
                    return sentence.strip()
        
        return context
    
    def _calculate_symptom_confidence(self, message: str, keyword: str) -> float:
        """Calculate confidence score for symptom extraction"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for exact matches
        if keyword.lower() in message.lower():
            confidence += 0.2
        
        # Boost confidence for medical terminology
        if any(term in keyword.lower() for term in ["pain", "ache", "discomfort", "fever", "cough"]):
            confidence += 0.1
        
        # Boost confidence for context
        context_words = ["feel", "have", "suffer", "experience", "symptom"]
        if any(word in message.lower() for word in context_words):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _analyze_severity(self, message: str, symptom_name: str) -> str:
        """Analyze symptom severity from message"""
        message_lower = message.lower()
        symptom_context = self._extract_symptom_context(message, symptom_name).lower()
        
        severity_scores = {"mild": 0, "moderate": 0, "severe": 0}
        
        for severity, indicators in self.severity_indicators.items():
            for indicator in indicators:
                if indicator in symptom_context:
                    severity_scores[severity] += 1
        
        # Determine severity based on scores
        if severity_scores["severe"] > 0:
            return "severe"
        elif severity_scores["moderate"] > severity_scores["mild"]:
            return "moderate"
        elif severity_scores["mild"] > 0:
            return "mild"
        else:
            return "moderate"  # Default
    
    def _extract_duration(self, message: str, symptom_name: str) -> Optional[str]:
        """Extract symptom duration from message"""
        symptom_context = self._extract_symptom_context(message, symptom_name)
        
        for pattern in self.duration_patterns:
            match = pattern.search(symptom_context)
            if match:
                return match.group(0)
        
        return None
    
    def _identify_primary_complaint(self, message: str, symptoms: List[Dict[str, Any]]) -> str:
        """Identify the primary complaint from extracted symptoms"""
        if not symptoms:
            # Extract from message directly
            sentences = message.split(".")
            for sentence in sentences:
                if any(word in sentence.lower() for word in ["pain", "hurt", "ache", "uncomfortable"]):
                    return sentence.strip()
            return message.strip()[:100]  # First 100 chars
        
        # Return the symptom with highest confidence
        primary = max(symptoms, key=lambda x: x["confidence"])
        return primary["name"]
    
    def _calculate_extraction_confidence(self, symptoms: List[Dict[str, Any]]) -> float:
        """Calculate overall extraction confidence"""
        if not symptoms:
            return 0.0
        
        total_confidence = sum(s["confidence"] for s in symptoms)
        return total_confidence / len(symptoms)
    
    def _extract_nlp_entities(self, message: str) -> List[Dict[str, Any]]:
        """Extract NLP entities from message"""
        if not self.nlp:
            return []
        
        doc = self.nlp(message)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0  # spaCy doesn't provide confidence by default
            })
        
        return entities
    
    def _extract_medical_terms(self, message: str) -> List[str]:
        """Extract medical terms from message"""
        medical_terms = []
        
        # Common medical term patterns
        medical_patterns = [
            r"\b(blood|pressure|heart|lung|stomach|liver|kidney)\b",
            r"\b(acute|chronic|inflammation|infection)\b",
            r"\b(medication|medicine|drug|prescription)\b"
        ]
        
        for pattern in medical_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            medical_terms.extend(matches)
        
        return list(set(medical_terms))  # Remove duplicates
    
    async def suggest_symptoms(self, query: str) -> List[str]:
        """Suggest symptoms based on partial input"""
        query_lower = query.lower()
        suggestions = []
        
        # Find matching symptoms
        for symptom_category, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if query_lower in keyword.lower() or keyword.lower().startswith(query_lower):
                    suggestions.append(symptom_category)
        
        # Remove duplicates and limit results
        return list(set(suggestions))[:10]
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        message = data.get("message", "")
        
        if not message or len(message.strip()) == 0:
            return False
        
        if len(message) > 2000:  # Reasonable limit
            return False
        
        return True
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "nlp_model_loaded": self.nlp is not None,
            "transformer_model_loaded": self.model is not None,
            "symptom_keywords_loaded": len(self.symptom_keywords) > 0,
            "test_extraction": await self._test_extraction()
        }
    
    async def _test_extraction(self) -> bool:
        """Test symptom extraction with sample input"""
        try:
            test_message = "I have a severe headache and fever for 2 days"
            result = await self._extract_symptoms(test_message)
            return len(result) > 0
        except Exception:
            return False
    
    async def _warm_up(self) -> bool:
        """Warm up the agent"""
        try:
            # Test extraction with sample data
            await self._test_extraction()
            return True
        except Exception:
            return False
    
    async def _cleanup(self):
        """Clean up resources"""
        # Clear models to free memory
        self.nlp = None
        self.model = None
        self.tokenizer = None
