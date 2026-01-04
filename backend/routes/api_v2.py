"""
API v2 - Lightweight endpoints optimized for mobile
All responses are slim by default with minimal payload sizes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
import logging

from utils.auth import get_current_user, User
from repositories import (
    get_project_repository,
    get_drawing_repository,
    get_user_repository,
    get_notification_repository
)

router = APIRouter(prefix="/v2", tags=["API v2 - Mobile"])
logger = logging.getLogger(__name__)


# ==================== PROJECT ENDPOINTS ====================

@router.get("/projects")
async def get_projects_slim(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get projects list - SLIM payload for mobile
    Returns: id, title, project_code, progress_percent, team_leader_name
    """
    project_repo = get_project_repository()
    
    projects = await project_repo.get_active_projects(
        user_id=current_user.id,
        role=current_user.role,
        slim=True,
        limit=limit,
        skip=skip
    )
    
    # Enrich with progress and team leader name
    result = []
    for project in projects:
        card = await project_repo.get_slim_project_card(project["id"])
        if card:
            result.append({
                "id": card["id"],
                "title": card.get("title"),
                "project_code": card.get("project_code"),
                "progress_percent": card.get("progress_percent", 0),
                "team_leader_name": card.get("team_leader_name"),
                "status": card.get("status", "active")
            })
    
    return {
        "projects": result,
        "count": len(result),
        "has_more": len(projects) == limit
    }


@router.get("/projects/{project_id}")
async def get_project_slim(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get single project - SLIM payload
    Returns basic info + progress summary (no drawings)
    """
    project_repo = get_project_repository()
    drawing_repo = get_drawing_repository()
    
    project = await project_repo.get_slim_project_card(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Add drawing summary
    summary = await drawing_repo.get_drawings_summary(project_id)
    
    return {
        "id": project["id"],
        "title": project.get("title"),
        "project_code": project.get("project_code"),
        "progress_percent": project.get("progress_percent", 0),
        "team_leader_name": project.get("team_leader_name"),
        "drawings_summary": summary
    }


@router.get("/projects/{project_id}/drawings")
async def get_project_drawings_slim(
    project_id: str,
    current_user: User = Depends(get_current_user),
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(10, le=50),
    skip: int = Query(0, ge=0)
):
    """
    Get drawings for project - PAGINATED & SLIM
    Load 10 at a time by default for mobile performance
    """
    drawing_repo = get_drawing_repository()
    
    drawings = await drawing_repo.get_project_drawings(
        project_id=project_id,
        slim=True,
        category=category,
        status=status,
        limit=limit,
        skip=skip
    )
    
    # Get total count for pagination
    total = await drawing_repo.count({
        "project_id": project_id,
        "deleted_at": None
    })
    
    return {
        "drawings": drawings,
        "count": len(drawings),
        "total": total,
        "has_more": skip + len(drawings) < total,
        "page": skip // limit + 1 if limit > 0 else 1
    }


# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Ultra-light dashboard summary for mobile home screen
    """
    project_repo = get_project_repository()
    drawing_repo = get_drawing_repository()
    notification_repo = get_notification_repository()
    
    # Get project counts
    projects = await project_repo.get_active_projects(
        user_id=current_user.id,
        role=current_user.role,
        slim=True
    )
    
    # Calculate aggregates
    total_projects = len(projects)
    
    # Get pending approvals count
    pending_drawings = await drawing_repo.get_pending_approvals()
    pending_count = len(pending_drawings)
    
    # Get overdue count
    overdue_drawings = await drawing_repo.get_overdue_drawings()
    overdue_count = len(overdue_drawings)
    
    # Get unread notifications
    unread_count = await notification_repo.get_unread_count(current_user.id)
    
    return {
        "total_projects": total_projects,
        "pending_approvals": pending_count,
        "overdue_drawings": overdue_count,
        "unread_notifications": unread_count,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/dashboard/action-items")
async def get_action_items(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, le=20)
):
    """
    Get priority action items for user
    """
    drawing_repo = get_drawing_repository()
    
    items = []
    
    # Get pending approvals (for owner/team_leader)
    if current_user.role in ["owner", "team_leader"] or current_user.is_owner:
        pending = await drawing_repo.get_pending_approvals()
        for d in pending[:5]:
            items.append({
                "type": "approval_needed",
                "drawing_id": d["id"],
                "drawing_name": d.get("name"),
                "category": d.get("category"),
                "priority": "high"
            })
    
    # Get overdue drawings
    overdue = await drawing_repo.get_overdue_drawings()
    for d in overdue[:5]:
        items.append({
            "type": "overdue",
            "drawing_id": d["id"],
            "drawing_name": d.get("name"),
            "due_date": d.get("due_date"),
            "priority": "critical"
        })
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: priority_order.get(x.get("priority"), 99))
    
    return {
        "items": items[:limit],
        "total": len(items)
    }


# ==================== NOTIFICATIONS ====================

@router.get("/notifications")
async def get_notifications_slim(
    current_user: User = Depends(get_current_user),
    unread_only: bool = False,
    limit: int = Query(20, le=50),
    skip: int = Query(0, ge=0)
):
    """
    Get notifications - paginated for mobile
    """
    notification_repo = get_notification_repository()
    
    notifications = await notification_repo.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        skip=skip
    )
    
    unread_count = await notification_repo.get_unread_count(current_user.id)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "has_more": len(notifications) == limit
    }


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    notification_id: Optional[str] = None
):
    """
    Mark notification(s) as read
    If no ID provided, marks all as read
    """
    notification_repo = get_notification_repository()
    
    if notification_id:
        success = await notification_repo.mark_as_read(notification_id)
        return {"success": success, "marked": 1 if success else 0}
    else:
        count = await notification_repo.mark_all_read(current_user.id)
        return {"success": True, "marked": count}


# ==================== TEAM ====================

@router.get("/team")
async def get_team_slim(
    current_user: User = Depends(get_current_user)
):
    """
    Get team members - slim list
    """
    user_repo = get_user_repository()
    
    members = await user_repo.get_team_members(approved_only=True)
    
    return {
        "members": [
            {
                "id": m["id"],
                "name": m.get("name"),
                "role": m.get("role"),
                "mobile": m.get("mobile")
            }
            for m in members
        ],
        "count": len(members)
    }


# ==================== OWNER METRICS ====================

@router.get("/metrics/notifications")
async def get_notification_metrics(
    current_user: User = Depends(get_current_user),
    days: int = Query(7, le=30)
):
    """
    Get notification success/failure metrics (Owner only)
    """
    if not current_user.is_owner and current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    
    notification_repo = get_notification_repository()
    
    metrics = await notification_repo.get_notification_metrics(days=days)
    errors = await notification_repo.get_whatsapp_errors(days=days, limit=10)
    
    return {
        "period_days": days,
        "metrics": metrics,
        "recent_whatsapp_errors": errors
    }
