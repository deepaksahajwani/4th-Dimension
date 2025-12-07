"""
Dashboard & Statistics Routes
"""
from fastapi import APIRouter, Depends
from utils.auth import get_current_user, User
from utils.database import get_database
from datetime import datetime, timezone

db = get_database()
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/team-member-stats")
async def get_team_member_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard stats for team members"""
    # Get due drawings
    due_drawings = await db.project_drawings.find({
        "status": {"$in": ["planned", "in_progress"]},
        "deleted_at": None,
        "due_date": {"$lte": datetime.now(timezone.utc).isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    # Get upcoming drawings
    upcoming_drawings = await db.project_drawings.find({
        "status": {"$in": ["planned", "in_progress"]},
        "deleted_at": None,
        "due_date": {"$gt": datetime.now(timezone.utc).isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    return {
        "due_count": len(due_drawings),
        "upcoming_count": len(upcoming_drawings),
        "due_drawings": due_drawings,
        "upcoming_drawings": upcoming_drawings
    }


@router.get("/owner-stats")
async def get_owner_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard stats for owner"""
    # Count active projects
    active_projects = await db.projects.count_documents({"deleted_at": None})
    
    # Count team members
    team_members = await db.users.count_documents({"role": "team_member"})
    
    # Count clients
    clients = await db.clients.count_documents({"deleted_at": None})
    
    return {
        "active_projects": active_projects,
        "team_members": team_members,
        "clients": clients
    }
