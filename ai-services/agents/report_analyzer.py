"""
Report Analyzer Agent - Analyzes medical reports using OCR and NLP
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from io import BytesIO

from .base_agent import BaseAgent
from ..utils.logger import log_ai_service


class ReportAnalyzerAgent(BaseAgent):
    """
    Report Analyzer Agent
    
    This agent is responsible for:
    - Extracting text from medical reports (PDF, images)
    - Identifying key medical findings
    - Extracting laboratory values
    - Analyzing abnormalities
    """
    
    def __init__(self):
        super().__init__("report_analyzer")
        self.medical_terms = self._load_medical_terms()
        self.lab_value_patterns = self._load_lab_value_patterns()
        
    def _load_medical_terms(self) -> Dict[str, List[str]]:
        """Load medical terms and patterns"""
        return {
            "blood_pressure": ["blood pressure", "bp", "systolic", "diastolic"],
            "heart_rate": ["heart rate", "hr", "pulse", "bpm"],
            "temperature": ["temperature", "temp", "fever", "celsius", "fahrenheit"],
            "glucose": ["glucose", "blood sugar", "blood glucose"],
            "cholesterol": ["cholesterol", "ldl", "hdl", "triglycerides"],
            "hemoglobin": ["hemoglobin", "hgb", "hb"],
            "white_blood_cells": ["white blood cells", "wbc", "leukocytes"],
            "red_blood_cells": ["red blood cells", "rbc", "erythrocytes"],
            "platelets": ["platelets", "plt"],
            "abnormalities": ["abnormal", "elevated", "decreased", "high", "low", "critical"]
        }
    
    def _load_lab_value_patterns(self) -> List[re.Pattern]:
        """Load regex patterns for lab values"""
        patterns = [
            re.compile(r'(\d+)\s*\/\s*(\d+)\s*mmHg', re.IGNORECASE),  # Blood pressure
            re.compile(r'(\d+(?:\.\d+)?)\s*bpm', re.IGNORECASE),  # Heart rate
            re.compile(r'(\d+(?:\.\d+)?)\s*°[CF]', re.IGNORECASE),  # Temperature
            re.compile(r'(\d+(?:\.\d+)?)\s*mg/dl', re.IGNORECASE),  # mg/dL values
            re.compile(r'(\d+(?:\.\d+)?)\s*mmol/L', re.IGNORECASE),  # mmol/L values
            re.compile(r'(\d+(?:\.\d+)?)\s*K/μL', re.IGNORECASE),  # Cells per microliter
            re.compile(r'(\d+(?:\.\d+)?)\s*g/dL', re.IGNORECASE),  # g/dL values
        ]
        return patterns
    
    async def _initialize(self) -> bool:
        """Initialize the report analyzer"""
        try:
            # Check if required libraries are available (mock for now)
            # In production, would check for Tesseract, PIL, etc.
            
            log_ai_service(self.name, "report_analyzer_initialized", {
                "medical_terms_loaded": len(self.medical_terms),
                "lab_patterns_loaded": len(self.lab_value_patterns)
            })
            
            return True
            
        except Exception as e:
            log_ai_service(self.name, "initialization_failed", {"error": str(e)})
            return False
    
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical report analysis"""
        file_content = data.get("file_content", b"")
        filename = data.get("filename", "")
        content_type = data.get("content_type", "")
        user_id = data.get("user_id")
        
        try:
            # Extract text from file (mock implementation)
            extracted_text = await self._extract_text(file_content, filename, content_type)
            
            # Analyze extracted text
            key_findings = self._extract_key_findings(extracted_text)
            lab_values = self._extract_lab_values(extracted_text)
            abnormalities = self._identify_abnormalities(key_findings, lab_values)
            
            result = {
                "extracted_text": extracted_text,
                "key_findings": key_findings,
                "lab_values": lab_values,
                "abnormalities": abnormalities,
                "recommendations": self._generate_recommendations(abnormalities),
                "confidence": self._calculate_confidence(extracted_text, lab_values),
                "file_info": {
                    "filename": filename,
                    "content_type": content_type,
                    "text_length": len(extracted_text)
                }
            }
            
            log_ai_service(self.name, "report_analyzed", {
                "user_id": user_id,
                "filename": filename,
                "findings_count": len(key_findings),
                "lab_values_count": len(lab_values),
                "abnormalities_count": len(abnormalities)
            })
            
            return result
            
        except Exception as e:
            log_ai_service(self.name, "report_analysis_failed", {
                "user_id": user_id,
                "filename": filename,
                "error": str(e)
            })
            raise
    
    async def _extract_text(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Extract text from file using OCR or PDF parser"""
        try:
            if "pdf" in content_type.lower() or filename.lower().endswith(".pdf"):
                return self._extract_text_from_pdf(file_content)
            elif "image" in content_type.lower() or filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                return self._extract_text_from_image(file_content)
            else:
                # Plain text or doc — decode directly
                return file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            log_ai_service(self.name, "text_extraction_failed", {"error": str(e), "filename": filename})
            return f"Could not extract text from {filename}: {str(e)}"

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF using pdfplumber or PyMuPDF"""
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception:
            pass

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception:
            pass

        return "PDF text extraction failed. Please ensure pdfplumber or PyMuPDF is installed."

    def _extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image using pytesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(BytesIO(file_content))
            text = pytesseract.image_to_string(image)
            return text.strip() if text.strip() else "No text detected in image."
        except ImportError:
            return "OCR not available. Please install pytesseract and Pillow."
        except Exception as e:
            return f"Image OCR failed: {str(e)}"
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key medical findings from text"""
        findings = []
        text_lower = text.lower()
        
        # Look for medical terms and their context
        for category, terms in self.medical_terms.items():
            for term in terms:
                if term in text_lower:
                    # Extract context around the term
                    context = self._extract_context(text, term, window=50)
                    findings.append(f"{category}: {context}")
        
        # Look for explicit findings
        finding_patterns = [
            r'(normal|abnormal|elevated|decreased|high|low)\s+(\w+)',
            r'(within|outside)\s+(normal|range)',
            r'(no|some|significant)\s+(findings|abnormalities)',
        ]
        
        for pattern in finding_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    findings.append(" ".join(match))
                else:
                    findings.append(match)
        
        return list(set(findings))  # Remove duplicates
    
    def _extract_lab_values(self, text: str) -> List[Dict[str, Any]]:
        """Extract laboratory values from text"""
        lab_values = []
        
        for pattern in self.lab_value_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                value = match.group(0)
                
                # Determine the test type based on the value and context
                test_type = self._identify_test_type(value, text)
                
                # Extract numerical value and unit
                numbers = re.findall(r'\d+(?:\.\d+)?', value)
                unit_match = re.search(r'[a-zA-Z/]+', value)
                
                if numbers:
                    lab_values.append({
                        "test": test_type,
                        "value": numbers[0],
                        "unit": unit_match.group(0) if unit_match else "",
                        "full_text": value,
                        "normal_range": self._get_normal_range(test_type),
                        "status": self._assess_lab_value_status(test_type, float(numbers[0]))
                    })
        
        return lab_values
    
    def _extract_context(self, text: str, term: str, window: int = 50) -> str:
        """Extract context around a term"""
        text_lower = text.lower()
        index = text_lower.find(term.lower())
        
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(text), index + len(term) + window)
        
        return text[start:end].strip()
    
    def _identify_test_type(self, value: str, full_text: str) -> str:
        """Identify the type of lab test based on value and context"""
        value_lower = value.lower()
        text_lower = full_text.lower()
        
        # Check for specific patterns
        if "mmhg" in value_lower:
            return "blood_pressure"
        elif "bpm" in value_lower:
            return "heart_rate"
        elif "°f" in value_lower or "°c" in value_lower:
            return "temperature"
        elif "glucose" in text_lower:
            return "glucose"
        elif "cholesterol" in text_lower or "ldl" in text_lower or "hdl" in text_lower:
            return "cholesterol"
        elif "hemoglobin" in text_lower or "hgb" in text_lower:
            return "hemoglobin"
        elif "wbc" in text_lower or "white" in text_lower:
            return "white_blood_cells"
        elif "platelets" in text_lower:
            return "platelets"
        else:
            return "unknown"
    
    def _get_normal_range(self, test_type: str) -> str:
        """Get normal range for a lab test"""
        normal_ranges = {
            "blood_pressure": "90-120/60-80 mmHg",
            "heart_rate": "60-100 bpm",
            "temperature": "97.0-99.0°F",
            "glucose": "70-100 mg/dL",
            "cholesterol": "<200 mg/dL",
            "ldl": "<100 mg/dL",
            "hdl": ">40 mg/dL",
            "triglycerides": "<150 mg/dL",
            "hemoglobin": "13.5-17.5 g/dL",
            "white_blood_cells": "4.5-11.0 K/μL",
            "platelets": "150-450 K/μL"
        }
        return normal_ranges.get(test_type, "Unknown")
    
    def _assess_lab_value_status(self, test_type: str, value: float) -> str:
        """Assess if lab value is normal, high, or low"""
        # Simplified assessment logic
        if test_type == "blood_pressure":
            # For blood pressure, this is simplified
            if value > 140:  # Systolic
                return "high"
            elif value < 90:
                return "low"
            else:
                return "normal"
        elif test_type == "heart_rate":
            if value > 100:
                return "high"
            elif value < 60:
                return "low"
            else:
                return "normal"
        elif test_type == "temperature":
            if value > 99.0:
                return "high"
            elif value < 97.0:
                return "low"
            else:
                return "normal"
        elif test_type == "glucose":
            if value > 100:
                return "high"
            elif value < 70:
                return "low"
            else:
                return "normal"
        elif test_type == "cholesterol":
            if value > 200:
                return "high"
            else:
                return "normal"
        else:
            return "normal"  # Default
    
    def _identify_abnormalities(self, key_findings: List[str], lab_values: List[Dict[str, Any]]) -> List[str]:
        """Identify abnormalities from findings and lab values"""
        abnormalities = []
        
        # Check lab values for abnormalities
        for lab_value in lab_values:
            if lab_value.get("status") in ["high", "low", "critical"]:
                abnormalities.append(f"{lab_value['test']}: {lab_value['status'].title()}")
        
        # Check key findings for abnormal terms
        abnormal_terms = ["abnormal", "elevated", "decreased", "high", "low", "critical"]
        for finding in key_findings:
            if any(term in finding.lower() for term in abnormal_terms):
                abnormalities.append(finding)
        
        return abnormalities
    
    def _generate_recommendations(self, abnormalities: List[str]) -> List[str]:
        """Generate recommendations based on abnormalities"""
        recommendations = []
        
        if not abnormalities:
            recommendations.append("All values appear to be within normal ranges")
            recommendations.append("Continue routine health monitoring")
        else:
            recommendations.append("Follow up with healthcare provider regarding abnormal values")
            recommendations.append("Consider repeat testing to confirm results")
            
            # Specific recommendations based on abnormality type
            for abnormality in abnormalities:
                abnormality_lower = abnormality.lower()
                if "blood pressure" in abnormality_lower:
                    recommendations.append("Monitor blood pressure regularly")
                    recommendations.append("Consider lifestyle modifications")
                elif "cholesterol" in abnormality_lower:
                    recommendations.append("Dietary changes may help manage cholesterol levels")
                    recommendations.append("Regular exercise recommended")
                elif "glucose" in abnormality_lower:
                    recommendations.append("Monitor blood sugar levels")
                    recommendations.append("Consider dietary modifications")
        
        return recommendations
    
    def _calculate_confidence(self, extracted_text: str, lab_values: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on text length
        if len(extracted_text) > 100:
            confidence += 0.2
        
        # Increase confidence based on lab values found
        if len(lab_values) > 0:
            confidence += 0.2
        
        # Increase confidence if structured data is present
        if "blood pressure" in extracted_text.lower() or "lab" in extracted_text.lower():
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    async def analyze_report(self, file_content: bytes, filename: str, content_type: str, user_id: str) -> Dict[str, Any]:
        """Analyze a medical report file"""
        data = {
            "file_content": file_content,
            "filename": filename,
            "content_type": content_type,
            "user_id": user_id
        }
        
        return await self.process(data)
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        file_content = data.get("file_content", b"")
        filename = data.get("filename", "")
        
        return len(file_content) > 0 and len(filename) > 0
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "medical_terms_loaded": len(self.medical_terms) > 0,
            "lab_patterns_loaded": len(self.lab_value_patterns) > 0,
            "test_analysis": await self._test_analysis()
        }
    
    async def _test_analysis(self) -> bool:
        """Test report analysis"""
        try:
            test_data = {
                "file_content": b"Test report content",
                "filename": "test.txt",
                "content_type": "text/plain"
            }
            result = await self._process(test_data)
            return "extracted_text" in result
        except Exception:
            return False
    
    async def _warm_up(self) -> bool:
        """Warm up the agent"""
        try:
            await self._test_analysis()
            return True
        except Exception:
            return False
