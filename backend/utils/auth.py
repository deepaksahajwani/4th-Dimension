"""
Authentication utilities
Handles JWT tokens, password hashing, and user authentication
"""
import os
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, Field, ConfigDict, EmailStr
import uuid
from typing import Optional

from utils.database import get_database

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT settings
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', 10080))

db = get_database()

# User model
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    date_of_joining: Optional[datetime] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    role: str
    preferred_language: str = 'en'
    salary: Optional[float] = None
    writeup: Optional[str] = None
    passions: Optional[str] = None
    contribution: Optional[str] = None
    password_hash: Optional[str] = None
    picture: Optional[str] = None
    is_owner: bool = False
    is_admin: bool = False
    is_validated: bool = False
    approval_status: str = "pending"
    mobile_verified: bool = False
    email_verified: bool = False
    registration_completed: bool = False
    registered_via: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash password"""
    return pwd_context.hash(password)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    
    try:
        # Check if it's a JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_doc = await db.users.find_one({"email": email}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)
    
    except JWTError:
        # Try Emergent session token
        session = await db.user_sessions.find_one({"session_token": token})
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Check expiry
        if isinstance(session['expires_at'], str):
            expires_at = datetime.fromisoformat(session['expires_at'])
        else:
            expires_at = session['expires_at']
        
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user_doc = await db.users.find_one({"id": session['user_id']}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)


async def require_owner(current_user: User = Depends(get_current_user)):
    """Require user to be owner"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Only owner can perform this action")
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)):
    """Require user to be admin or owner"""
    if not current_user.is_owner and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
