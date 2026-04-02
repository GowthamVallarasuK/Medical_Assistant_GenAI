"""
Recommendation Agent - Provides medical recommendations and doctor suggestions
"""

import asyncio
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..utils.logger import log_ai_service


class RecommendationAgent(BaseAgent):
    """
    Recommendation Agent
    
    This agent is responsible for:
    - Generating treatment recommendations
    - Providing lifestyle advice
    - Suggesting when to see a doctor
    - Recommending appropriate medical specialists
    """
    
    def __init__(self):
        super().__init__("recommendation_agent")
        self.condition_recommendations = self._load_condition_recommendations()
        self.specialty_mapping = self._load_specialty_mapping()
        self.emergency_criteria = self._load_emergency_criteria()
        
    def _load_condition_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """Load condition-specific recommendations"""
        return {
            "common_cold": {
                "treatment": [
                    "Rest and increased fluid intake",
                    "Over-the-counter pain relievers for headache and body aches",
                    "Decongestants for nasal congestion",
                    "Warm salt water gargles for sore throat"
                ],
                "lifestyle": [
                    "Get adequate rest (7-9 hours of sleep)",
                    "Stay hydrated with water, juice, or warm broth",
                    "Use a humidifier to ease congestion",
                    "Avoid alcohol and caffeine"
                ],
                "precautions": [
                    "Wash hands frequently to prevent spread",
                    "Cover mouth and nose when coughing/sneezing",
                    "Avoid close contact with others",
                    "Monitor for fever above 103°F"
                ],
                "follow_up": "See a doctor if symptoms worsen or last more than 10 days"
            },
            "flu": {
                "treatment": [
                    "Antiviral medications if prescribed within 48 hours",
                    "Over-the-counter fever reducers",
                    "Rest and hydration",
                    "Pain relievers for body aches"
                ],
                "lifestyle": [
                    "Complete bed rest if fever is present",
                    "Isolate yourself to prevent spreading",
                    "Eat light, nutritious meals",
                    "Monitor temperature regularly"
                ],
                "precautions": [
                    "Seek immediate care for difficulty breathing",
                    "Watch for signs of dehydration",
                    "Monitor for high fever (>103°F)",
                    "Avoid alcohol and tobacco"
                ],
                "follow_up": "Seek medical attention if symptoms are severe or complications develop"
            },
            "migraine": {
                "treatment": [
                    "Prescription migraine medications",
                    "Over-the-counter pain relievers",
                    "Anti-nausea medications",
                    "Triptans if prescribed"
                ],
                "lifestyle": [
                    "Rest in a dark, quiet room",
                    "Apply cold compresses to head",
                    "Stay hydrated",
                    "Maintain regular sleep schedule"
                ],
                "precautions": [
                    "Avoid known migraine triggers",
                    "Keep a headache diary",
                    "Don't ignore warning signs",
                    "Seek care for sudden severe headaches"
                ],
                "follow_up": "See a neurologist if migraines are frequent or severe"
            },
            "gastroenteritis": {
                "treatment": [
                    "Oral rehydration solutions",
                    "Anti-nausea medications",
                    "Probiotics",
                    "BRAT diet (Bananas, Rice, Applesauce, Toast)"
                ],
                "lifestyle": [
                    "Gradually reintroduce foods",
                    "Avoid dairy and fatty foods initially",
                    "Rest the digestive system",
                    "Practice good hygiene"
                ],
                "precautions": [
                    "Watch for signs of severe dehydration",
                    "Seek care for blood in stool",
                    "Monitor for high fever",
                    "Avoid anti-diarrheal medications if fever is present"
                ],
                "follow_up": "See a doctor if symptoms last more than 3 days or are severe"
            },
            "hypertension": {
                "treatment": [
                    "Prescription blood pressure medications",
                    "Regular monitoring of blood pressure",
                    "Low-sodium diet",
                    "Stress management techniques"
                ],
                "lifestyle": [
                    "Regular aerobic exercise (30 minutes daily)",
                    "Weight management",
                    "Limit alcohol consumption",
                    "Quit smoking"
                ],
                "precautions": [
                    "Monitor blood pressure regularly",
                    "Take medications as prescribed",
                    "Reduce stress through relaxation techniques",
                    "Limit processed foods and salt"
                ],
                "follow_up": "Regular cardiology follow-ups every 3-6 months"
            }
        }
    
    def _load_specialty_mapping(self) -> Dict[str, str]:
        """Load condition to medical specialty mapping"""
        return {
            "common_cold": "General Practice",
            "flu": "General Practice",
            "migraine": "Neurology",
            "gastroenteritis": "Gastroenterology",
            "hypertension": "Cardiology",
            "chest_pain": "Cardiology",
            "skin_rash": "Dermatology",
            "joint_pain": "Rheumatology",
            "mental_health": "Psychiatry",
            "womens_health": "Gynecology",
            "childrens_health": "Pediatrics",
            "eye_problems": "Ophthalmology",
            "ear_problems": "Otolaryngology"
        }
    
    def _load_emergency_criteria(self) -> List[str]:
        """Load emergency medical criteria"""
        return [
            "chest pain or pressure",
            "difficulty breathing or shortness of breath",
            "severe abdominal pain",
            "sudden severe headache",
            "confusion or difficulty speaking",
            "vision changes",
            "numbness or weakness",
            "high fever (>103°F/39.4°C)",
            "uncontrolled bleeding",
            "seizures",
            "loss of consciousness"
        ]
    
    async def _initialize(self) -> bool:
        """Initialize the recommendation agent"""
        try:
            # Validate databases are loaded
            if not self.condition_recommendations or not self.specialty_mapping:
                return False
            
            log_ai_service(self.name, "recommendation_agent_initialized", {
                "conditions_loaded": len(self.condition_recommendations),
                "specialties_loaded": len(self.specialty_mapping),
                "emergency_criteria_loaded": len(self.emergency_criteria)
            })
            
            return True
            
        except Exception as e:
            log_ai_service(self.name, "initialization_failed", {"error": str(e)})
            return False
    
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process diagnosis to generate recommendations"""
        diagnosis = data.get("diagnosis", {})
        symptoms = data.get("symptoms", [])
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        try:
            primary_condition = diagnosis.get("primary_condition", "").lower()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(primary_condition)
            lifestyle_advice = self._generate_lifestyle_advice(primary_condition)
            precautions = self._generate_precautions(primary_condition)
            
            # Determine follow-up needs
            follow_up = self._determine_follow_up(primary_condition, diagnosis.get("risk_level", "low"))
            
            # Check for emergency conditions
            emergency_alert = self._check_emergency_conditions(symptoms, diagnosis)
            
            # Generate doctor recommendations
            doctor_recommendations = self._recommend_doctors(diagnosis)
            
            result = {
                "recommendations": recommendations,
                "lifestyle_advice": lifestyle_advice,
                "precautions": precautions,
                "follow_up": follow_up,
                "emergency_alert": emergency_alert,
                "doctor_recommendations": doctor_recommendations,
                "medical_disclaimer": self._get_medical_disclaimer()
            }
            
            log_ai_service(self.name, "recommendations_generated", {
                "user_id": user_id,
                "session_id": session_id,
                "primary_condition": primary_condition,
                "emergency_triggered": emergency_alert.get("triggered", False)
            })
            
            return result
            
        except Exception as e:
            log_ai_service(self.name, "recommendation_generation_failed", {
                "user_id": user_id,
                "session_id": session_id,
                "error": str(e)
            })
            raise
    
    def _generate_recommendations(self, primary_condition: str) -> List[str]:
        """Generate treatment recommendations"""
        # Find matching condition
        for condition_key, condition_data in self.condition_recommendations.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                return condition_data.get("treatment", [])
        
        # Default recommendations
        return [
            "Rest and stay hydrated",
            "Monitor symptoms closely",
            "Over-the-counter medications may help with symptom relief",
            "Contact healthcare provider if symptoms worsen"
        ]
    
    def _generate_lifestyle_advice(self, primary_condition: str) -> List[str]:
        """Generate lifestyle advice"""
        for condition_key, condition_data in self.condition_recommendations.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                return condition_data.get("lifestyle", [])
        
        # Default lifestyle advice
        return [
            "Get adequate rest (7-9 hours)",
            "Maintain balanced nutrition",
            "Stay hydrated with water",
            "Engage in light physical activity if able"
        ]
    
    def _generate_precautions(self, primary_condition: str) -> List[str]:
        """Generate precautions"""
        for condition_key, condition_data in self.condition_recommendations.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                return condition_data.get("precautions", [])
        
        # Default precautions
        return [
            "Monitor for worsening symptoms",
            "Seek medical attention if symptoms persist",
            "Follow medication instructions carefully",
            "Avoid activities that worsen symptoms"
        ]
    
    def _determine_follow_up(self, primary_condition: str, risk_level: str) -> Dict[str, Any]:
        """Determine follow-up requirements"""
        follow_up = {
            "recommended": True,
            "timeframe": "1-2 weeks",
            "with_doctor": False,
            "urgency": "routine"
        }
        
        # Adjust based on condition
        for condition_key, condition_data in self.condition_recommendations.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                follow_up_text = condition_data.get("follow_up", "")
                if "specialist" in follow_up_text.lower():
                    follow_up["with_doctor"] = True
                if "immediate" in follow_up_text.lower():
                    follow_up["urgency"] = "immediate"
                break
        
        # Adjust based on risk level
        if risk_level == "high":
            follow_up["timeframe"] = "within 48 hours"
            follow_up["with_doctor"] = True
            follow_up["urgency"] = "urgent"
        elif risk_level == "medium":
            follow_up["timeframe"] = "within 1 week"
            follow_up["with_doctor"] = True
            follow_up["urgency"] = "within 48 hours"
        
        return follow_up
    
    def _check_emergency_conditions(self, symptoms: List[Dict[str, Any]], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Check for emergency conditions"""
        emergency_alert = {
            "triggered": False,
            "reason": "",
            "actions": []
        }
        
        # Check symptoms against emergency criteria
        symptom_names = [s.get("name", "").lower() for s in symptoms]
        primary_condition = diagnosis.get("primary_condition", "").lower()
        risk_level = diagnosis.get("risk_level", "low")
        
        # High risk conditions automatically trigger emergency alert
        if risk_level == "high":
            emergency_alert["triggered"] = True
            emergency_alert["reason"] = "High risk condition detected"
            emergency_alert["actions"] = [
                "Seek immediate medical attention",
                "Go to emergency room or call emergency services",
                "Do not drive yourself if experiencing severe symptoms"
            ]
            return emergency_alert
        
        # Check for emergency symptoms
        for symptom in symptom_names:
            for criterion in self.emergency_criteria:
                if criterion in symptom:
                    emergency_alert["triggered"] = True
                    emergency_alert["reason"] = f"Emergency symptom detected: {symptom}"
                    emergency_alert["actions"] = [
                        "Call emergency services immediately",
                        "Go to nearest emergency room",
                        "Do not wait for symptoms to improve"
                    ]
                    return emergency_alert
        
        return emergency_alert
    
    def _recommend_doctors(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend appropriate doctors"""
        primary_condition = diagnosis.get("primary_condition", "").lower()
        medical_specialty = diagnosis.get("medical_specialty", "")
        
        # Determine specialty
        if medical_specialty:
            specialty = medical_specialty
        else:
            specialty = "General Practice"
            for condition_key, mapped_specialty in self.specialty_mapping.items():
                if condition_key in primary_condition or primary_condition in condition_key:
                    specialty = mapped_specialty
                    break
        
        # Generate recommendations
        recommendations = {
            "specialties": [specialty],
            "urgency": "routine",
            "reasoning": f"Based on your symptoms and diagnosis of {diagnosis.get('primary_condition', 'unknown')}",
            "local_options": [],  # Would be populated with actual doctor data
            "questions_to_ask": self._generate_questions_for_doctor(primary_condition),
            "preparation": self._generate_preparation_for_visit(primary_condition)
        }
        
        # Adjust urgency based on risk level
        risk_level = diagnosis.get("risk_level", "low")
        if risk_level == "high":
            recommendations["urgency"] = "immediate"
        elif risk_level == "medium":
            recommendations["urgency"] = "within 48 hours"
        
        return recommendations
    
    def _generate_questions_for_doctor(self, primary_condition: str) -> List[str]:
        """Generate questions to ask the doctor"""
        general_questions = [
            "What is the likely cause of my symptoms?",
            "What treatment options are available?",
            "When should I expect to see improvement?",
            "What symptoms should prompt me to seek emergency care?"
        ]
        
        condition_specific = {
            "migraine": [
                "What type of migraines do I have?",
                "What are the best preventive medications?",
                "What are my migraine triggers?"
            ],
            "hypertension": [
                "What should my target blood pressure be?",
                "How often should I monitor my blood pressure?",
                "What lifestyle changes are most important?"
            ],
            "gastroenteritis": [
                "How can I prevent dehydration?",
                "When can I return to normal diet?",
                "What are signs of complications?"
            ]
        }
        
        questions = general_questions
        for condition_key, specific_questions in condition_specific.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                questions.extend(specific_questions)
                break
        
        return questions[:6]  # Limit to 6 questions
    
    def _generate_preparation_for_visit(self, primary_condition: str) -> List[str]:
        """Generate preparation tips for doctor visit"""
        general_preparation = [
            "Write down all symptoms and when they started",
            "List all medications you're currently taking",
            "Bring a list of questions to ask",
            "Consider bringing a family member for support"
        ]
        
        condition_specific = {
            "migraine": [
                "Keep a headache diary before the visit",
                "Note any potential triggers",
                "List previous treatments tried"
            ],
            "hypertension": [
                "Bring recent blood pressure readings",
                "List all salt intake sources",
                "Note any exercise routine"
            ],
            "gastroenteritis": [
            "Track fluid intake and output",
                "Note any foods that worsen symptoms",
                "Record temperature readings"
            ]
        }
        
        preparation = general_preparation
        for condition_key, specific_preparation in condition_specific.items():
            if condition_key in primary_condition or primary_condition in condition_key:
                preparation.extend(specific_preparation)
                break
        
        return preparation[:5]  # Limit to 5 tips
    
    def _get_medical_disclaimer(self) -> str:
        """Get medical disclaimer"""
        return "This AI-generated advice is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition."
    
    async def recommend_doctors(self, diagnosis: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Recommend doctors based on diagnosis"""
        return self._recommend_doctors(diagnosis)
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        diagnosis = data.get("diagnosis", {})
        symptoms = data.get("symptoms", [])
        
        return isinstance(diagnosis, dict) and isinstance(symptoms, list)
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "condition_recommendations_loaded": len(self.condition_recommendations) > 0,
            "specialty_mapping_loaded": len(self.specialty_mapping) > 0,
            "emergency_criteria_loaded": len(self.emergency_criteria) > 0,
            "test_recommendation": await self._test_recommendation()
        }
    
    async def _test_recommendation(self) -> bool:
        """Test recommendation generation"""
        try:
            test_data = {
                "diagnosis": {"primary_condition": "Common Cold", "risk_level": "low"},
                "symptoms": [{"name": "cough", "severity": "mild"}]
            }
            result = await self._process(test_data)
            return "recommendations" in result
        except Exception:
            return False
    
    async def _warm_up(self) -> bool:
        """Warm up the agent"""
        try:
            await self._test_recommendation()
            return True
        except Exception:
            return False
