"""
Diagnosis Generator Agent - Generates possible diagnoses based on symptoms
"""

import asyncio
import json
from typing import Dict, Any, List
import random

from .base_agent import BaseAgent
from ..utils.logger import log_ai_service


class DiagnosisGeneratorAgent(BaseAgent):
    """
    Diagnosis Generator Agent
    
    This agent is responsible for:
    - Generating possible diagnoses based on symptoms
    - Calculating confidence scores
    - Providing medical specialty recommendations
    - Assessing risk levels
    """
    
    def __init__(self):
        super().__init__("diagnosis_generator")
        self.condition_database = self._load_condition_database()
        self.symptom_condition_mapping = self._load_symptom_condition_mapping()
        
    def _load_condition_database(self) -> Dict[str, Any]:
        """Load medical conditions database"""
        return {
            "common_cold": {
                "name": "Common Cold",
                "icd10": "J00",
                "specialty": "General Practice",
                "symptoms": ["cough", "sore throat", "runny nose", "fatigue", "headache"],
                "risk_level": "low",
                "confidence_range": (0.7, 0.9)
            },
            "flu": {
                "name": "Influenza (Flu)",
                "icd10": "J11",
                "specialty": "General Practice",
                "symptoms": ["fever", "cough", "fatigue", "muscle pain", "headache"],
                "risk_level": "medium",
                "confidence_range": (0.6, 0.8)
            },
            "migraine": {
                "name": "Migraine",
                "icd10": "G43",
                "specialty": "Neurology",
                "symptoms": ["headache", "nausea", "dizziness", "sensitivity to light"],
                "risk_level": "medium",
                "confidence_range": (0.5, 0.7)
            },
            "gastroenteritis": {
                "name": "Gastroenteritis",
                "icd10": "K09",
                "specialty": "Gastroenterology",
                "symptoms": ["abdominal pain", "nausea", "vomiting", "diarrhea"],
                "risk_level": "medium",
                "confidence_range": (0.6, 0.8)
            },
            "hypertension": {
                "name": "Hypertension",
                "icd10": "I10",
                "specialty": "Cardiology",
                "symptoms": ["headache", "dizziness", "chest pain"],
                "risk_level": "high",
                "confidence_range": (0.4, 0.6)
            }
        }
    
    def _load_symptom_condition_mapping(self) -> Dict[str, List[str]]:
        """Load symptom to condition mapping"""
        return {
            "headache": ["common_cold", "flu", "migraine", "hypertension"],
            "fever": ["common_cold", "flu"],
            "cough": ["common_cold", "flu"],
            "fatigue": ["common_cold", "flu"],
            "nausea": ["migraine", "gastroenteritis"],
            "vomiting": ["gastroenteritis"],
            "abdominal pain": ["gastroenteritis"],
            "dizziness": ["migraine", "hypertension"],
            "sore throat": ["common_cold", "flu"],
            "muscle pain": ["flu"],
            "chest pain": ["hypertension"]
        }
    
    async def _initialize(self) -> bool:
        """Initialize the diagnosis generator"""
        try:
            # Validate databases are loaded
            if not self.condition_database or not self.symptom_condition_mapping:
                return False
            
            log_ai_service(self.name, "diagnosis_generator_initialized", {
                "conditions_loaded": len(self.condition_database),
                "symptom_mappings": len(self.symptom_condition_mapping)
            })
            
            return True
            
        except Exception as e:
            log_ai_service(self.name, "initialization_failed", {"error": str(e)})
            return False
    
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process symptoms to generate diagnoses"""
        symptoms = data.get("symptoms", [])
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        try:
            # Extract symptom names
            symptom_names = [s.get("name", "").lower() for s in symptoms]
            
            # Find matching conditions
            possible_conditions = self._find_matching_conditions(symptom_names)
            
            # Generate diagnosis with confidence scores
            diagnosis = self._generate_diagnosis(possible_conditions, symptom_names)
            
            # Assess risk level
            risk_assessment = self._assess_risk(diagnosis, symptom_names)
            
            result = {
                "diagnosis": diagnosis,
                "risk_assessment": risk_assessment,
                "possible_conditions": possible_conditions,
                "confidence": diagnosis.get("confidence", 0.5),
                "processed_symptoms": symptom_names,
                "recommendations": self._generate_basic_recommendations(diagnosis)
            }
            
            log_ai_service(self.name, "diagnosis_generated", {
                "user_id": user_id,
                "session_id": session_id,
                "primary_condition": diagnosis.get("primary_condition"),
                "confidence": diagnosis.get("confidence"),
                "risk_level": risk_assessment.get("risk_level")
            })
            
            return result
            
        except Exception as e:
            log_ai_service(self.name, "diagnosis_generation_failed", {
                "user_id": user_id,
                "session_id": session_id,
                "error": str(e)
            })
            raise
    
    def _find_matching_conditions(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Find conditions that match the symptoms"""
        condition_matches = {}
        
        for symptom in symptoms:
            if symptom in self.symptom_condition_mapping:
                for condition_id in self.symptom_condition_mapping[symptom]:
                    if condition_id not in condition_matches:
                        condition_matches[condition_id] = {
                            "id": condition_id,
                            "matched_symptoms": [],
                            "total_symptoms": 0
                        }
                    condition_matches[condition_id]["matched_symptoms"].append(symptom)
        
        # Calculate match scores
        for condition_id, match_data in condition_matches.items():
            condition_info = self.condition_database.get(condition_id, {})
            total_symptoms = len(condition_info.get("symptoms", []))
            matched_count = len(match_data["matched_symptoms"])
            
            condition_matches[condition_id]["match_score"] = matched_count / total_symptoms if total_symptoms > 0 else 0
            condition_matches[condition_id]["total_symptoms"] = total_symptoms
        
        return list(condition_matches.values())
    
    def _generate_diagnosis(self, possible_conditions: List[Dict[str, Any]], symptoms: List[str]) -> Dict[str, Any]:
        """Generate primary diagnosis with confidence"""
        if not possible_conditions:
            return {
                "primary_condition": "Unknown",
                "alternative_conditions": [],
                "confidence": 0.1,
                "icd10_code": "",
                "medical_specialty": "General Practice"
            }
        
        # Sort by match score
        possible_conditions.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Get primary condition
        primary = possible_conditions[0]
        condition_id = primary["id"]
        condition_info = self.condition_database.get(condition_id, {})
        
        # Calculate confidence based on match score and symptom coverage
        base_confidence = primary["match_score"]
        confidence_range = condition_info.get("confidence_range", (0.3, 0.7))
        confidence = base_confidence * (confidence_range[1] - confidence_range[0]) + confidence_range[0]
        
        # Get alternative conditions
        alternatives = []
        for condition in possible_conditions[1:3]:  # Top 2 alternatives
            alt_info = self.condition_database.get(condition["id"], {})
            alternatives.append(alt_info.get("name", "Unknown"))
        
        return {
            "primary_condition": condition_info.get("name", "Unknown"),
            "alternative_conditions": alternatives,
            "confidence": min(confidence, 0.95),  # Cap at 95%
            "icd10_code": condition_info.get("icd10", ""),
            "medical_specialty": condition_info.get("specialty", "General Practice")
        }
    
    def _assess_risk(self, diagnosis: Dict[str, Any], symptoms: List[str]) -> Dict[str, Any]:
        """Assess the risk level"""
        primary_condition = diagnosis.get("primary_condition", "")
        
        # Find the condition info
        risk_level = "low"
        for condition_id, condition_info in self.condition_database.items():
            if condition_info.get("name") == primary_condition:
                risk_level = condition_info.get("risk_level", "low")
                break
        
        # Adjust risk based on symptoms
        high_risk_symptoms = ["chest pain", "shortness of breath", "severe headache"]
        if any(symptom in symptoms for symptom in high_risk_symptoms):
            risk_level = "high"
        
        # Calculate risk score
        risk_scores = {"low": 20, "medium": 50, "high": 80}
        risk_score = risk_scores.get(risk_level, 30)
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "concerns": self._get_risk_concerns(risk_level, symptoms),
            "urgency": self._get_urgency_level(risk_level)
        }
    
    def _get_risk_concerns(self, risk_level: str, symptoms: List[str]) -> List[str]:
        """Get risk-specific concerns"""
        concerns = []
        
        if risk_level == "high":
            concerns.append("Immediate medical attention recommended")
            concerns.append("Symptoms may indicate serious condition")
        elif risk_level == "medium":
            concerns.append("Medical consultation recommended")
            concerns.append("Monitor symptoms closely")
        else:
            concerns.append("Self-care may be sufficient")
            concerns.append("Rest and hydration recommended")
        
        return concerns
    
    def _get_urgency_level(self, risk_level: str) -> str:
        """Get urgency level based on risk"""
        urgency_map = {
            "low": "routine",
            "medium": "within 48 hours",
            "high": "immediate"
        }
        return urgency_map.get(risk_level, "routine")
    
    def _generate_basic_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """Generate basic recommendations"""
        recommendations = []
        
        primary_condition = diagnosis.get("primary_condition", "")
        specialty = diagnosis.get("medical_specialty", "")
        
        # General recommendations
        recommendations.append("Rest and stay hydrated")
        recommendations.append("Monitor symptoms and seek medical attention if they worsen")
        
        # Condition-specific recommendations
        if "cold" in primary_condition.lower() or "flu" in primary_condition.lower():
            recommendations.append("Over-the-counter cold/flu medication may help with symptoms")
            recommendations.append("Gargle with warm salt water for sore throat")
        
        if "migraine" in primary_condition.lower():
            recommendations.append("Rest in a dark, quiet room")
            recommendations.append("Avoid bright lights and loud noises")
        
        if specialty != "General Practice":
            recommendations.append(f"Consult with a {specialty} specialist")
        
        return recommendations
    
    async def assess_risk(self, symptoms: List[str]) -> Dict[str, Any]:
        """Quick risk assessment for symptoms"""
        try:
            # Use the same risk assessment logic
            mock_diagnosis = {"primary_condition": "Unknown"}
            risk_assessment = self._assess_risk(mock_diagnosis, [s.lower() for s in symptoms])
            
            return {
                "risk_level": risk_assessment["risk_level"],
                "risk_score": risk_assessment["risk_score"],
                "urgency": risk_assessment["urgency"],
                "concerns": risk_assessment["concerns"],
                "confidence": 0.7
            }
            
        except Exception as e:
            return {
                "risk_level": "medium",
                "risk_score": 50,
                "urgency": "within 48 hours",
                "concerns": ["Unable to assess risk accurately"],
                "confidence": 0.1
            }
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        symptoms = data.get("symptoms", [])
        return isinstance(symptoms, list) and len(symptoms) > 0
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "condition_database_loaded": len(self.condition_database) > 0,
            "symptom_mapping_loaded": len(self.symptom_condition_mapping) > 0,
            "total_conditions": len(self.condition_database),
            "test_diagnosis": await self._test_diagnosis()
        }
    
    async def _test_diagnosis(self) -> bool:
        """Test diagnosis generation"""
        try:
            test_symptoms = [{"name": "headache", "severity": "moderate"}]
            result = await self._process({"symptoms": test_symptoms})
            return "diagnosis" in result
        except Exception:
            return False
    
    async def _warm_up(self) -> bool:
        """Warm up the agent"""
        try:
            await self._test_diagnosis()
            return True
        except Exception:
            return False
