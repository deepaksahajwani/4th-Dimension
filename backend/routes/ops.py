"""
Operational API Routes

Provides endpoints for:
- System health checks
- Service status monitoring
- Notification logs and debugging
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.security import HTTPBearer

from integrations.twilio_service import twilio_service
from integrations.sendgrid_service import sendgrid_service
from integrations.notification_logger import notification_logger

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/ops", tags=["Operations"])


# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "4th-dimension-backend"
    }


@router.get("/status")
async def system_status():
    """
    Comprehensive system status check.
    Returns status of all integrated services.
    """
    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "twilio": twilio_service.get_status(),
            "sendgrid": sendgrid_service.get_status(),
            "database": {
                "service": "mongodb",
                "configured": bool(os.environ.get('MONGO_URL')),
                "database": os.environ.get('DB_NAME', 'archflow')
            }
        },
        "environment": {
            "node": os.environ.get('NODE_NAME', 'unknown'),
            "version": "2.0.0"
        }
    }


@router.get("/status/integrations")
async def integration_status():
    """
    Get detailed status of all third-party integrations.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrations": {
            "twilio": {
                **twilio_service.get_status(),
                "features": {
                    "whatsapp": bool(twilio_service.whatsapp_from),
                    "sms": bool(twilio_service.sms_from)
                }
            },
            "sendgrid": {
                **sendgrid_service.get_status()
            }
        }
    }


# ============================================
# NOTIFICATION LOGS ENDPOINTS
# ============================================

@router.get("/logs/notifications")
async def get_notification_logs(
    channel: Optional[str] = Query(None, description="Filter by channel (whatsapp, sms, email, in_app)"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    recipient: Optional[str] = Query(None, description="Filter by recipient"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get notification logs with optional filtering.
    
    Supports filtering by:
    - channel: whatsapp, sms, email, in_app
    - notification_type: drawing_approval, user_invite, etc.
    - success: true/false
    - recipient: phone or email
    """
    filters = {}
    
    if channel:
        filters["channel"] = channel
    if notification_type:
        filters["notification_type"] = notification_type
    if success is not None:
        filters["success"] = success
    if recipient:
        filters["recipient"] = {"$regex": recipient, "$options": "i"}
    
    logs = await notification_logger.get_logs(
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    return {
        "total": len(logs),
        "skip": skip,
        "limit": limit,
        "logs": logs
    }


@router.get("/logs/notifications/failures")
async def get_notification_failures(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """
    Get summary of notification failures.
    
    Returns failure counts grouped by channel and error type.
    Useful for debugging WhatsApp/SMS delivery issues.
    """
    summary = await notification_logger.get_failure_summary(hours=hours)
    return summary


@router.get("/logs/notifications/stats")
async def get_notification_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """
    Get notification statistics.
    
    Returns success/failure rates by channel and notification type.
    """
    stats = await notification_logger.get_stats(hours=hours)
    return stats


@router.get("/logs/notifications/{log_id}")
async def get_notification_log_detail(log_id: str):
    """
    Get details of a specific notification log entry.
    """
    logs = await notification_logger.get_logs(
        filters={"id": log_id},
        limit=1
    )
    
    if not logs:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    return logs[0]


# ============================================
# WHATSAPP SPECIFIC ENDPOINTS
# ============================================

@router.get("/logs/whatsapp")
async def get_whatsapp_logs(
    success: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get WhatsApp-specific notification logs.
    
    Shows all WhatsApp message attempts with delivery status.
    """
    filters = {"channel": {"$in": ["whatsapp", "whatsapp_template"]}}
    
    if success is not None:
        filters["success"] = success
    
    logs = await notification_logger.get_logs(
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    # Enhance with error explanations
    for log in logs:
        if not log.get("success") and log.get("error_code"):
            log["error_explanation"] = twilio_service._get_friendly_error(
                int(log["error_code"]) if log["error_code"].isdigit() else 0,
                log.get("error_message", "")
            )
    
    return {
        "total": len(logs),
        "logs": logs
    }


@router.get("/logs/whatsapp/failures")
async def get_whatsapp_failures(
    hours: int = Query(24, ge=1, le=168)
):
    """
    Get WhatsApp failure analysis.
    
    Returns detailed breakdown of WhatsApp failures with:
    - Error codes and their meanings
    - Affected recipients
    - Failure timestamps
    """
    from datetime import timedelta
    from integrations.notification_logger import db
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Get failures with error details
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": cutoff},
                "channel": {"$in": ["whatsapp", "whatsapp_template"]},
                "success": False
            }
        },
        {
            "$group": {
                "_id": "$error_code",
                "count": {"$sum": 1},
                "error_message": {"$first": "$error_message"},
                "affected_recipients": {"$addToSet": "$recipient"},
                "last_occurrence": {"$max": "$timestamp"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    cursor = db.notification_logs.aggregate(pipeline)
    results = await cursor.to_list(length=50)
    
    # Add friendly error explanations
    for result in results:
        error_code = result["_id"]
        if error_code and str(error_code).isdigit():
            result["error_explanation"] = twilio_service._get_friendly_error(
                int(error_code),
                result.get("error_message", "")
            )
        result["affected_count"] = len(result.get("affected_recipients", []))
    
    return {
        "period_hours": hours,
        "failures": results
    }
