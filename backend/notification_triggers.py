"""
Notification Triggers - Functions that send WhatsApp alerts for various events
These are called from different parts of the application when events occur
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

from whatsapp_service import whatsapp_service, templates

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def check_user_notifications_enabled(user_id: str, notification_type: str) -> bool:
    """
    Check if user has this type of notification enabled in their settings
    
    Args:
        user_id: User ID
        notification_type: Type of notification (e.g., 'notify_task_assigned')
    
    Returns:
        True if notifications enabled, False otherwise
    """
    try:
        settings = await db.whatsapp_settings.find_one({"user_id": user_id}, {"_id": 0})
        
        if not settings:
            # If no settings exist, notifications are enabled by default
            return True
        
        # Check if notifications are enabled globally
        if not settings.get("enabled", True):
            return False
        
        # Check specific notification type
        return settings.get(notification_type, True)
    
    except Exception as e:
        logger.error(f"Error checking notification settings: {str(e)}")
        return True  # Default to enabled if there's an error


async def save_notification_log(
    user_id: Optional[str],
    phone_number: str,
    message_type: str,
    message_body: str,
    project_id: Optional[str],
    result: Dict
):
    """Save notification attempt to database"""
    try:
        log_entry = {
            "user_id": user_id,
            "phone_number": phone_number,
            "message_type": message_type,
            "message_body": message_body,
            "project_id": project_id,
            "twilio_message_sid": result.get("message_sid"),
            "delivery_status": "sent" if result.get("success") else "failed",
            "error_code": result.get("error_code"),
            "error_message": result.get("error"),
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_notifications.insert_one(log_entry)
        logger.info(f"Notification log saved for {message_type} to {phone_number}")
    
    except Exception as e:
        logger.error(f"Error saving notification log: {str(e)}")


async def notify_user_registered(user_data: Dict):
    """
    Notify owner when new user registers
    
    Args:
        user_data: Dict containing user info (name, email, role, etc.)
    """
    try:
        # Get owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if not owner or not owner.get("mobile"):
            logger.warning("Owner not found or no mobile number")
            return
        
        # Check if owner has this notification enabled
        if not await check_user_notifications_enabled(owner["id"], "notify_user_registered"):
            logger.info("Owner has user_registered notifications disabled")
            return
        
        # Generate message
        message = templates.user_registered(
            user_data.get("name", "Unknown"),
            user_data.get("role", "Unknown")
        )
        
        # Send WhatsApp
        result = whatsapp_service.send_message(owner["mobile"], message)
        
        # Log the notification
        await save_notification_log(
            user_id=owner["id"],
            phone_number=owner["mobile"],
            message_type="user_registered",
            message_body=message,
            project_id=None,
            result=result
        )
        
        logger.info(f"User registration notification sent to owner: {result}")
    
    except Exception as e:
        logger.error(f"Error sending user_registered notification: {str(e)}")


async def notify_user_approved(user_id: str):
    """
    Notify user when their account is approved
    
    Args:
        user_id: ID of the approved user
    """
    try:
        # Get user details
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("mobile"):
            logger.warning(f"User {user_id} not found or no mobile number")
            return
        
        # Check if user has this notification enabled
        if not await check_user_notifications_enabled(user_id, "notify_user_registered"):
            logger.info(f"User {user_id} has approval notifications disabled")
            return
        
        # Generate message
        message = templates.user_approved(user.get("name", "User"))
        
        # Send WhatsApp
        result = whatsapp_service.send_message(user["mobile"], message)
        
        # Log the notification
        await save_notification_log(
            user_id=user_id,
            phone_number=user["mobile"],
            message_type="user_approved",
            message_body=message,
            project_id=None,
            result=result
        )
        
        logger.info(f"User approval notification sent to {user['email']}: {result}")
    
    except Exception as e:
        logger.error(f"Error sending user_approved notification: {str(e)}")


async def notify_drawing_uploaded(project_id: str, drawing_name: str, uploaded_by_id: str):
    """
    Notify team members when a drawing is uploaded
    
    Args:
        project_id: Project ID
        drawing_name: Name of the drawing
        uploaded_by_id: User ID of uploader
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get uploader details
        uploader = await db.users.find_one({"id": uploaded_by_id}, {"_id": 0})
        uploader_name = uploader.get("name", "Someone") if uploader else "Someone"
        
        # Get all team members on this project
        team_member_ids = project.get("team_members", [])
        assigned_contractors = project.get("assigned_contractors", [])
        assigned_clients = project.get("assigned_clients", [])
        
        all_user_ids = set(team_member_ids + assigned_contractors + assigned_clients)
        
        # Remove the uploader (don't notify them)
        all_user_ids.discard(uploaded_by_id)
        
        # Generate enhanced message with deep link
        app_url = os.environ.get('FRONTEND_URL', 'https://architect-pm.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""🏗️ NEW DRAWING UPLOADED
        
Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Uploaded by: {uploader_name}

👆 REVIEW NOW: {project_link}

Quick Actions:
✅ Approve | 🔄 Request Revision | 💬 Add Comment

- 4th Dimension Team"""
        
        # Send to all team members
        for user_id in all_user_ids:
            if not await check_user_notifications_enabled(user_id, "notify_drawing_uploaded"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="drawing_uploaded",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Drawing upload notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending drawing_uploaded notification: {str(e)}")


async def notify_new_comment(project_id: str, commenter_id: str, comment_text: str, mentioned_user_ids: List[str] = None):
    """
    Notify users when a new comment is posted
    
    Args:
        project_id: Project ID
        commenter_id: User who posted comment
        comment_text: Comment content
        mentioned_user_ids: List of user IDs mentioned in comment
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        # Get commenter details
        commenter = await db.users.find_one({"id": commenter_id}, {"_id": 0})
        commenter_name = commenter.get("name", "Someone") if commenter else "Someone"
        
        # Generate enhanced comment message with deep link
        app_url = os.environ.get('FRONTEND_URL', 'https://architect-pm.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        # Truncate comment for WhatsApp display
        display_comment = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
        
        message = f"""💬 NEW COMMENT ADDED

Project: {project.get("name", "Unknown Project")}
By: {commenter_name}
Comment: "{display_comment}"

👆 VIEW & RESPOND: {project_link}

Quick Actions:
💬 Reply | ✅ Acknowledge | 🔔 Mark Important

- 4th Dimension Team"""
        
        # Notify mentioned users or all team members
        if mentioned_user_ids:
            recipients = set(mentioned_user_ids)
        else:
            team_member_ids = project.get("team_members", [])
            recipients = set(team_member_ids)
        
        # Remove commenter
        recipients.discard(commenter_id)
        
        # Send notifications
        for user_id in recipients:
            if not await check_user_notifications_enabled(user_id, "notify_new_comment"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="new_comment",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Comment notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending comment notification: {str(e)}")


async def notify_task_assigned(task_id: str, assignee_id: str, project_id: str):
    """
    Notify user when a task is assigned to them
    
    Args:
        task_id: Task ID
        assignee_id: User ID of assignee
        project_id: Project ID
    """
    try:
        # Get task details
        task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        if not task:
            return
        
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        project_name = project.get("name", "Unknown Project") if project else "Unknown Project"
        
        # Check notification settings
        if not await check_user_notifications_enabled(assignee_id, "notify_task_assigned"):
            return
        
        # Get assignee details
        user = await db.users.find_one({"id": assignee_id}, {"_id": 0})
        if not user or not user.get("mobile"):
            return
        
        # Format deadline
        deadline_str = task.get("deadline", "Not set")
        if isinstance(deadline_str, str) and "T" in deadline_str:
            try:
                deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                deadline_str = deadline_dt.strftime("%d %b %Y, %I:%M %p")
            except:
                pass
        
        # Generate enhanced task assignment message with deep link
        app_url = os.environ.get('FRONTEND_URL', 'https://architect-pm.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        # Priority emoji
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "🟡")
        
        message = f"""✅ NEW TASK ASSIGNED

{priority_emoji} Priority: {task.get("priority", "Medium").title()}
Task: {task.get("title", "Unnamed Task")}
Project: {project_name}
Deadline: {deadline_str}

👆 VIEW TASK: {project_link}

Quick Actions:
▶️ Start Work | ❓ Ask Question | ⏰ Update Status

- 4th Dimension Team"""
        
        # Send WhatsApp
        result = whatsapp_service.send_message(user["mobile"], message)
        
        # Log notification
        await save_notification_log(
            user_id=assignee_id,
            phone_number=user["mobile"],
            message_type="task_assigned",
            message_body=message,
            project_id=project_id,
            result=result
        )
        
        logger.info(f"Task assignment notification sent to {user['email']}")
    
    except Exception as e:
        logger.error(f"Error sending task_assigned notification: {str(e)}")


async def notify_milestone_completed(project_id: str, milestone_name: str):
    """
    Notify all project members when a milestone is completed
    
    Args:
        project_id: Project ID
        milestone_name: Name of completed milestone
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        # Generate message
        message = templates.milestone_completed(
            project.get("name", "Unknown Project"),
            milestone_name
        )
        
        # Get all project members
        team_member_ids = project.get("team_members", [])
        assigned_contractors = project.get("assigned_contractors", [])
        assigned_clients = project.get("assigned_clients", [])
        
        all_user_ids = set(team_member_ids + assigned_contractors + assigned_clients)
        
        # Send to all
        for user_id in all_user_ids:
            if not await check_user_notifications_enabled(user_id, "notify_milestone_completed"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="milestone_completed",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Milestone completion notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending milestone notification: {str(e)}")


async def notify_payment_due(project_id: str, amount: float, due_date: str, recipient_ids: List[str]):
    """
    Notify about payment due
    
    Args:
        project_id: Project ID
        amount: Payment amount
        due_date: Due date string
        recipient_ids: List of user IDs to notify
    """
    try:
        # Get project
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        project_name = project.get("name", "Unknown Project") if project else "Unknown Project"
        
        # Generate message
        message = templates.payment_due(project_name, f"{amount:,.2f}", due_date)
        
        # Send to recipients
        for user_id in recipient_ids:
            if not await check_user_notifications_enabled(user_id, "notify_payment"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="payment_due",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info("Payment due notifications sent")
    
    except Exception as e:
        logger.error(f"Error sending payment_due notification: {str(e)}")


async def notify_site_visit_scheduled(project_id: str, visit_date: str, visit_time: str):
    """
    Notify team about scheduled site visit
    
    Args:
        project_id: Project ID
        visit_date: Visit date
        visit_time: Visit time
    """
    try:
        # Get project
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        # Generate message
        message = templates.site_visit_scheduled(
            project.get("name", "Unknown Project"),
            visit_date,
            visit_time
        )
        
        # Get all project members
        team_member_ids = project.get("team_members", [])
        assigned_contractors = project.get("assigned_contractors", [])
        
        all_user_ids = set(team_member_ids + assigned_contractors)
        
        # Send notifications
        for user_id in all_user_ids:
            if not await check_user_notifications_enabled(user_id, "notify_site_visit"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="site_visit_scheduled",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Site visit notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending site_visit notification: {str(e)}")


# Export all notification functions
__all__ = [
    'notify_user_registered',
    'notify_user_approved',
    'notify_drawing_uploaded',
    'notify_new_comment',
    'notify_task_assigned',
    'notify_milestone_completed',
    'notify_payment_due',
    'notify_site_visit_scheduled'
]
