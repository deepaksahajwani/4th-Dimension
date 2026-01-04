"""
Project Repository - Project data access
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from .base import BaseRepository

logger = logging.getLogger(__name__)


# Slim projection for mobile/list views
PROJECT_SLIM_PROJECTION = {
    "id": 1,
    "title": 1,
    "project_code": 1,
    "client_id": 1,
    "team_leader_id": 1,
    "status": 1,
    "start_date": 1,
    "end_date": 1,
    "created_at": 1
}

# Full projection excludes only internal fields
PROJECT_FULL_PROJECTION = {
    "_id": 0
}


class ProjectRepository(BaseRepository):
    """Repository for project operations"""
    
    def __init__(self):
        super().__init__("projects")
    
    async def get_active_projects(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        slim: bool = False,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """Get active (non-archived, non-deleted) projects"""
        query = {
            "$or": [
                {"archived": False},
                {"archived": {"$exists": False}}
            ],
            "deleted_at": None
        }
        
        # Filter by role
        if role == "client" and user_id:
            query["client_id"] = user_id
        elif role == "team_leader" and user_id:
            query["team_leader_id"] = user_id
        
        projection = PROJECT_SLIM_PROJECTION if slim else PROJECT_FULL_PROJECTION
        
        return await self.find_many(
            query,
            projection=projection,
            sort=[("created_at", -1)],
            limit=limit,
            skip=skip
        )
    
    async def get_project_with_progress(self, project_id: str) -> Optional[Dict]:
        """Get project with calculated progress"""
        project = await self.find_by_id(project_id)
        if not project:
            return None
        
        # Get drawings for progress calculation
        drawings = await self.db.project_drawings.find(
            {"project_id": project_id, "deleted_at": None},
            {"_id": 0, "is_issued": 1, "is_approved": 1, "is_not_applicable": 1}
        ).to_list(500)
        
        total = len(drawings)
        applicable = len([d for d in drawings if not d.get("is_not_applicable")])
        completed = len([d for d in drawings if d.get("is_issued") or d.get("is_approved")])
        
        project["progress"] = {
            "total_drawings": total,
            "applicable_drawings": applicable,
            "completed_drawings": completed,
            "percentage": round((completed / applicable * 100) if applicable > 0 else 0)
        }
        
        return project
    
    async def get_slim_project_card(self, project_id: str) -> Optional[Dict]:
        """Get minimal project data for mobile card view"""
        project = await self.find_by_id(project_id, projection=PROJECT_SLIM_PROJECTION)
        if not project:
            return None
        
        # Add progress percentage
        drawings = await self.db.project_drawings.find(
            {"project_id": project_id, "deleted_at": None, "is_not_applicable": {"$ne": True}},
            {"_id": 0, "is_issued": 1, "is_approved": 1}
        ).to_list(500)
        
        total = len(drawings)
        completed = len([d for d in drawings if d.get("is_issued") or d.get("is_approved")])
        
        project["progress_percent"] = round((completed / total * 100) if total > 0 else 0)
        
        # Get team leader name
        if project.get("team_leader_id"):
            leader = await self.db.users.find_one(
                {"id": project["team_leader_id"]},
                {"_id": 0, "name": 1}
            )
            project["team_leader_name"] = leader.get("name") if leader else None
        
        return project
    
    async def get_projects_for_user(
        self,
        user_id: str,
        role: str,
        slim: bool = True
    ) -> List[Dict]:
        """Get projects accessible to a specific user based on role"""
        if role == "owner":
            return await self.get_active_projects(slim=slim)
        elif role == "team_leader":
            return await self.get_active_projects(user_id=user_id, role="team_leader", slim=slim)
        elif role == "client":
            # Get client ID from clients collection
            client = await self.db.clients.find_one({"email": {"$regex": user_id, "$options": "i"}}, {"_id": 0, "id": 1})
            if client:
                return await self.get_active_projects(user_id=client["id"], role="client", slim=slim)
            return []
        else:
            # Team members see all active projects
            return await self.get_active_projects(slim=slim)
    
    async def get_project_count_by_status(self) -> Dict:
        """Get project counts grouped by status"""
        pipeline = [
            {"$match": {"deleted_at": None}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        results = await self.collection.aggregate(pipeline).to_list(100)
        return {r["_id"]: r["count"] for r in results if r["_id"]}


# Singleton instance
_project_repo = None

def get_project_repository() -> ProjectRepository:
    global _project_repo
    if _project_repo is None:
        _project_repo = ProjectRepository()
    return _project_repo
