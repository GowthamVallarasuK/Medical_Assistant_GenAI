"""
Configuration settings for the Agentic AI Medical Diagnosis System
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "development"
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5000", "http://localhost:5173"]
    
    # Authentication
    jwt_secret: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    
    # Database Configuration
    mongodb_uri: str = "mongodb://localhost:27017/medical_diagnosis"
    
    # AI Services Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.3
    
    # Hugging Face Configuration
    hf_model_name: str = "dmis-lab/biobert-base-cased-v1.1"
    hf_cache_dir: str = "./models/huggingface"
    
    # Vector Database Configuration
    vector_db_path: str = "./data/vector_db"
    embedding_dimension: int = 768
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "text/plain",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    upload_dir: str = "./uploads"
    
    # OCR Configuration
    tesseract_path: Optional[str] = None  # Auto-detected if None
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/ai_services.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Agent Configuration
    agent_timeout: int = 30  # seconds
    max_concurrent_agents: int = 5
    
    # Medical Knowledge Base
    knowledge_base_path: str = "./data/medical_knowledge"
    symptom_database_path: str = "./data/symptoms.json"
    condition_database_path: str = "./data/conditions.json"
    
    # Caching Configuration
    cache_ttl: int = 3600  # 1 hour
    redis_url: Optional[str] = None
    
    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 8001
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def assemble_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("debug", pre=True)
    def assemble_debug(cls, v):
        return v if isinstance(v, bool) else v.lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
