"""
Authentication Routes
Handles user registration, login, OTP verification, and password management
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx
import random
import string

from utils.auth import (
    User, get_current_user, require_owner, require_admin,
    create_access_token, verify_password, get_password_hash
)
from utils.database import get_database

# Import notification triggers
import notification_triggers

db = get_database()

router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PublicRegistration(BaseModel):
    """New public self-registration model"""
    name: str
    email: EmailStr
    mobile: str
    registration_type: str  # client, team_member, contractor, vendor, consultant
    preferred_language: str = 'en'
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    registered_via: str  # email or google

class VerifyRegistrationOTP(BaseModel):
    """Verify both email and phone OTPs"""
    email: EmailStr
    email_otp: str
    phone_otp: str

class SetPasswordAfterOTP(BaseModel):
    """Set password after OTP verification"""
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    """Request password reset"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Reset password with token"""
    token: str
    new_password: str

class CompleteProfile(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: str
    landmark: Optional[str] = None
    city: str
    state: str
    pin_code: str
    email: EmailStr
    mobile: str
    date_of_birth: str
    date_of_joining: str
    gender: str
    marital_status: str
    role: str

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = datetime.now(timezone.utc)


# ==================== ROUTES ====================

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Auto-detect user role
    client = await db.clients.find_one({"email": user_data.email}, {"_id": 0})
    contractor = await db.contractors.find_one({"email": user_data.email}, {"_id": 0})
    
    if client:
        detected_role = "client"
        is_external_user = True
    elif contractor:
        detected_role = "contractor"
        is_external_user = True
    else:
        detected_role = "team_member"
        is_external_user = False
    
    # Check if owner
    is_owner_email = user_data.email.lower() in ["deepaksahajwani@gmail.com", "deepak@4thdimension.com"]
    
    if is_owner_email:
        user = User(
            email=user_data.email,
            name="Deepak Shreechand Sahajwani",
            mobile="+919913899888",
            date_of_birth=datetime(1973, 9, 15),
            date_of_joining=datetime(2010, 1, 1),
            gender="male",
            marital_status="married",
            role="owner",
            password_hash=get_password_hash(user_data.password),
            is_owner=True,
            is_validated=True,
            mobile_verified=True,
            email_verified=True,
            registration_completed=True
        )
    else:
        user = User(
            email=user_data.email,
            name=user_data.name,
            role=detected_role,
            password_hash=get_password_hash(user_data.password),
            is_owner=False,
            is_validated=is_external_user,
            registration_completed=is_external_user
        )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('date_of_birth'):
        user_dict['date_of_birth'] = user_dict['date_of_birth'].isoformat()
    if user_dict.get('date_of_joining'):
        user_dict['date_of_joining'] = user_dict['date_of_joining'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Notify owner
    if not is_owner_email:
        try:
            owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
            if owner:
                notification = {
                    "id": str(uuid4()),
                    "user_id": owner["id"],
                    "message": f"New registration: {user.name} ({user.email}) - Role: {detected_role}",
                    "link": "/pending-registrations",
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.notifications.insert_one(notification)
                
                try:
                    await notification_triggers.notify_owner_new_registration(
                        user.name, user.email, detected_role
                    )
                except Exception as e:
                    print(f"WhatsApp notification failed: {str(e)}")
        except Exception as e:
            print(f"Failed to notify owner: {str(e)}")
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_owner": user.is_owner,
            "is_validated": user.is_validated,
            "registration_completed": user.registration_completed
        },
        "requires_profile_completion": not user.registration_completed
    }


@router.post("/login")
async def login(credentials: UserLogin):
    """User login"""
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check approval status
    approval_status = user_doc.get('approval_status', 'approved')
    if approval_status == 'rejected':
        raise HTTPException(
            status_code=403,
            detail="Your registration was rejected. Please contact admin."
        )
    elif approval_status == 'pending':
        raise HTTPException(
            status_code=403,
            detail="Your registration is pending approval. Please wait for admin approval."
        )
    
    if not user_doc.get('password_hash'):
        raise HTTPException(status_code=401, detail="Please use Google login")
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": credentials.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_doc['id'],
            "email": user_doc['email'],
            "name": user_doc['name'],
            "role": user_doc.get('role', ''),
            "is_owner": user_doc.get('is_owner', False),
            "is_validated": user_doc.get('is_validated', False),
            "approval_status": user_doc.get('approval_status', 'approved'),
            "registration_completed": user_doc.get('registration_completed', False)
        },
        "requires_profile_completion": not user_doc.get('registration_completed', False)
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    # Note: With JWT, logout is typically handled client-side
    # This endpoint exists for session token cleanup if needed
    return {"message": "Logged out successfully"}
