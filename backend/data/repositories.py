"""
Data Repositories

Dedicated data access layer for MongoDB operations.
Provides clean, reusable methods for common database queries.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'archflow')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class BaseRepository:
    """Base class for all repositories with common operations."""
    
    collection_name: str = None
    
    @classmethod
    async def find_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Find a document by ID."""
        return await db[cls.collection_name].find_one({"id": id}, {"_id": 0})
    
    @classmethod
    async def find_one(cls, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        return await db[cls.collection_name].find_one(query, {"_id": 0})
    
    @classmethod
    async def find_many(
        cls,
        query: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query."""
        cursor = db[cls.collection_name].find(query or {}, {"_id": 0})
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    @classmethod
    async def count(cls, query: Dict[str, Any] = None) -> int:
        """Count documents matching the query."""
        return await db[cls.collection_name].count_documents(query or {})
    
    @classmethod
    async def insert(cls, document: Dict[str, Any]) -> str:
        """Insert a new document."""
        document["created_at"] = datetime.now(timezone.utc).isoformat()
        await db[cls.collection_name].insert_one(document)
        return document.get("id")
    
    @classmethod
    async def update(
        cls,
        id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a document by ID."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await db[cls.collection_name].update_one(
            {"id": id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    @classmethod
    async def delete(cls, id: str) -> bool:
        """Delete a document by ID."""
        result = await db[cls.collection_name].delete_one({"id": id})
        return result.deleted_count > 0


class UserRepository(BaseRepository):
    """Repository for user-related database operations."""
    
    collection_name = "users"
    
    @classmethod
    async def find_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email."""
        return await db[cls.collection_name].find_one(
            {"email": email.lower()},
            {"_id": 0}
        )
    
    @classmethod
    async def find_by_phone(cls, phone: str) -> Optional[Dict[str, Any]]:
        """Find a user by phone number."""
        return await db[cls.collection_name].find_one(
            {"mobile": phone},
            {"_id": 0}
        )
    
    @classmethod
    async def get_owner(cls) -> Optional[Dict[str, Any]]:
        """Get the owner user."""
        return await db[cls.collection_name].find_one(
            {"is_owner": True},
            {"_id": 0}
        )
    
    @classmethod
    async def get_team_members(
        cls,
        include_owner: bool = False,
        approved_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all team members."""
        query = {}
        
        if not include_owner:
            query["is_owner"] = {"$ne": True}
        
        if approved_only:
            query["approval_status"] = "approved"
        
        return await db[cls.collection_name].find(
            query,
            {"_id": 0, "password_hash": 0}
        ).to_list(1000)
    
    @classmethod
    async def get_pending_approvals(cls) -> List[Dict[str, Any]]:
        """Get users pending approval."""
        return await db[cls.collection_name].find(
            {"approval_status": "pending"},
            {"_id": 0, "password_hash": 0}
        ).to_list(100)


class ProjectRepository(BaseRepository):
    """Repository for project-related database operations."""
    
    collection_name = "projects"
    
    @classmethod
    async def get_user_projects(
        cls,
        user_id: str,
        user_role: str,
        is_owner: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get projects accessible to a user based on their role.
        
        Args:
            user_id: The user's ID
            user_role: The user's role (owner, client, contractor, etc.)
            is_owner: Whether user is the owner
            
        Returns:
            List of projects the user can access
        """
        if is_owner:
            # Owner sees all projects
            return await db[cls.collection_name].find(
                {"archived": {"$ne": True}},
                {"_id": 0}
            ).to_list(1000)
        
        elif user_role == 'client':
            # Client sees only their projects
            return await db[cls.collection_name].find(
                {
                    "client_id": user_id,
                    "archived": {"$ne": True}
                },
                {"_id": 0}
            ).to_list(100)
        
        elif user_role == 'team_leader':
            # Team leader sees assigned projects + shared projects
            return await db[cls.collection_name].find(
                {
                    "$or": [
                        {"team_leader_id": user_id},
                        {f"shared_with.{user_id}": {"$exists": True}}
                    ],
                    "archived": {"$ne": True}
                },
                {"_id": 0}
            ).to_list(100)
        
        elif user_role in ['contractor', 'consultant']:
            # Contractors/consultants see projects they're assigned to
            return await db[cls.collection_name].find(
                {
                    "$or": [
                        {"assigned_contractors": {"$regex": user_id}},
                        {"assigned_consultants": {"$regex": user_id}}
                    ],
                    "archived": {"$ne": True}
                },
                {"_id": 0}
            ).to_list(100)
        
        else:
            # Team member sees all non-archived projects
            return await db[cls.collection_name].find(
                {"archived": {"$ne": True}},
                {"_id": 0}
            ).to_list(1000)
    
    @classmethod
    async def get_project_team(cls, project_id: str) -> Dict[str, Any]:
        """
        Get all team members assigned to a project.
        
        Returns:
            Dict with contractors, consultants, and co_clients lists
        """
        project = await cls.find_by_id(project_id)
        if not project:
            return {"contractors": [], "consultants": [], "co_clients": []}
        
        result = {"contractors": [], "consultants": [], "co_clients": []}
        
        # Get assigned contractors
        if project.get("assigned_contractors"):
            for contractor_type, contractor_id in project["assigned_contractors"].items():
                if contractor_id:
                    contractor = await db.contractors.find_one(
                        {"id": contractor_id},
                        {"_id": 0}
                    )
                    if contractor:
                        result["contractors"].append(contractor)
        
        # Get assigned consultants
        if project.get("assigned_consultants"):
            for consultant_id in project["assigned_consultants"]:
                consultant = await db.consultants.find_one(
                    {"id": consultant_id},
                    {"_id": 0}
                )
                if consultant:
                    result["consultants"].append(consultant)
        
        return result


class NotificationRepository(BaseRepository):
    """Repository for notification-related database operations."""
    
    collection_name = "notifications"
    
    @classmethod
    async def get_user_notifications(
        cls,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user."""
        query = {"user_id": user_id}
        
        if unread_only:
            query["read"] = False
        
        return await db[cls.collection_name].find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
    
    @classmethod
    async def mark_as_read(cls, notification_id: str) -> bool:
        """Mark a notification as read."""
        result = await db[cls.collection_name].update_one(
            {"id": notification_id},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    @classmethod
    async def mark_all_read(cls, user_id: str) -> int:
        """Mark all notifications for a user as read."""
        result = await db[cls.collection_name].update_many(
            {"user_id": user_id, "read": False},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count
    
    @classmethod
    async def get_unread_count(cls, user_id: str) -> int:
        """Get count of unread notifications."""
        return await db[cls.collection_name].count_documents(
            {"user_id": user_id, "read": False}
        )


class DrawingRepository(BaseRepository):
    """Repository for drawing-related database operations."""
    
    collection_name = "project_drawings"
    
    @classmethod
    async def get_project_drawings(
        cls,
        project_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all drawings for a project."""
        query = {"project_id": project_id}
        
        if category:
            query["category"] = category
        
        return await db[cls.collection_name].find(
            query,
            {"_id": 0}
        ).sort("sort_order", 1).to_list(500)
    
    @classmethod
    async def get_pending_approvals(
        cls,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get drawings pending approval."""
        query = {
            "under_review": True,
            "is_approved": {"$ne": True}
        }
        
        if project_id:
            query["project_id"] = project_id
        
        return await db[cls.collection_name].find(
            query,
            {"_id": 0}
        ).to_list(100)
    
    @classmethod
    async def get_issued_drawings(
        cls,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Get all issued drawings for a project."""
        return await db[cls.collection_name].find(
            {
                "project_id": project_id,
                "is_issued": True
            },
            {"_id": 0}
        ).to_list(500)
