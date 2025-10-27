"""
Complete Security System - Authentication & Authorization
"""
import os
import time
import jwt
import hashlib
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

security = HTTPBearer()

# Security Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "mordzix-super-secret-2025")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

class SecurityManager:
    """Complete security management system"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.rate_limits: Dict[str, List[float]] = {}
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is temporarily blocked"""
        if ip in self.blocked_ips:
            if time.time() - self.blocked_ips[ip] > 3600:  # 1 hour block
                del self.blocked_ips[ip]
                return False
            return True
        return False
    
    def record_failed_attempt(self, ip: str):
        """Record failed authentication attempt"""
        now = time.time()
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []
        
        # Clean old attempts (older than 15 minutes)
        self.failed_attempts[ip] = [
            attempt for attempt in self.failed_attempts[ip] 
            if now - attempt < 900
        ]
        
        self.failed_attempts[ip].append(now)
        
        # Block IP after 5 failed attempts
        if len(self.failed_attempts[ip]) >= 5:
            self.blocked_ips[ip] = now
    
    def check_rate_limit(self, ip: str, endpoint: str, limit: int = 100) -> bool:
        """Check if request exceeds rate limit"""
        key = f"{ip}:{endpoint}"
        now = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Clean old requests (older than 1 hour)
        self.rate_limits[key] = [
            req_time for req_time in self.rate_limits[key]
            if now - req_time < 3600
        ]
        
        if len(self.rate_limits[key]) >= limit:
            return False
        
        self.rate_limits[key].append(now)
        return True

# Global security manager instance
security_manager = SecurityManager()

def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify authentication token (supports both JWT and simple tokens)"""
    token = credentials.credentials
    
    # Try JWT first
    try:
        return verify_jwt_token(token)
    except HTTPException:
        pass
    
    # Fallback to simple token
    expected_token = os.getenv("AUTH_TOKEN", "changeme")
    if token == expected_token:
        return {"user_id": "default", "type": "simple", "token": token}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

async def auth_dependency(request: Request) -> Dict[str, Any]:
    """Advanced authentication dependency with security features"""
    client_ip = get_client_ip(request)
    
    # Check if IP is blocked
    if security_manager.is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="IP temporarily blocked due to too many failed attempts"
        )
    
    # Check rate limiting
    endpoint = request.url.path
    if not security_manager.check_rate_limit(client_ip, endpoint):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Check authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        security_manager.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    if not auth_header.startswith("Bearer "):
        security_manager.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Try JWT first
        try:
            user_data = verify_jwt_token(token)
            return user_data
        except HTTPException:
            pass
        
        # Fallback to simple token
        expected_token = os.getenv("AUTH_TOKEN", "changeme")
        if token == expected_token:
            return {"user_id": "default", "type": "simple", "ip": client_ip}
        
        security_manager.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        
    except Exception as e:
        security_manager.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Legacy compatibility
def _auth(request: Request) -> bool:
    """Legacy auth function for backwards compatibility"""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(auth_dependency(request))
        return True
    except:
        return False

# Admin-level authentication
async def admin_auth(request: Request) -> Dict[str, Any]:
    """Admin-level authentication with elevated privileges"""
    user_data = await auth_dependency(request)
    
    # Check if user has admin privileges
    admin_token = os.getenv("ADMIN_TOKEN", os.getenv("AUTH_TOKEN", "changeme"))
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    
    if token != admin_token and user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    user_data["is_admin"] = True
    return user_data

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed