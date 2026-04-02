"""
Authentication utilities for the Agentic AI Medical Diagnosis System
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, status
from jose import JWTError

from .config import settings
from .logger import log_error


async def verify_token(token: str) -> Dict:
    """
    Verify JWT token and extract payload
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload dictionary
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        log_error(e, {"context": "token_verification", "token_preview": token[:20] + "..."})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        log_error(e, {"context": "token_verification"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


def create_token(payload: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token
    
    Args:
        payload: Token payload data
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = payload.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
    
    to_encode.update({"exp": expire})
    
    # Create token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def extract_user_from_token(token: str) -> Optional[Dict]:
    """
    Extract user information from token without verification (for testing)
    
    Args:
        token: JWT token string
        
    Returns:
        User information dictionary or None
    """
    try:
        # Decode without verification (for testing only)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None


def validate_user_permissions(user_id: str, required_permissions: list) -> bool:
    """
    Validate if user has required permissions
    
    Args:
        user_id: User identifier
        required_permissions: List of required permissions
        
    Returns:
        True if user has all required permissions
    """
    # This would typically check against a database or permission service
    # For now, we'll implement a simple check
    
    # Mock user permissions (in real implementation, fetch from database)
    user_permissions = {
        "basic": ["diagnose", "chat", "upload_reports"],
        "premium": ["diagnose", "chat", "upload_reports", "advanced_analysis"],
        "admin": ["diagnose", "chat", "upload_reports", "advanced_analysis", "system_admin"]
    }
    
    # Get user role (in real implementation, fetch from database)
    user_role = "basic"  # Default role
    
    # Check permissions
    available_permissions = user_permissions.get(user_role, [])
    return all(perm in available_permissions for perm in required_permissions)


def get_user_from_request(request) -> Optional[Dict]:
    """
    Extract user information from HTTP request
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information dictionary or None
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Verify token and extract payload
        payload = await verify_token(token)
        
        return payload
        
    except Exception:
        return None


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class AuthorizationError(Exception):
    """Custom authorization error"""
    pass


def require_auth(required_permissions: list = None):
    """
    Decorator to require authentication and optional permissions
    
    Args:
        required_permissions: List of required permissions
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a FastAPI dependency in real usage
            # For now, this is a placeholder for the concept
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            identifier: Unique identifier (user ID, IP address, etc.)
            
        Returns:
            True if request is allowed
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Get existing requests for identifier
        user_requests = self.requests.get(identifier, [])
        
        # Remove old requests outside window
        user_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            self.requests[identifier] = user_requests
            return True
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=50, window_seconds=900)  # 50 requests per 15 minutes
