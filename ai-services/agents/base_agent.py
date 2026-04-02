"""
Base Agent class for the Agentic AI Medical Diagnosis System
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logger import log_agent_performance, log_ai_service, log_error


class BaseAgent(ABC):
    """
    Base class for all AI agents in the medical diagnosis system
    
    This class provides common functionality for all agents including:
    - Performance logging
    - Error handling
    - Timeout management
    - Health checks
    """
    
    def __init__(self, name: str, timeout: int = 30):
        """
        Initialize base agent
        
        Args:
            name: Agent name for logging
            timeout: Operation timeout in seconds
        """
        self.name = name
        self.timeout = timeout
        self.is_initialized = False
        self.last_health_check = None
        self.health_status = "unknown"
        
    async def initialize(self) -> bool:
        """
        Initialize the agent
        
        Returns:
            True if initialization successful
        """
        try:
            start_time = time.time()
            
            # Perform agent-specific initialization
            success = await self._initialize()
            
            initialization_time = time.time() - start_time
            
            if success:
                self.is_initialized = True
                log_agent_performance(self.name, "initialization", initialization_time)
                log_ai_service(self.name, "agent_initialized", {
                    "initialization_time": initialization_time
                })
            else:
                log_error(Exception(f"Agent {self.name} initialization failed"))
                
            return success
            
        except Exception as e:
            log_error(e, {"context": f"Agent {self.name} initialization"})
            return False
    
    @abstractmethod
    async def _initialize(self) -> bool:
        """
        Agent-specific initialization logic
        
        Returns:
            True if initialization successful
        """
        pass
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data through the agent
        
        Args:
            data: Input data for processing
            
        Returns:
            Processed data with results
            
        Raises:
            TimeoutError: If processing exceeds timeout
            Exception: If processing fails
        """
        if not self.is_initialized:
            raise RuntimeError(f"Agent {self.name} not initialized")
        
        start_time = time.time()
        
        try:
            # Process with timeout
            result = await asyncio.wait_for(
                self._process(data),
                timeout=self.timeout
            )
            
            processing_time = time.time() - start_time
            
            # Add metadata to result
            result["agent_metadata"] = {
                "agent": self.name,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
            log_agent_performance(self.name, "processing", processing_time, {
                "input_size": len(str(data)),
                "output_size": len(str(result))
            })
            
            return result
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            log_agent_performance(self.name, "timeout", processing_time)
            log_ai_service(self.name, "processing_timeout", {
                "processing_time": processing_time,
                "timeout_limit": self.timeout
            })
            raise TimeoutError(f"Agent {self.name} processing timed out after {self.timeout}s")
            
        except Exception as e:
            processing_time = time.time() - start_time
            log_error(e, {
                "context": f"Agent {self.name} processing",
                "processing_time": processing_time
            })
            
            # Return error result
            return {
                "agent_metadata": {
                    "agent": self.name,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": str(e)
                },
                "error": str(e)
            }
    
    @abstractmethod
    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent-specific processing logic
        
        Args:
            data: Input data for processing
            
        Returns:
            Processed data with results
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the agent
        
        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            
            # Perform agent-specific health check
            health_data = await self._health_check()
            
            health_check_time = time.time() - start_time
            self.last_health_check = datetime.utcnow()
            
            # Build health status
            status = {
                "agent": self.name,
                "status": "healthy",
                "initialized": self.is_initialized,
                "last_health_check": self.last_health_check.isoformat(),
                "health_check_time": health_check_time,
                "details": health_data
            }
            
            self.health_status = "healthy"
            return status
            
        except Exception as e:
            self.health_status = "unhealthy"
            log_error(e, {"context": f"Agent {self.name} health check"})
            
            return {
                "agent": self.name,
                "status": "unhealthy",
                "initialized": self.is_initialized,
                "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
                "error": str(e)
            }
    
    @abstractmethod
    async def _health_check(self) -> Dict[str, Any]:
        """
        Agent-specific health check logic
        
        Returns:
            Health check details
        """
        pass
    
    async def warm_up(self) -> bool:
        """
        Warm up the agent (preload models, etc.)
        
        Returns:
            True if warm up successful
        """
        try:
            start_time = time.time()
            
            # Perform agent-specific warm up
            success = await self._warm_up()
            
            warm_up_time = time.time() - start_time
            
            log_agent_performance(self.name, "warm_up", warm_up_time)
            log_ai_service(self.name, "agent_warmed_up", {
                "warm_up_time": warm_up_time
            })
            
            return success
            
        except Exception as e:
            log_error(e, {"context": f"Agent {self.name} warm up"})
            return False
    
    async def _warm_up(self) -> bool:
        """
        Agent-specific warm up logic
        
        Returns:
            True if warm up successful
        """
        # Default implementation - override if needed
        return True
    
    async def cleanup(self):
        """
        Clean up agent resources
        """
        try:
            # Perform agent-specific cleanup
            await self._cleanup()
            
            self.is_initialized = False
            log_ai_service(self.name, "agent_cleaned_up")
            
        except Exception as e:
            log_error(e, {"context": f"Agent {self.name} cleanup"})
    
    async def _cleanup(self):
        """
        Agent-specific cleanup logic
        """
        # Default implementation - override if needed
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status
        
        Returns:
            Agent status information
        """
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "timeout": self.timeout
        }
    
    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data
        
        Args:
            data: Input data to validate
            
        Returns:
            True if input is valid
        """
        try:
            # Perform agent-specific validation
            return await self._validate_input(data)
        except Exception as e:
            log_error(e, {"context": f"Agent {self.name} input validation"})
            return False
    
    async def _validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Agent-specific input validation
        
        Args:
            data: Input data to validate
            
        Returns:
            True if input is valid
        """
        # Default implementation - override if needed
        return True
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent capabilities
        
        Returns:
            Agent capabilities information
        """
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": self.__doc__ or "No description available",
            "initialized": self.is_initialized,
            "health_status": self.health_status,
            "supported_operations": getattr(self, "_supported_operations", []),
            "input_types": getattr(self, "_input_types", []),
            "output_types": getattr(self, "_output_types", [])
        }
