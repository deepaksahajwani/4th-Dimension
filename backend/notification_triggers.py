"""
Notification Triggers - Functions that send WhatsApp alerts for various events
These are called from different parts of the application when events occur
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Import WhatsApp service - will be initialized after .env loads
from whatsapp_service import whatsapp_service, templates

logger = logging.getLogger(__name__)

# Database connection
def get_db():
    """Get database connection"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

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
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""🏗️ NEW DRAWING UPLOADED

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Uploaded by: {uploader_name}

👆 REVIEW NOW: {project_link}

Next Actions:
💬 Add Comment | 🔄 Request Revision | ✅ Approve for Issue

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
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
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
            except Exception:
                pass
        
        # Generate enhanced task assignment message with deep link
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
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


 
async def notify_voice_note_added(project_id: str, drawing_name: str, commenter_id: str, comment_id: str):
    """
    Notify team members when a voice note is added to a comment
    
    Args:
        project_id: Project ID
        drawing_name: Name of the drawing
        commenter_id: User ID who added the voice note
        comment_id: Comment ID
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get commenter details
        commenter = await db.users.find_one({"id": commenter_id}, {"_id": 0})
        commenter_name = commenter.get("name", "Someone") if commenter else "Someone"
        
        # Get all team members on this project
        team_member_ids = project.get("team_members", [])
        assigned_contractors = project.get("assigned_contractors", [])
        assigned_clients = project.get("assigned_clients", [])
        
        all_user_ids = set(team_member_ids + assigned_contractors + assigned_clients)
        
        # Remove the commenter (don't notify them)
        all_user_ids.discard(commenter_id)
        
        # Generate enhanced message with deep link
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""🎤 VOICE NOTE ADDED
        
Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Voice Note by: {commenter_name}

👆 LISTEN NOW: {project_link}

Quick Actions:
🎧 Play Voice Note | 💬 Reply | ✅ Acknowledge

- 4th Dimension Team"""
        
        # Send to all team members
        for user_id in all_user_ids:
            if not await check_user_notifications_enabled(user_id, "notify_new_comment"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="voice_note_added",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Voice note notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending voice_note_added notification: {str(e)}")


async def notify_project_onboarding(project_id: str, creator_id: str):
    """
    Notify all project stakeholders when they are onboarded to a new project
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get all assigned stakeholders
        stakeholder_ids = set()
        
        # Add team members
        if project.get("lead_architect_id"):
            stakeholder_ids.add(project["lead_architect_id"])
        if project.get("project_manager_id"):
            stakeholder_ids.add(project["project_manager_id"])
        
        # Add assigned contractors
        assigned_contractors = project.get("assigned_contractors", {})
        if isinstance(assigned_contractors, dict):
            stakeholder_ids.update(assigned_contractors.values())
        
        # Add client
        if project.get("client_id"):
            stakeholder_ids.add(project["client_id"])
        
        # Remove the creator (don't notify them)
        stakeholder_ids.discard(creator_id)
        
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""🎉 NEW PROJECT ASSIGNED

Project: {project.get("name", "Unknown Project")}
You have been assigned to this project!

👆 VIEW PROJECT: {project_link}

📋 Your Role: Team Member
📅 Start Date: {project.get('start_date', 'Not set')}
🎯 First Milestone: Layout Plan (Due in 3 days)

Welcome to the team! 🏗️

- 4th Dimension Team"""
        
        # Send to all stakeholders
        for user_id in stakeholder_ids:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="project_onboarding",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Project onboarding notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending project onboarding notification: {str(e)}")


async def notify_drawing_due_soon(project_id: str, drawing_name: str, due_date: datetime):
    """
    Notify owner and team leader about upcoming drawing due date
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get owner and team leader
        notify_user_ids = set()
        
        # Add owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if owner:
            notify_user_ids.add(owner["id"])
        
        # Add team leader/lead architect
        if project.get("lead_architect_id"):
            notify_user_ids.add(project["lead_architect_id"])
        
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        formatted_due_date = due_date.strftime("%B %d, %Y")
        
        message = f"""📐 DRAWING DUE SOON

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
📅 Due Date: {formatted_due_date}

⏰ This is the first drawing milestone for the project.

👆 VIEW PROJECT: {project_link}

🚀 Ready to start? Upload the drawing when ready!

- 4th Dimension Team"""
        
        for user_id in notify_user_ids:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="drawing_due_soon",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Drawing due date notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending drawing due date notification: {str(e)}")


async def notify_drawing_issued(
    project_id: str,
    drawing_name: str,
    drawing_category: str,
    recipient_ids: List[str],
    issued_by_id: str
):
    """
    Send WhatsApp notifications when a drawing is issued to selected recipients
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get issuer details
        issuer = await db.users.find_one({"id": issued_by_id}, {"_id": 0})
        issuer_name = issuer.get("name", "Team Member") if issuer else "Team Member"
        
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""📐 DRAWING ISSUED

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Category: {drawing_category}
Issued by: {issuer_name}

📋 This drawing has been issued and is ready for review.

👆 VIEW PROJECT: {project_link}

Quick Actions:
💬 Add Comment | ✅ Approve | 📥 Download PDF

- 4th Dimension Team"""
        
        # Send to each recipient
        for user_id in recipient_ids:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="drawing_issued",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Drawing issued notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending drawing issued notification: {str(e)}")


async def notify_next_drawing_available(project_id: str, drawing_name: str, sequence_number: int):
    """
    Notify team when next drawing becomes available
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.warning(f"Project {project_id} not found")
            return
        
        # Get owner and team leader
        notify_user_ids = set()
        
        # Add owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if owner:
            notify_user_ids.add(owner["id"])
        
        # Add team leader/lead architect
        if project.get("lead_architect_id"):
            notify_user_ids.add(project["lead_architect_id"])
        
        app_url = os.environ.get('FRONTEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{app_url}/projects/{project_id}"
        
        message = f"""🔓 NEXT DRAWING UNLOCKED

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Sequence: #{sequence_number}

✅ Previous drawing issued successfully!
📐 This drawing is now ready to work on.

👆 VIEW PROJECT: {project_link}

🚀 Ready to start the next milestone!

- 4th Dimension Team"""
        
        for user_id in notify_user_ids:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="next_drawing_available",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Next drawing available notifications sent for project {project_id}")
    
    except Exception as e:
        logger.error(f"Error sending next drawing available notification: {str(e)}")


async def notify_drawing_issued(
    project_id: str,
    drawing_name: str,
    drawing_category: str,
    recipient_ids: List[str],
    issued_by_id: str
):
    """
    Send WhatsApp notifications when a drawing is issued to selected recipients
    
    Args:
        project_id: Project ID
        drawing_name: Name of the drawing
        drawing_category: Category of the drawing
        recipient_ids: List of user IDs to notify
        issued_by_id: ID of user who issued the drawing
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.error(f"Project not found: {project_id}")
            return
        
        # Get issuer details
        issuer = await db.users.find_one({"id": issued_by_id}, {"_id": 0})
        issuer_name = issuer.get("name", "Team Member") if issuer else "Team Member"
        
        # Create project link
        frontend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{frontend_url}/projects/{project_id}"
        
        message = f"""📐 DRAWING ISSUED

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Category: {drawing_category}
Issued by: {issuer_name}

📋 This drawing has been issued and is ready for review.

👆 VIEW PROJECT: {project_link}

- 4th Dimension Team"""
        
        # Send to each recipient
        for user_id in recipient_ids:
            # Check if user has notifications enabled
            if not await check_user_notifications_enabled(user_id, "notify_drawing_issued"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="drawing_issued",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Drawing issued notifications sent for project {project_id}, drawing {drawing_name}")
    
    except Exception as e:
        logger.error(f"Error sending drawing issued notification: {str(e)}")


async def notify_next_drawing_available(
    project_id: str,
    drawing_name: str,
    sequence_number: int
):
    """
    Send WhatsApp notifications when the next drawing in sequence becomes available
    
    Args:
        project_id: Project ID
        drawing_name: Name of the newly available drawing
        sequence_number: Sequence number of the drawing
    """
    try:
        # Get project details
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            logger.error(f"Project not found: {project_id}")
            return
        
        # Get all team members assigned to the project
        assigned_user_ids = project.get("assigned_to", [])
        if project.get("team_leader"):
            assigned_user_ids.append(project["team_leader"])
        
        # Remove duplicates
        assigned_user_ids = list(set(assigned_user_ids))
        
        # Create project link
        frontend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://archflow-system.preview.emergentagent.com')
        project_link = f"{frontend_url}/projects/{project_id}"
        
        message = f"""🔓 NEXT DRAWING UNLOCKED

Project: {project.get("name", "Unknown Project")}
Drawing: {drawing_name}
Sequence: #{sequence_number}

✅ The previous drawing has been issued, and this drawing is now available to work on.

👆 VIEW PROJECT: {project_link}

🚀 Ready to start working on this drawing!

- 4th Dimension Team"""
        
        # Send to all assigned team members
        for user_id in assigned_user_ids:
            # Check if user has notifications enabled
            if not await check_user_notifications_enabled(user_id, "notify_next_drawing_available"):
                continue
            
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("mobile"):
                result = whatsapp_service.send_message(user["mobile"], message)
                await save_notification_log(
                    user_id=user_id,
                    phone_number=user["mobile"],
                    message_type="next_drawing_available",
                    message_body=message,
                    project_id=project_id,
                    result=result
                )
        
        logger.info(f"Next drawing available notifications sent for project {project_id}, drawing {drawing_name}")
    
    except Exception as e:
        logger.error(f"Error sending next drawing available notification: {str(e)}")


async def notify_owner_new_registration(user_name: str, user_email: str, role: str):
    """
    Notify owner when a new user registers
    """
    try:
        # Get owner
        owner = await get_db().users.find_one({"is_owner": True}, {"_id": 0})
        
        if not owner:
            logger.warning("Owner not found - cannot send registration notification")
            return
        
        # Prepare message
        message = (
            f"🔔 *New Registration*\n\n"
            f"Name: {user_name}\n"
            f"Email: {user_email}\n"
            f"Role: {role}\n\n"
            f"Please review and approve in the Pending Registrations section."
        )
        
        # Send WhatsApp to owner
        result = whatsapp_service.send_message(owner["mobile"], message)
        
        # Log the notification
        await save_notification_log(
            user_id=owner["id"],
            notification_type="notify_owner_new_registration",
            message=message,
            mobile_number=owner["mobile"],
            result=result
        )
        
        logger.info(f"New registration notification sent to owner for: {user_name}")
        
    except Exception as e:
        logger.error(f"Error sending new registration notification to owner: {str(e)}")


# Export all notification functions
__all__ = [
    'notify_user_registered',
    'notify_user_approved',
    'notify_drawing_uploaded',
    'notify_new_comment',
    'notify_task_assigned',
    'notify_milestone_completed',
    'notify_payment_due',
    'notify_site_visit_scheduled',
    'notify_voice_note_added',
    'notify_project_onboarding',
    'notify_drawing_due_soon',
    'notify_drawing_issued',
    'notify_next_drawing_available',
    'notify_owner_new_registration'
]
