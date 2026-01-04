"""
Notification Routes
"""
from fastapi import APIRouter, Depends
from utils.auth import get_current_user, User
from utils.database import get_database

db = get_database()
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Get user notifications"""
    notifications = await db.notifications.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    return notifications


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        return {"message": "Notification not found or already read"}
    
    return {"message": "Notification marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    result = await db.notifications.delete_one({
        "id": notification_id,
        "user_id": current_user.id
    })
    
    if result.deleted_count == 0:
        return {"message": "Notification not found"}
    
    return {"message": "Notification deleted"}
