"""
Logging configuration for the Agentic AI Medical Diagnosis System
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from .config import settings


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Setup logger with consistent formatting and handlers
    
    Args:
        name: Logger name
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if settings.log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_ai_service(service: str, action: str, details: dict = None):
    """
    Log AI service activity with structured information
    
    Args:
        service: Name of the AI service/agent
        action: Action being performed
        details: Additional details to log
    """
    logger = logging.getLogger("ai_services")
    
    log_data = {
        "service": service,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        **(details or {})
    }
    
    # Log as structured message
    logger.info(f"AI_SERVICE: {service} - {action} - {log_data}")


def log_agent_performance(agent: str, operation: str, duration: float, details: dict = None):
    """
    Log agent performance metrics
    
    Args:
        agent: Agent name
        operation: Operation performed
        duration: Duration in seconds
        details: Additional performance details
    """
    logger = logging.getLogger("agent_performance")
    
    perf_data = {
        "agent": agent,
        "operation": operation,
        "duration_seconds": duration,
        "timestamp": datetime.utcnow().isoformat(),
        **(details or {})
    }
    
    logger.info(f"PERFORMANCE: {agent} - {operation} - {duration:.3f}s - {perf_data}")


def log_error(error: Exception, context: dict = None):
    """
    Log error with context information
    
    Args:
        error: Exception that occurred
        context: Additional context information
    """
    logger = logging.getLogger("errors")
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        **(context or {})
    }
    
    logger.error(f"ERROR: {type(error).__name__} - {str(error)} - {error_data}", exc_info=True)


def log_user_activity(user_id: str, action: str, details: dict = None):
    """
    Log user activity for auditing
    
    Args:
        user_id: User identifier
        action: Action performed
        details: Additional details
    """
    logger = logging.getLogger("user_activity")
    
    activity_data = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        **(details or {})
    }
    
    logger.info(f"USER_ACTIVITY: {user_id} - {action} - {activity_data}")


def log_medical_decision(decision_type: str, input_data: dict, output_data: dict, confidence: float):
    """
    Log medical decision for audit trail
    
    Args:
        decision_type: Type of medical decision
        input_data: Input data used for decision
        output_data: Output decision data
        confidence: Confidence score (0-1)
    """
    logger = logging.getLogger("medical_decisions")
    
    decision_data = {
        "decision_type": decision_type,
        "input_hash": hash(str(input_data)) % 10000,  # Simple hash for privacy
        "output_summary": {
            "risk_level": output_data.get("risk_level"),
            "primary_condition": output_data.get("primary_condition"),
            "recommendations_count": len(output_data.get("recommendations", []))
        },
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"MEDICAL_DECISION: {decision_type} - confidence:{confidence:.2f} - {decision_data}")


# Create module-level loggers
main_logger = setup_logger("main")
agent_logger = setup_logger("agents")
service_logger = setup_logger("services")
model_logger = setup_logger("models")
