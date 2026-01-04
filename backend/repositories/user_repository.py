"""
User Repository - User data access
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    def __init__(self):
        super().__init__("users")
    
    async def find_by_email(self, email: str) -> Optional[Dict]:
        """Find user by email"""
        return await self.find_one({"email": email.lower()})
    
    async def find_by_mobile(self, mobile: str) -> Optional[Dict]:
        """Find user by mobile number"""
        # Normalize phone number
        digits = ''.join(filter(str.isdigit, mobile))[-10:]
        return await self.find_one({"mobile": {"$regex": digits}})
    
    async def get_owner(self) -> Optional[Dict]:
        """Get the owner user"""
        return await self.find_one({"is_owner": True})
    
    async def get_team_members(self, approved_only: bool = True) -> List[Dict]:
        """Get team members (excludes external stakeholders)"""
        excluded_roles = ['client', 'contractor', 'consultant', 'vendor']
        query = {"role": {"$nin": excluded_roles}}
        
        if approved_only:
            query["approval_status"] = "approved"
        
        return await self.find_many(
            query,
            projection={"password_hash": 0}
        )
    
    async def get_team_leaders(self) -> List[Dict]:
        """Get all team leaders"""
        return await self.find_many(
            {"role": "team_leader", "approval_status": "approved"},
            projection={"password_hash": 0}
        )
    
    async def get_pending_approvals(self) -> List[Dict]:
        """Get users pending approval"""
        return await self.find_many(
            {"approval_status": "pending", "registration_completed": True},
            projection={"password_hash": 0}
        )
    
    async def approve_user(self, user_id: str) -> bool:
        """Approve a user"""
        return await self.update_by_id(user_id, {
            "approval_status": "approved",
            "is_validated": True,
            "approved_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def get_slim_user(self, user_id: str) -> Optional[Dict]:
        """Get minimal user data for mobile"""
        return await self.find_by_id(user_id, projection={
            "id": 1,
            "name": 1,
            "email": 1,
            "role": 1,
            "mobile": 1
        })


# Singleton instance
_user_repo = None

def get_user_repository() -> UserRepository:
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo
