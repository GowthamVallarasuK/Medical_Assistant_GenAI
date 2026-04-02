"""
Orchestrator Agent - Coordinates all other AI agents
"""

import asyncio
import time
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent
from ..utils.logger import log_ai_service, log_agent_performance


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - The brain of the system
    
    This agent is responsible for:
    - Coordinating all other agents
    - Managing the workflow
    - Combining outputs from all agents
    - Making final decisions
    - Handling emergency situations
    """
    
    def __init__(self, symptom_analyzer, diagnosis_generator, report_analyzer, recommendation_agent):
        super().__init__("orchestrator")
        self.symptom_analyzer = symptom_analyzer
        self.diagnosis_generator = diagnosis_generator
        self.report_analyzer = report_analyzer
        self.recommendation_agent = recommendation_agent
        
    async def _initialize(self) -> bool:
        """Initialize the orchestrator and all agents"""
        try:
            # Initialize all agents
            agents = [
                self.symptom_analyzer,
                self.diagnosis_generator,
                self.report_analyzer,
                self.recommendation_agent
            ]
            
            for agent in agents:
                success = await agent.initialize()
                if not success:
                    log_ai_service(self.name, "agent_initialization_failed", {"agent": agent.name})
                    return False
            
            log_ai_service(self.name, "orchestrator_initialized", {
                "agents_initialized": len(agents),
                "agents": [agent.name for agent in agents]
            })
            
            return True
            
        except Exception as e:
            log_ai_service(self.name, "initialization_failed", {"error": str(e)})
            return False
    
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process diagnosis request through all agents"""
        message = data.get("message", "")
        files = data.get("files", [])
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        try:
            start_time = time.time()
            workflow_steps = []
            agent_results = {}
            
            log_ai_service(self.name, "diagnosis_workflow_started", {
                "user_id": user_id,
                "session_id": session_id,
                "message_length": len(message),
                "files_count": len(files)
            })
            
            # Step 1: Analyze symptoms
            workflow_steps.append("symptom_analysis")
            symptom_result = await self.symptom_analyzer.process({
                "message": message,
                "user_id": user_id,
                "session_id": session_id
            })
            agent_results["symptom_analyzer"] = symptom_result
            
            # Step 2: Analyze uploaded files (if any)
            if files:
                workflow_steps.append("report_analysis")
                file_results = []
                for file in files:
                    file_result = await self.report_analyzer.process({
                        "file_content": file.get("content", b""),
                        "filename": file.get("filename", ""),
                        "content_type": file.get("file_type", ""),
                        "user_id": user_id
                    })
                    file_results.append(file_result)
                agent_results["report_analyzer"] = {"files": file_results}
            
            # Step 3: Generate diagnosis
            workflow_steps.append("diagnosis_generation")
            diagnosis_result = await self.diagnosis_generator.process({
                "symptoms": symptom_result.get("symptoms", []),
                "user_id": user_id,
                "session_id": session_id
            })
            agent_results["diagnosis_generator"] = diagnosis_result
            
            # Step 4: Generate recommendations
            workflow_steps.append("recommendation_generation")
            recommendation_result = await self.recommendation_agent.process({
                "diagnosis": diagnosis_result.get("diagnosis", {}),
                "symptoms": symptom_result.get("symptoms", []),
                "user_id": user_id,
                "session_id": session_id
            })
            agent_results["recommendation_agent"] = recommendation_result
            
            # Step 5: Combine and format final response
            final_result = await self._combine_results(
                symptom_result,
                diagnosis_result,
                recommendation_result,
                agent_results.get("report_analyzer"),
                workflow_steps,
                start_time
            )
            
            log_ai_service(self.name, "diagnosis_workflow_completed", {
                "user_id": user_id,
                "session_id": session_id,
                "processing_time": final_result.get("processing_time", 0),
                "workflow_steps": workflow_steps,
                "risk_level": final_result.get("risk_level", "unknown")
            })
            
            return final_result
            
        except Exception as e:
            log_ai_service(self.name, "diagnosis_workflow_failed", {
                "user_id": user_id,
                "session_id": session_id,
                "error": str(e)
            })
            raise
    
    async def _combine_results(
        self,
        symptom_result: Dict[str, Any],
        diagnosis_result: Dict[str, Any],
        recommendation_result: Dict[str, Any],
        report_result: Optional[Dict[str, Any]],
        workflow_steps: List[str],
        start_time: float
    ) -> Dict[str, Any]:
        """Combine results from all agents into final response"""
        
        processing_time = time.time() - start_time
        
        # Extract key information
        symptoms = symptom_result.get("symptoms", [])
        diagnosis = diagnosis_result.get("diagnosis", {})
        risk_assessment = diagnosis_result.get("risk_assessment", {})
        recommendations = recommendation_result.get("recommendations", [])
        lifestyle_advice = recommendation_result.get("lifestyle_advice", [])
        precautions = recommendation_result.get("precautions", [])
        follow_up = recommendation_result.get("follow_up", {})
        emergency_alert = recommendation_result.get("emergency_alert", {})
        
        # Process uploaded files
        uploaded_files = []
        if report_result and "files" in report_result:
            for i, file_result in enumerate(report_result["files"]):
                uploaded_files.append({
                    "filename": f"file_{i+1}",
                    "analysis": {
                        "key_findings": file_result.get("key_findings", []),
                        "lab_values": file_result.get("lab_values", []),
                        "abnormalities": file_result.get("abnormalities", [])
                    }
                })
        
        # Generate human-readable response
        response = self._generate_response(
            symptoms,
            diagnosis,
            risk_assessment,
            recommendations,
            emergency_alert
        )
        
        # Build final result
        final_result = {
            "success": True,
            "response": response,
            "session_id": str(time.time()),  # Fallback session id
            "risk_level": risk_assessment.get("risk_level", "low"),
            "risk_score": risk_assessment.get("risk_score", 20),
            "symptoms": symptoms,
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "precautions": precautions,
            "medications": [],  # Could be added later
            "lifestyle_advice": lifestyle_advice,
            "follow_up": follow_up,
            "emergency_alert": emergency_alert,
            "uploaded_files": uploaded_files,
            "ai_agents": {
                "symptom_analyzer": {
                    "processed": True,
                    "processing_time": symptom_result.get("agent_metadata", {}).get("processing_time", 0),
                    "confidence": symptom_result.get("extraction_confidence", 0.5)
                },
                "diagnosis_generator": {
                    "processed": True,
                    "processing_time": diagnosis_result.get("agent_metadata", {}).get("processing_time", 0),
                    "confidence": diagnosis.get("confidence", 0.5)
                },
                "report_analyzer": {
                    "processed": len(uploaded_files) > 0,
                    "processing_time": sum(
                        f.get("agent_metadata", {}).get("processing_time", 0) 
                        for f in report_result.get("files", []) if isinstance(f, dict)
                    ) if report_result else 0,
                    "confidence": 0.7  # Mock confidence
                },
                "recommendation_agent": {
                    "processed": True,
                    "processing_time": recommendation_result.get("agent_metadata", {}).get("processing_time", 0),
                    "confidence": 0.8  # Mock confidence
                },
                "orchestrator": {
                    "total_processing_time": processing_time,
                    "workflow_steps": workflow_steps,
                    "final_confidence": diagnosis.get("confidence", 0.5)
                }
            },
            "processing_time": processing_time,
            "timestamp": time.time()
        }
        
        return final_result
    
    def _generate_response(
        self,
        symptoms: List[Dict[str, Any]],
        diagnosis: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        recommendations: List[str],
        emergency_alert: Dict[str, Any]
    ) -> str:
        """Generate human-readable response"""
        
        primary_condition = diagnosis.get("primary_condition", "Unknown condition")
        confidence = diagnosis.get("confidence", 0) * 100
        risk_level = risk_assessment.get("risk_level", "low")
        
        response_parts = []
        
        # Start with diagnosis
        response_parts.append(f"Based on your symptoms, I've identified **{primary_condition}** as the most likely condition.")
        response_parts.append(f"Confidence level: {confidence:.0f}%")
        
        # Add alternative conditions if any
        alternatives = diagnosis.get("alternative_conditions", [])
        if alternatives:
            response_parts.append(f"Alternative possibilities include: {', '.join(alternatives[:2])}")
        
        # Add risk assessment
        response_parts.append(f"**Risk Level: {risk_level.upper()}**")
        
        # Add symptoms summary
        if symptoms:
            symptom_names = [s.get("name", "") for s in symptoms[:3]]
            response_parts.append(f"Key symptoms identified: {', '.join(symptom_names)}")
        
        # Add recommendations
        if recommendations:
            response_parts.append("\n**Recommendations:**")
            for i, rec in enumerate(recommendations[:3], 1):
                response_parts.append(f"{i}. {rec}")
        
        # Add emergency alert if triggered
        if emergency_alert.get("triggered"):
            response_parts.append("\n⚠️ **EMERGENCY ALERT**")
            response_parts.append(emergency_alert.get("reason", ""))
            response_parts.append("\n**Immediate Actions:**")
            for action in emergency_alert.get("actions", []):
                response_parts.append(f"• {action}")
        else:
            # Add follow-up information
            follow_up = risk_assessment.get("urgency", "routine")
            response_parts.append(f"\n**Follow-up:** {follow_up}")
        
        # Add medical disclaimer
        response_parts.append("\n*This assessment is for informational purposes only and should not replace professional medical advice.*")
        
        return "\n\n".join(response_parts)
    
    async def process_chat(self, message: str, conversation_history: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Process chat message"""
        try:
            # For now, use symptom analyzer for chat processing
            # In a full implementation, this would have more sophisticated chat logic
            result = await self.symptom_analyzer.process({
                "message": message,
                "user_id": user_id
            })
            
            # Generate chat response
            response = self._generate_chat_response(message, result, conversation_history)
            
            return {
                "response": response,
                "suggestions": self._generate_chat_suggestions(result),
                "is_medical_query": self._is_medical_query(message),
                "requires_doctor": self._requires_doctor(result),
                "confidence": result.get("extraction_confidence", 0.5),
                "processing_time": result.get("agent_metadata", {}).get("processing_time", 0),
                "timestamp": time.time()
            }
            
        except Exception as e:
            log_ai_service(self.name, "chat_processing_failed", {
                "user_id": user_id,
                "error": str(e)
            })
            raise
    
    def _generate_chat_response(self, message: str, symptom_result: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """Generate chat response"""
        symptoms = symptom_result.get("symptoms", [])
        
        if symptoms:
            symptom_names = [s.get("name", "") for s in symptoms[:3]]
            response = f"I can see you're experiencing {', '.join(symptom_names)}. "
            response += "Would you like me to provide a detailed analysis of these symptoms? "
            response += "You can also upload any medical reports if you have them."
        else:
            response = "I'm here to help with your medical concerns. "
            response += "Please describe your symptoms in detail, and I'll provide an analysis. "
            response += "You can also upload medical reports for a more comprehensive assessment."
        
        return response
    
    def _generate_chat_suggestions(self, symptom_result: Dict[str, Any]) -> List[str]:
        """Generate chat suggestions"""
        suggestions = [
            "Describe your symptoms in detail",
            "Upload medical reports (PDF, images)",
            "Ask about specific conditions",
            "Request doctor recommendations"
        ]
        
        symptoms = symptom_result.get("symptoms", [])
        if symptoms:
            suggestions.insert(0, "Get detailed analysis of current symptoms")
        
        return suggestions[:3]
    
    def _is_medical_query(self, message: str) -> bool:
        """Check if message is a medical query"""
        medical_keywords = [
            "symptom", "pain", "fever", "headache", "cough", "nausea",
            "diagnosis", "medicine", "treatment", "doctor", "medical"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in medical_keywords)
    
    def _requires_doctor(self, symptom_result: Dict[str, Any]) -> bool:
        """Check if doctor consultation is recommended"""
        symptoms = symptom_result.get("symptoms", [])
        
        # Check for severe symptoms
        for symptom in symptoms:
            severity = symptom.get("severity", "").lower()
            if severity == "severe":
                return True
        
        return False
    
    async def assess_emergency(self, symptoms: List[str]) -> Dict[str, Any]:
        """Assess if symptoms indicate emergency"""
        try:
            # Use recommendation agent's emergency criteria
            mock_diagnosis = {"primary_condition": "Unknown", "risk_level": "low"}
            emergency_alert = self.recommendation_agent._check_emergency_conditions(
                [{"name": symptom} for symptom in symptoms],
                mock_diagnosis
            )
            
            return {
                "is_emergency": emergency_alert.get("triggered", False),
                "urgency_level": emergency_alert.get("reason", "No emergency detected"),
                "immediate_actions": emergency_alert.get("actions", []),
                "emergency_services": emergency_alert.get("triggered", False),
                "reasoning": emergency_alert.get("reason", ""),
                "confidence": 0.8
            }
            
        except Exception as e:
            return {
                "is_emergency": False,
                "urgency_level": "Unable to assess",
                "immediate_actions": ["Seek medical attention if concerned"],
                "emergency_services": False,
                "reasoning": "Assessment failed",
                "confidence": 0.1
            }
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        message = data.get("message", "")
        return isinstance(message, str) and len(message.strip()) > 0
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check of all agents"""
        agent_health = {}
        total_agents = 0
        healthy_agents = 0
        
        agents = {
            "symptom_analyzer": self.symptom_analyzer,
            "diagnosis_generator": self.diagnosis_generator,
            "report_analyzer": self.report_analyzer,
            "recommendation_agent": self.recommendation_agent
        }
        
        for name, agent in agents.items():
            try:
                health = await agent.health_check()
                agent_health[name] = health
                total_agents += 1
                if health.get("status") == "healthy":
                    healthy_agents += 1
            except Exception as e:
                agent_health[name] = {"status": "error", "error": str(e)}
                total_agents += 1
        
        return {
            "orchestrator_status": "healthy",
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "agent_health": agent_health,
            "overall_health": "healthy" if healthy_agents == total_agents else "degraded"
        }
    
    async def _test_diagnosis(self) -> bool:
        """Test full diagnosis workflow"""
        try:
            test_data = {
                "message": "I have a headache and fever",
                "files": [],
                "user_id": "test_user",
                "session_id": "test_session"
            }
            
            result = await self.process(test_data)
            return result.get("success", False)
            
        except Exception:
            return False
    
    async def _warm_up(self) -> bool:
        """Warm up all agents"""
        try:
            agents = [
                self.symptom_analyzer,
                self.diagnosis_generator,
                self.report_analyzer,
                self.recommendation_agent
            ]
            
            for agent in agents:
                await agent.warm_up()
            
            # Test full workflow
            await self._test_diagnosis()
            
            return True
            
        except Exception:
            return False
    
    async def cleanup(self):
        """Clean up all agents"""
        agents = [
            self.symptom_analyzer,
            self.diagnosis_generator,
            self.report_analyzer,
            self.recommendation_agent
        ]
        
        for agent in agents:
            try:
                await agent.cleanup()
            except Exception:
                pass  # Ignore cleanup errors
        
        await super().cleanup()
