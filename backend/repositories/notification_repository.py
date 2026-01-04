"""
Notification Repository - Notification data access and metrics
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import logging

from .base import BaseRepository

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository):
    """Repository for notification operations"""
    
    def __init__(self):
        super().__init__("notifications")
        self.logs_collection = self.db["notification_logs"]
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """Get notifications for a user"""
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        return await self.find_many(
            query,
            sort=[("created_at", -1)],
            limit=limit,
            skip=skip
        )
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        return await self.count({"user_id": user_id, "is_read": False})
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        return await self.update_by_id(notification_id, {
            "is_read": True,
            "read_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def mark_all_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        result = await self.collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return result.modified_count
    
    # ==================== NOTIFICATION LOGGING ====================
    
    async def log_notification(
        self,
        notification_type: str,
        channel: str,  # 'whatsapp', 'email', 'in_app'
        recipient: str,
        status: str,  # 'sent', 'failed', 'queued'
        template_name: Optional[str] = None,
        error_message: Optional[str] = None,
        response_data: Optional[Dict] = None
    ) -> str:
        """Log notification send attempt"""
        import uuid
        log_entry = {
            "id": str(uuid.uuid4()),
            "notification_type": notification_type,
            "channel": channel,
            "recipient": recipient,
            "status": status,
            "template_name": template_name,
            "error_message": error_message,
            "response_data": response_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.logs_collection.insert_one(log_entry)
        return log_entry["id"]
    
    async def get_notification_metrics(self, days: int = 7) -> Dict:
        """Get notification success/failure metrics"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff_str}}},
            {"$group": {
                "_id": {"channel": "$channel", "status": "$status"},
                "count": {"$sum": 1}
            }}
        ]
        
        results = await self.logs_collection.aggregate(pipeline).to_list(100)
        
        metrics = {
            "whatsapp": {"sent": 0, "failed": 0, "queued": 0},
            "email": {"sent": 0, "failed": 0, "queued": 0},
            "in_app": {"sent": 0, "failed": 0, "queued": 0}
        }
        
        for r in results:
            channel = r["_id"].get("channel", "unknown")
            status = r["_id"].get("status", "unknown")
            if channel in metrics and status in metrics[channel]:
                metrics[channel][status] = r["count"]
        
        # Calculate success rates
        for channel in metrics:
            total = sum(metrics[channel].values())
            if total > 0:
                metrics[channel]["success_rate"] = round(
                    metrics[channel]["sent"] / total * 100, 1
                )
            else:
                metrics[channel]["success_rate"] = 0
        
        return metrics
    
    async def get_whatsapp_errors(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get recent WhatsApp failures"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return await self.logs_collection.find(
            {
                "channel": "whatsapp",
                "status": "failed",
                "created_at": {"$gte": cutoff_str}
            },
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        result = await self.logs_collection.delete_many(
            {"created_at": {"$lt": cutoff_str}}
        )
        return result.deleted_count


# Singleton instance
_notification_repo = None

def get_notification_repository() -> NotificationRepository:
    global _notification_repo
    if _notification_repo is None:
        _notification_repo = NotificationRepository()
    return _notification_repo
