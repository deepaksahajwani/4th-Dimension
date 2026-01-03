"""
Aggregated APIs for Dashboard and Project Views
Reduces multiple API calls to single aggregated endpoints
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from motor.motor_asyncio import AsyncIOMotorClient
import jwt

logger = logging.getLogger(__name__)

# Create router
aggregated_router = APIRouter(prefix="/api/aggregated", tags=["aggregated"])

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")


async def get_current_user_from_token(authorization: str = Header(None)):
    """Extract and verify user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_identifier = payload.get("sub") or payload.get("user_id")
        
        if not user_identifier:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database - try by ID first, then by email
        user = await db.users.find_one({"id": user_identifier}, {"_id": 0})
        if not user:
            # Try by email (JWT sub is email in this app)
            user = await db.users.find_one({"email": user_identifier}, {"_id": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@aggregated_router.get("/team-leader-dashboard")
async def get_team_leader_dashboard(user: dict = Depends(get_current_user_from_token)):
    """
    Aggregated API for Team Leader Dashboard.
    Returns all data needed in a single call:
    - Projects assigned to the user
    - Drawing stats per project
    - Recent comments
    - Pending actions summary
    """
    user_id = user.get('id')
    user_name = user.get('name')
    user_role = user.get('role')
    
    # Get projects where user is team leader
    projects = await db.projects.find(
        {"team_leader_id": user_id, "deleted_at": None},
        {"_id": 0}
    ).to_list(100)
    
    # Aggregate drawing stats for each project
    projects_with_stats = []
    total_revisions = 0
    total_pending_approval = 0
    total_ready_to_issue = 0
    total_new_comments = 0
    
    for project in projects:
        # Get drawings for this project
        drawings = await db.project_drawings.find(
            {"project_id": project['id'], "deleted_at": None},
            {"_id": 0}
        ).to_list(500)
        
        # Calculate stats
        total_drawings = len(drawings)
        issued = len([d for d in drawings if d.get('is_issued')])
        revisions = len([d for d in drawings if d.get('has_pending_revision')])
        pending_approval = len([d for d in drawings if d.get('under_review') and not d.get('is_approved') and not d.get('has_pending_revision')])
        ready_to_issue = len([d for d in drawings if d.get('is_approved') and not d.get('is_issued')])
        
        # Get recent comments (last 24h)
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_comments = await db.comments.count_documents({
            "project_id": project['id'],
            "created_at": {"$gte": yesterday.isoformat()},
            "user_id": {"$ne": user_id}
        })
        
        # Update totals
        total_revisions += revisions
        total_pending_approval += pending_approval
        total_ready_to_issue += ready_to_issue
        total_new_comments += recent_comments
        
        project_data = {
            **project,
            "stats": {
                "total_drawings": total_drawings,
                "issued": issued,
                "revisions_needed": revisions,
                "pending_approval": pending_approval,
                "ready_to_issue": ready_to_issue,
                "new_comments": recent_comments,
                "percent_complete": round((issued / total_drawings * 100) if total_drawings > 0 else 0)
            }
        }
        projects_with_stats.append(project_data)
    
    # Sort by urgency
    projects_with_stats.sort(
        key=lambda p: (
            p['stats']['revisions_needed'] * 3 + 
            p['stats']['pending_approval'] * 2 + 
            p['stats']['ready_to_issue']
        ),
        reverse=True
    )
    
    return {
        "user": {
            "id": user_id,
            "name": user_name,
            "role": user_role
        },
        "summary": {
            "total_projects": len(projects),
            "total_revisions_needed": total_revisions,
            "total_pending_approval": total_pending_approval,
            "total_ready_to_issue": total_ready_to_issue,
            "total_new_comments": total_new_comments
        },
        "projects": projects_with_stats
    }


@aggregated_router.get("/project/{project_id}/full")
async def get_project_full(project_id: str, user: dict = Depends(get_current_user_from_token)):
    """
    Aggregated API for Project Detail View.
    Returns all project data in a single call:
    - Project details
    - All drawings with status
    - 3D images grouped by category
    - Recent comments
    - Client info
    - Team leader info
    """
    # Get project
    project = await db.projects.find_one(
        {"id": project_id, "deleted_at": None},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get drawings grouped by status
    drawings = await db.project_drawings.find(
        {"project_id": project_id, "deleted_at": None},
        {"_id": 0}
    ).to_list(500)
    
    # Categorize drawings
    drawings_by_status = {
        "revisions_needed": [d for d in drawings if d.get('has_pending_revision')],
        "pending_approval": [d for d in drawings if d.get('under_review') and not d.get('is_approved') and not d.get('has_pending_revision')],
        "ready_to_issue": [d for d in drawings if d.get('is_approved') and not d.get('is_issued')],
        "issued": [d for d in drawings if d.get('is_issued') and not d.get('has_pending_revision')],
        "not_started": [d for d in drawings if not d.get('file_url') and not d.get('is_issued') and not d.get('has_pending_revision') and not d.get('under_review')]
    }
    
    # Get 3D images grouped by category
    images_3d = await db.project_3d_images.find(
        {"project_id": project_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    images_by_category = {}
    for img in images_3d:
        category = img.get('category', 'Other')
        if category not in images_by_category:
            images_by_category[category] = []
        images_by_category[category].append(img)
    
    images_3d_grouped = [
        {"category": cat, "images": imgs, "count": len(imgs)}
        for cat, imgs in images_by_category.items()
    ]
    
    # Get recent comments (last 50)
    comments = await db.comments.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Get client info
    client_info = None
    if project.get('client_id'):
        client_info = await db.clients.find_one(
            {"id": project['client_id']},
            {"_id": 0, "name": 1, "email": 1, "phone": 1, "mobile": 1}
        )
        if not client_info:
            client_info = await db.users.find_one(
                {"id": project['client_id']},
                {"_id": 0, "name": 1, "email": 1, "phone": 1, "mobile": 1}
            )
    
    # Get team leader info
    team_leader = None
    if project.get('team_leader_id'):
        team_leader = await db.users.find_one(
            {"id": project['team_leader_id']},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1, "role": 1}
        )
    
    # Calculate stats
    total_drawings = len(drawings)
    issued_count = len(drawings_by_status['issued'])
    
    return {
        "project": {
            **project,
            "team_leader": team_leader,
            "client": client_info
        },
        "stats": {
            "total_drawings": total_drawings,
            "issued": issued_count,
            "percent_complete": round((issued_count / total_drawings * 100) if total_drawings > 0 else 0),
            "revisions_needed": len(drawings_by_status['revisions_needed']),
            "pending_approval": len(drawings_by_status['pending_approval']),
            "ready_to_issue": len(drawings_by_status['ready_to_issue']),
            "not_started": len(drawings_by_status['not_started'])
        },
        "drawings": drawings_by_status,
        "images_3d": {
            "total": len(images_3d),
            "categories": images_3d_grouped
        },
        "comments": comments
    }


@aggregated_router.get("/my-work")
async def get_my_work(user: dict = Depends(get_current_user_from_token)):
    """
    Aggregated API for My Work page.
    Returns all actionable items across projects.
    """
    user_id = user.get('id')
    
    # Get projects where user is team leader
    projects = await db.projects.find(
        {"team_leader_id": user_id, "deleted_at": None},
        {"_id": 0}
    ).to_list(100)
    
    action_items = []
    
    for project in projects:
        # Get actionable drawings
        drawings = await db.project_drawings.find(
            {"project_id": project['id'], "deleted_at": None},
            {"_id": 0}
        ).to_list(500)
        
        revisions = [d for d in drawings if d.get('has_pending_revision')]
        pending_approval = [d for d in drawings if d.get('under_review') and not d.get('is_approved') and not d.get('has_pending_revision')]
        ready_to_issue = [d for d in drawings if d.get('is_approved') and not d.get('is_issued')]
        
        # Get recent comments
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_comments = await db.comments.find(
            {
                "project_id": project['id'],
                "created_at": {"$gte": yesterday.isoformat()},
                "user_id": {"$ne": user_id}
            },
            {"_id": 0}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        if revisions or pending_approval or ready_to_issue or recent_comments:
            action_items.append({
                "project": {
                    "id": project['id'],
                    "title": project.get('title'),
                    "code": project.get('code')
                },
                "revisions_needed": revisions,
                "pending_approval": pending_approval,
                "ready_to_issue": ready_to_issue,
                "recent_comments": recent_comments,
                "total_actions": len(revisions) + len(pending_approval) + len(ready_to_issue) + len(recent_comments)
            })
    
    # Sort by total actions
    action_items.sort(key=lambda x: x['total_actions'], reverse=True)
    
    return {
        "user_id": user_id,
        "total_projects": len(projects),
        "total_actions": sum(item['total_actions'] for item in action_items),
        "action_items": action_items
    }


@aggregated_router.get("/logs")
async def get_paginated_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    log_type: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user_from_token)
):
    """
    Paginated logs API for better performance.
    """
    is_owner = user.get('is_owner', False)
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    # Build query
    query = {}
    if log_type:
        query["type"] = log_type
    if status:
        query["status"] = status
    
    # Get total count
    total = await db.notification_logs.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    logs = await db.notification_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "logs": logs
    }


@aggregated_router.get("/cache-stats")
async def get_cache_stats(user: dict = Depends(get_current_user_from_token)):
    """Get cache statistics (Owner only)"""
    if not user.get('is_owner', False):
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        from cache_service import cache
        return {
            "cache_stats": cache.stats(),
            "async_notifications_enabled": True
        }
    except ImportError:
        return {
            "cache_stats": None,
            "async_notifications_enabled": False
        }


# Dummy function for compatibility
def set_auth_dependency(auth_func):
    """Legacy function - no longer needed with Header-based auth"""
    pass
