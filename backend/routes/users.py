"""
Users Router - Team Member Management
Refactored from server.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
import random
import string
import uuid

from utils.auth import get_current_user, require_admin, require_owner, User
from utils.database import get_database

db = get_database()
router = APIRouter(tags=["Users"])
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class UpdateTeamMember(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: str
    landmark: Optional[str] = None
    city: str
    state: str
    pin_code: str
    mobile: str
    date_of_birth: str
    date_of_joining: str
    gender: str
    marital_status: str
    role: str
    salary: Optional[float] = None
    writeup: Optional[str] = None
    passions: Optional[str] = None
    contribution: Optional[str] = None


class OTP(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    otp_code: str
    action: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OTPRequest(BaseModel):
    action: str
    target_user_id: Optional[str] = None


class OTPVerify(BaseModel):
    otp_code: str
    action: str
    target_user_id: Optional[str] = None


# ==================== ROUTES ====================


@router.get("/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all team members (excludes clients, contractors, consultants, vendors)"""
    excluded_roles = ['client', 'contractor', 'consultant', 'vendor']
    
    users = await db.users.find(
        {
            "approval_status": "approved",
            "role": {"$nin": excluded_roles}
        }, 
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('date_of_joining') and isinstance(user['date_of_joining'], str):
            user['date_of_joining'] = datetime.fromisoformat(user['date_of_joining'])
    return users


@router.get("/users/pending")
async def get_pending_users(current_user: User = Depends(require_admin)):
    """Get all users pending validation"""
    users = await db.users.find(
        {"is_validated": False, "registration_completed": True}, 
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('date_of_birth') and isinstance(user['date_of_birth'], str):
            user['date_of_birth'] = datetime.fromisoformat(user['date_of_birth'])
    return users


@router.post("/users/{user_id}/validate")
async def validate_user(user_id: str, current_user: User = Depends(require_admin)):
    """Approve a pending user (owner or admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['is_validated']:
        raise HTTPException(status_code=400, detail="User already validated")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_validated": True}}
    )
    
    return {"message": "User validated successfully"}


@router.post("/users/{user_id}/reject")
async def reject_user(user_id: str, current_user: User = Depends(require_admin)):
    """Reject a pending user (owner or admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['is_validated']:
        raise HTTPException(status_code=400, detail="User already validated")
    
    await db.users.delete_one({"id": user_id})
    
    return {"message": "User rejected and removed"}


@router.post("/users/{user_id}/toggle-admin")
async def toggle_admin_rights(user_id: str, current_user: User = Depends(require_owner)):
    """Toggle administrator rights (owner only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get('is_owner'):
        raise HTTPException(status_code=400, detail="Cannot change admin rights for owner")
    
    new_status = not user.get('is_admin', False)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": new_status}}
    )
    
    action = "granted" if new_status else "revoked"
    return {"message": f"Administrator rights {action} successfully", "is_admin": new_status}


@router.post("/users/generate-otp")
async def generate_otp(request: OTPRequest, current_user: User = Depends(require_owner)):
    """Generate OTP for sensitive operations (add/delete team members)"""
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    otp = OTP(
        user_id=current_user.id,
        otp_code=otp_code,
        action=request.action,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    
    otp_dict = otp.model_dump()
    otp_dict['created_at'] = otp_dict['created_at'].isoformat()
    otp_dict['expires_at'] = otp_dict['expires_at'].isoformat()
    
    await db.otps.insert_one(otp_dict)
    
    return {
        "message": "OTP generated successfully",
        "otp_code": otp_code,
        "expires_in": 300
    }


@router.post("/users/verify-otp")
async def verify_otp(request: OTPVerify, current_user: User = Depends(require_owner)):
    """Verify OTP for sensitive operations"""
    otp_doc = await db.otps.find_one({
        "user_id": current_user.id,
        "otp_code": request.otp_code,
        "action": request.action,
        "used": False
    })
    
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    expires_at = datetime.fromisoformat(otp_doc['expires_at']) if isinstance(otp_doc['expires_at'], str) else otp_doc['expires_at']
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    await db.otps.update_one(
        {"id": otp_doc['id']},
        {"$set": {"used": True}}
    )
    
    return {
        "message": "OTP verified successfully",
        "verified": True
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_owner)):
    """HARD DELETE a team member (Owner only) - Complete cleanup for fresh re-registration"""
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_email = user.get('email')
    user_phone = user.get('mobile')
    
    await db.users.delete_one({"id": user_id})
    logger.info(f"Hard deleted user: {user.get('name')}")
    
    await db.user_sessions.delete_many({"user_id": user_id})
    
    if user_email:
        await db.pending_registrations.delete_many({"email": user_email})
        await db.team_verifications.delete_many({"email": user_email})
        await db.invitations.delete_many({"email": user_email})
    
    if user_phone:
        phone_digits = ''.join(filter(str.isdigit, user_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Team member permanently deleted. They can now be invited fresh."}


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UpdateTeamMember, current_user: User = Depends(require_owner)):
    """Update a team member's information (Owner only)"""
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    dob = datetime.fromisoformat(user_data.date_of_birth) if user_data.date_of_birth else None
    doj = datetime.fromisoformat(user_data.date_of_joining) if user_data.date_of_joining else None
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "name": user_data.full_name,
            "address_line_1": user_data.address_line_1,
            "address_line_2": user_data.address_line_2,
            "landmark": user_data.landmark,
            "city": user_data.city,
            "state": user_data.state,
            "pin_code": user_data.pin_code,
            "mobile": user_data.mobile,
            "date_of_birth": dob.isoformat() if dob else None,
            "date_of_joining": doj.isoformat() if doj else None,
            "gender": user_data.gender,
            "marital_status": user_data.marital_status,
            "role": user_data.role,
            "salary": user_data.salary,
            "writeup": user_data.writeup,
            "passions": user_data.passions,
            "contribution": user_data.contribution
        }}
    )
    
    return {"message": "User updated successfully"}
