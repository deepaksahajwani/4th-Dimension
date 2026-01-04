"""
Monitoring & Metrics Router - Phase 5 Owner Dashboard
Provides system health, notification stats, API performance, and usage metrics
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

from utils.auth import get_current_user, User
from utils.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Get DB reference
db = get_database()


@router.get("/system-health")
async def get_system_health(current_user: User = Depends(get_current_user)):
    """Get overall system health metrics (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        # Get counts from various collections
        total_users = await db.users.count_documents({"deleted_at": None})
        total_projects = await db.projects.count_documents({"deleted_at": None})
        active_projects = await db.projects.count_documents({"deleted_at": None, "archived": {"$ne": True}})
        total_drawings = await db.project_drawings.count_documents({"deleted_at": None})
        issued_drawings = await db.project_drawings.count_documents({"deleted_at": None, "is_issued": True})
        
        # Calculate drawing completion rate
        completion_rate = round((issued_drawings / total_drawings * 100) if total_drawings > 0 else 0, 1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "users": {
                "total": total_users,
                "active": total_users  # TODO: Track active users
            },
            "projects": {
                "total": total_projects,
                "active": active_projects,
                "archived": total_projects - active_projects
            },
            "drawings": {
                "total": total_drawings,
                "issued": issued_drawings,
                "completion_rate": completion_rate
            }
        }
    except Exception as e:
        logger.error(f"System health check error: {e}")
        return {"status": "degraded", "error": str(e)}


@router.get("/notifications")
async def get_notification_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get notification delivery metrics (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        # Total notifications in period
        total = await db.whatsapp_notifications.count_documents({
            "created_at": {"$gte": cutoff_str}
        })
        
        # By delivery status
        sent = await db.whatsapp_notifications.count_documents({
            "created_at": {"$gte": cutoff_str},
            "delivery_status": "sent"
        })
        delivered = await db.whatsapp_notifications.count_documents({
            "created_at": {"$gte": cutoff_str},
            "delivery_status": "delivered"
        })
        failed = await db.whatsapp_notifications.count_documents({
            "created_at": {"$gte": cutoff_str},
            "delivery_status": "failed"
        })
        pending = await db.whatsapp_notifications.count_documents({
            "created_at": {"$gte": cutoff_str},
            "delivery_status": {"$in": ["pending", "queued"]}
        })
        
        # Calculate success rate
        completed = sent + delivered
        success_rate = round((completed / total * 100) if total > 0 else 100, 1)
        
        # Get failure reasons
        failure_pipeline = [
            {"$match": {"delivery_status": "failed", "created_at": {"$gte": cutoff_str}}},
            {"$group": {"_id": "$error_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        failure_reasons = await db.whatsapp_notifications.aggregate(failure_pipeline).to_list(10)
        
        # Daily breakdown
        daily_pipeline = [
            {"$match": {"created_at": {"$gte": cutoff_str}}},
            {"$addFields": {
                "date": {"$substr": ["$created_at", 0, 10]}
            }},
            {"$group": {
                "_id": "$date",
                "total": {"$sum": 1},
                "success": {"$sum": {"$cond": [{"$in": ["$delivery_status", ["sent", "delivered"]]}, 1, 0]}},
                "failed": {"$sum": {"$cond": [{"$eq": ["$delivery_status", "failed"]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_stats = await db.whatsapp_notifications.aggregate(daily_pipeline).to_list(30)
        
        return {
            "period_days": days,
            "summary": {
                "total": total,
                "sent": sent,
                "delivered": delivered,
                "failed": failed,
                "pending": pending,
                "success_rate": success_rate
            },
            "failure_reasons": [
                {"reason": r["_id"] or "Unknown", "count": r["count"]}
                for r in failure_reasons
            ],
            "daily_breakdown": daily_stats
        }
    except Exception as e:
        logger.error(f"Notification metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def get_storage_metrics(current_user: User = Depends(get_current_user)):
    """Get storage usage metrics (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        import os
        from pathlib import Path
        
        upload_dir = Path("/app/uploads")
        
        def get_dir_size(path: Path) -> int:
            total = 0
            if path.exists():
                for entry in path.rglob("*"):
                    if entry.is_file():
                        total += entry.stat().st_size
            return total
        
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        
        # Get sizes for each upload type
        drawings_size = get_dir_size(upload_dir / "drawings")
        images_3d_size = get_dir_size(upload_dir / "3d_images")
        voice_notes_size = get_dir_size(upload_dir / "voice_notes")
        comments_size = get_dir_size(upload_dir / "comments")
        thumbnails_size = get_dir_size(upload_dir / "thumbnails")
        total_size = get_dir_size(upload_dir)
        
        # Count files
        def count_files(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(1 for _ in path.rglob("*") if _.is_file())
        
        return {
            "total": {
                "bytes": total_size,
                "formatted": format_size(total_size),
                "file_count": count_files(upload_dir)
            },
            "breakdown": {
                "drawings": {
                    "bytes": drawings_size,
                    "formatted": format_size(drawings_size),
                    "file_count": count_files(upload_dir / "drawings")
                },
                "3d_images": {
                    "bytes": images_3d_size,
                    "formatted": format_size(images_3d_size),
                    "file_count": count_files(upload_dir / "3d_images")
                },
                "voice_notes": {
                    "bytes": voice_notes_size,
                    "formatted": format_size(voice_notes_size),
                    "file_count": count_files(upload_dir / "voice_notes")
                },
                "comments": {
                    "bytes": comments_size,
                    "formatted": format_size(comments_size),
                    "file_count": count_files(upload_dir / "comments")
                },
                "thumbnails": {
                    "bytes": thumbnails_size,
                    "formatted": format_size(thumbnails_size),
                    "file_count": count_files(upload_dir / "thumbnails")
                }
            }
        }
    except Exception as e:
        logger.error(f"Storage metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-usage")
async def get_api_usage_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get API usage statistics (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        # Get login count
        login_count = await db.user_sessions.count_documents({
            "created_at": {"$gte": cutoff_str}
        }) if "user_sessions" in await db.list_collection_names() else 0
        
        # Get active users (users who logged in)
        active_users_pipeline = [
            {"$match": {"last_login": {"$gte": cutoff_str}}},
            {"$count": "count"}
        ]
        active_result = await db.users.aggregate(active_users_pipeline).to_list(1)
        active_users = active_result[0]["count"] if active_result else 0
        
        # Get project activity
        projects_created = await db.projects.count_documents({
            "created_at": {"$gte": cutoff_str}
        })
        
        drawings_uploaded = await db.project_drawings.count_documents({
            "created_at": {"$gte": cutoff_str}
        })
        
        comments_created = await db.project_comments.count_documents({
            "created_at": {"$gte": cutoff_str}
        }) + await db.drawing_comments.count_documents({
            "created_at": {"$gte": cutoff_str}
        })
        
        return {
            "period_days": days,
            "users": {
                "active": active_users,
                "logins": login_count
            },
            "activity": {
                "projects_created": projects_created,
                "drawings_uploaded": drawings_uploaded,
                "comments_created": comments_created
            }
        }
    except Exception as e:
        logger.error(f"API usage metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_metrics_overview(current_user: User = Depends(get_current_user)):
    """Get comprehensive metrics overview for Owner Dashboard (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    try:
        # Combine all metrics into one response
        health = await get_system_health(current_user)
        notifications = await get_notification_metrics(days=7, current_user=current_user)
        storage = await get_storage_metrics(current_user)
        api_usage = await get_api_usage_metrics(days=7, current_user=current_user)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_health": health,
            "notifications": notifications,
            "storage": storage,
            "api_usage": api_usage
        }
    except Exception as e:
        logger.error(f"Metrics overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
