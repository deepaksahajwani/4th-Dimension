"""
Drawing Repository - Drawing data access
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from .base import BaseRepository

logger = logging.getLogger(__name__)


# Slim projection for list views
DRAWING_SLIM_PROJECTION = {
    "id": 1,
    "name": 1,
    "category": 1,
    "is_issued": 1,
    "is_approved": 1,
    "is_not_applicable": 1,
    "due_date": 1,
    "revision_number": 1,
    "file_url": 1,
    "comment_count": 1
}


class DrawingRepository(BaseRepository):
    """Repository for drawing operations"""
    
    def __init__(self):
        super().__init__("project_drawings")
    
    async def get_project_drawings(
        self,
        project_id: str,
        slim: bool = False,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """Get drawings for a project with optional filters"""
        query = {"project_id": project_id, "deleted_at": None}
        
        if category:
            query["category"] = category
        
        if status:
            if status == "issued":
                query["is_issued"] = True
            elif status == "approved":
                query["is_approved"] = True
                query["is_issued"] = {"$ne": True}
            elif status == "pending":
                query["is_approved"] = {"$ne": True}
                query["is_issued"] = {"$ne": True}
                query["file_url"] = {"$exists": False}
            elif status == "under_review":
                query["is_approved"] = {"$ne": True}
                query["is_issued"] = {"$ne": True}
                query["file_url"] = {"$exists": True}
        
        projection = DRAWING_SLIM_PROJECTION if slim else {"_id": 0}
        
        return await self.find_many(
            query,
            projection=projection,
            sort=[("category", 1), ("name", 1)],
            limit=limit,
            skip=skip
        )
    
    async def get_drawings_summary(self, project_id: str) -> Dict:
        """Get drawing statistics for a project"""
        drawings = await self.find_many(
            {"project_id": project_id, "deleted_at": None},
            projection={"is_issued": 1, "is_approved": 1, "is_not_applicable": 1, "due_date": 1}
        )
        
        total = len(drawings)
        issued = sum(1 for d in drawings if d.get("is_issued"))
        approved = sum(1 for d in drawings if d.get("is_approved") and not d.get("is_issued"))
        not_applicable = sum(1 for d in drawings if d.get("is_not_applicable"))
        pending = total - issued - approved - not_applicable
        
        # Count overdue
        now = datetime.now(timezone.utc)
        overdue = sum(1 for d in drawings if (
            d.get("due_date") and 
            not d.get("is_issued") and 
            not d.get("is_not_applicable") and
            datetime.fromisoformat(d["due_date"].replace("Z", "+00:00")) < now
        ))
        
        applicable = total - not_applicable
        progress = round((issued + approved) / applicable * 100) if applicable > 0 else 0
        
        return {
            "total": total,
            "issued": issued,
            "approved": approved,
            "pending": pending,
            "not_applicable": not_applicable,
            "overdue": overdue,
            "progress_percent": progress
        }
    
    async def get_pending_approvals(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get drawings pending approval"""
        query = {
            "deleted_at": None,
            "file_url": {"$exists": True, "$ne": None},
            "is_approved": {"$ne": True},
            "is_issued": {"$ne": True},
            "is_not_applicable": {"$ne": True}
        }
        
        return await self.find_many(query, projection=DRAWING_SLIM_PROJECTION)
    
    async def get_overdue_drawings(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get overdue drawings"""
        now = datetime.now(timezone.utc).isoformat()
        query = {
            "deleted_at": None,
            "is_issued": {"$ne": True},
            "is_not_applicable": {"$ne": True},
            "due_date": {"$lt": now, "$exists": True}
        }
        
        if project_id:
            query["project_id"] = project_id
        
        return await self.find_many(query, projection=DRAWING_SLIM_PROJECTION)
    
    async def approve_drawing(self, drawing_id: str, approved_by: str) -> bool:
        """Approve a drawing"""
        return await self.update_by_id(drawing_id, {
            "is_approved": True,
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def issue_drawing(self, drawing_id: str, file_url: str, issued_by: str) -> bool:
        """Issue a drawing"""
        return await self.update_by_id(drawing_id, {
            "is_issued": True,
            "file_url": file_url,
            "issued_by": issued_by,
            "issued_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def mark_not_applicable(self, drawing_id: str, marked_by: str, reason: Optional[str] = None) -> bool:
        """Mark drawing as not applicable"""
        return await self.update_by_id(drawing_id, {
            "is_not_applicable": True,
            "na_marked_by": marked_by,
            "na_reason": reason,
            "na_marked_at": datetime.now(timezone.utc).isoformat()
        })


# Singleton instance
_drawing_repo = None

def get_drawing_repository() -> DrawingRepository:
    global _drawing_repo
    if _drawing_repo is None:
        _drawing_repo = DrawingRepository()
    return _drawing_repo
