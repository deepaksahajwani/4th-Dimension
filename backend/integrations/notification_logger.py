"""
Notification Logger

Centralized logging system for all notifications.
Stores notification history in MongoDB for tracking and debugging.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4

logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'archflow')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class NotificationLogger:
    """
    Centralized notification logging service.
    Logs all notification attempts to MongoDB for tracking and debugging.
    """
    
    COLLECTION = 'notification_logs'
    
    @staticmethod
    async def log(
        notification_type: str,
        channel: str,
        recipient: str,
        recipient_id: Optional[str] = None,
        subject: Optional[str] = None,
        message_preview: Optional[str] = None,
        success: bool = False,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        message_sid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a notification attempt.
        
        Args:
            notification_type: Type of notification (e.g., 'drawing_approval', 'user_invite')
            channel: Channel used (e.g., 'whatsapp', 'sms', 'email', 'in_app')
            recipient: Recipient identifier (phone/email)
            recipient_id: User ID if available
            subject: Email subject or notification title
            message_preview: First 200 chars of message
            success: Whether notification was successful
            error_code: Error code if failed
            error_message: Error description if failed
            message_sid: External message ID (e.g., Twilio SID)
            metadata: Additional context data
            
        Returns:
            Log entry ID
        """
        log_id = str(uuid4())
        
        log_entry = {
            "id": log_id,
            "notification_type": notification_type,
            "channel": channel,
            "recipient": recipient,
            "recipient_id": recipient_id,
            "subject": subject,
            "message_preview": message_preview[:200] if message_preview else None,
            "success": success,
            "error_code": error_code,
            "error_message": error_message,
            "message_sid": message_sid,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc)
        }
        
        try:
            await db[NotificationLogger.COLLECTION].insert_one(log_entry)
            logger.debug(f"Notification logged: {notification_type} via {channel} to {recipient}")
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
        
        return log_id
    
    @staticmethod
    async def get_logs(
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50,
        sort_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve notification logs with optional filtering.
        
        Args:
            filters: MongoDB query filters
            skip: Number of records to skip
            limit: Maximum records to return
            sort_desc: Sort by newest first
            
        Returns:
            List of log entries
        """
        query = filters or {}
        sort_order = -1 if sort_desc else 1
        
        try:
            cursor = db[NotificationLogger.COLLECTION].find(
                query,
                {"_id": 0}
            ).sort("timestamp", sort_order).skip(skip).limit(limit)
            
            logs = await cursor.to_list(length=limit)
            return logs
            
        except Exception as e:
            logger.error(f"Failed to retrieve notification logs: {str(e)}")
            return []
    
    @staticmethod
    async def get_failure_summary(
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary of notification failures in the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Summary with failure counts by channel and error type
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            # Get failure counts by channel
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": cutoff},
                        "success": False
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "channel": "$channel",
                            "error_code": "$error_code"
                        },
                        "count": {"$sum": 1},
                        "last_error": {"$last": "$error_message"}
                    }
                }
            ]
            
            cursor = db[NotificationLogger.COLLECTION].aggregate(pipeline)
            results = await cursor.to_list(length=100)
            
            # Get total counts
            total_sent = await db[NotificationLogger.COLLECTION].count_documents(
                {"timestamp": {"$gte": cutoff}}
            )
            total_failed = await db[NotificationLogger.COLLECTION].count_documents(
                {"timestamp": {"$gte": cutoff}, "success": False}
            )
            
            return {
                "period_hours": hours,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "success_rate": round((total_sent - total_failed) / total_sent * 100, 1) if total_sent > 0 else 100,
                "failures_by_channel": results
            }
            
        except Exception as e:
            logger.error(f"Failed to get failure summary: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def get_stats(
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get notification statistics for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Statistics including counts by channel and type
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            # Stats by channel
            channel_pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff}}},
                {
                    "$group": {
                        "_id": "$channel",
                        "total": {"$sum": 1},
                        "success": {"$sum": {"$cond": ["$success", 1, 0]}},
                        "failed": {"$sum": {"$cond": ["$success", 0, 1]}}
                    }
                }
            ]
            
            # Stats by notification type
            type_pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff}}},
                {
                    "$group": {
                        "_id": "$notification_type",
                        "total": {"$sum": 1},
                        "success": {"$sum": {"$cond": ["$success", 1, 0]}}
                    }
                }
            ]
            
            channel_cursor = db[NotificationLogger.COLLECTION].aggregate(channel_pipeline)
            type_cursor = db[NotificationLogger.COLLECTION].aggregate(type_pipeline)
            
            channel_stats = await channel_cursor.to_list(length=20)
            type_stats = await type_cursor.to_list(length=50)
            
            return {
                "period_hours": hours,
                "by_channel": channel_stats,
                "by_type": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {"error": str(e)}


# Singleton instance
notification_logger = NotificationLogger()
