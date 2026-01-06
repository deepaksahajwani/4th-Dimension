"""
Drawing Approval Reminder System
Sends immediate notification when drawing uploaded, then hourly reminders after 6 hours
"""

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', '')


async def get_owner_info() -> Optional[Dict]:
    """Get owner user info"""
    return await db.users.find_one({"is_owner": True}, {"_id": 0})


async def get_pending_approval_drawings() -> List[Dict]:
    """
    Get all drawings that are uploaded for review (under_review=True) 
    but not yet approved (is_approved=False)
    """
    cursor = db.project_drawings.find({
        "under_review": True,
        "is_approved": {"$ne": True},
        "is_not_applicable": {"$ne": True}
    }, {"_id": 0})
    
    drawings = await cursor.to_list(100)
    return drawings


async def send_approval_reminder(
    drawing: Dict,
    project: Dict,
    owner: Dict,
    is_initial: bool = False
):
    """Send approval reminder notification to owner"""
    from notification_service import notification_service
    
    drawing_name = drawing.get('name', 'Drawing')
    project_name = project.get('title', 'Project')
    drawing_id = drawing.get('id')
    project_id = project.get('id')
    
    # Calculate time since upload
    uploaded_at = drawing.get('uploaded_for_review_at') or drawing.get('updated_at')
    if isinstance(uploaded_at, str):
        uploaded_at = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
    
    if uploaded_at:
        hours_waiting = (datetime.now(timezone.utc) - uploaded_at).total_seconds() / 3600
        time_text = f"⏰ Waiting: {int(hours_waiting)} hours" if hours_waiting >= 1 else "⏰ Just uploaded"
    else:
        time_text = ""
    
    # Generate magic link to Drawing Review Page
    try:
        from services.magic_link_helper import create_drawing_review_magic_link
        deep_link = await create_drawing_review_magic_link(
            user_id=owner['id'],
            user_email=owner.get('email', ''),
            user_role='owner',
            project_id=project_id,
            drawing_id=drawing_id
        )
    except Exception as e:
        logger.warning(f"Failed to create magic link for reminder: {e}")
        deep_link = f"{APP_URL}/projects/{project_id}/drawing/{drawing_id}"
    
    if is_initial:
        message = f"""📤 *Drawing Uploaded - Approval Required*

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
{time_text}

Please review and approve this drawing.

👉 *Click to view:*
{deep_link}"""
    else:
        message = f"""⏰ *REMINDER: Drawing Pending Approval*

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
{time_text}

This drawing is still waiting for your approval.

👉 *Click to approve:*
{deep_link}"""
    
    # Send WhatsApp
    result = await notification_service.send_whatsapp(owner['mobile'], message)
    if result.get('success'):
        logger.info(f"Approval reminder sent for drawing: {drawing_name}")
    else:
        # Fallback to SMS
        sms_result = await notification_service.send_sms(owner['mobile'], message)
        if sms_result.get('success'):
            logger.info(f"SMS approval reminder sent for drawing: {drawing_name}")
    
    return result.get('success') or sms_result.get('success', False) if 'sms_result' in dir() else result.get('success', False)


async def update_reminder_tracking(drawing_id: str):
    """Update the last reminder sent time for a drawing"""
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {
            "last_approval_reminder_at": datetime.now(timezone.utc).isoformat(),
            "approval_reminder_count": {"$inc": 1}
        }}
    )
    
    # Also use $inc properly
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$inc": {"approval_reminder_count": 1}}
    )


async def check_and_send_reminders():
    """
    Main function to check pending drawings and send reminders
    
    Logic:
    - If drawing uploaded < 6 hours ago: No reminder (initial notification already sent)
    - If drawing uploaded >= 6 hours ago: Send hourly reminders
    """
    try:
        owner = await get_owner_info()
        if not owner or not owner.get('mobile'):
            logger.warning("Owner not found or no mobile number for reminders")
            return
        
        pending_drawings = await get_pending_approval_drawings()
        
        if not pending_drawings:
            logger.debug("No pending drawings for approval")
            return
        
        now = datetime.now(timezone.utc)
        reminders_sent = 0
        
        for drawing in pending_drawings:
            drawing_id = drawing.get('id')
            project_id = drawing.get('project_id')
            
            # Get project info
            project = await db.projects.find_one({"id": project_id}, {"_id": 0})
            if not project:
                continue
            
            # Get upload time
            uploaded_at = drawing.get('uploaded_for_review_at') or drawing.get('updated_at')
            if isinstance(uploaded_at, str):
                try:
                    uploaded_at = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                except:
                    uploaded_at = now - timedelta(hours=7)  # Default to eligible for reminder
            
            if not uploaded_at:
                continue
            
            hours_since_upload = (now - uploaded_at).total_seconds() / 3600
            
            # Only send reminders if uploaded >= 6 hours ago
            if hours_since_upload < 6:
                continue
            
            # Check when last reminder was sent
            last_reminder = drawing.get('last_approval_reminder_at')
            if last_reminder:
                if isinstance(last_reminder, str):
                    last_reminder = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                
                hours_since_reminder = (now - last_reminder).total_seconds() / 3600
                
                # Only send if >= 1 hour since last reminder
                if hours_since_reminder < 1:
                    continue
            
            # Send reminder
            success = await send_approval_reminder(drawing, project, owner, is_initial=False)
            
            if success:
                # Update tracking
                await db.project_drawings.update_one(
                    {"id": drawing_id},
                    {
                        "$set": {"last_approval_reminder_at": now.isoformat()},
                        "$inc": {"approval_reminder_count": 1}
                    }
                )
                reminders_sent += 1
        
        if reminders_sent > 0:
            logger.info(f"Sent {reminders_sent} approval reminders")
            
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {str(e)}")


async def send_immediate_approval_notification(
    drawing_id: str,
    drawing_name: str,
    project_id: str,
    uploaded_by_name: str
):
    """
    Send immediate notification when drawing is uploaded for review
    Called from the drawing upload/update endpoint
    Sends: In-app, WhatsApp (template-based), SMS (fallback), and Email
    """
    try:
        owner = await get_owner_info()
        if not owner:
            logger.warning("Owner not found for immediate approval notification")
            return
        
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        project_name = project.get('title', 'Project') if project else 'Project'
        
        # Generate magic link to Drawing Review Page
        try:
            from services.magic_link_helper import create_drawing_review_magic_link
            deep_link = await create_drawing_review_magic_link(
                user_id=owner['id'],
                user_email=owner.get('email', ''),
                user_role='owner',
                project_id=project_id,
                drawing_id=drawing_id
            )
        except Exception as e:
            logger.warning(f"Failed to create magic link: {e}")
            # Fallback to direct Drawing Review Page URL
            deep_link = f"{APP_URL}/projects/{project_id}/drawing/{drawing_id}"
        
        # In-app link uses Drawing Review Page format
        in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        
        from notification_service import notification_service
        
        # 1. Create in-app notification FIRST (always works)
        await notification_service.create_in_app_notification(
            user_id=owner['id'],
            title="Drawing Approval Needed",
            message=f"📤 {drawing_name} uploaded for approval by {uploaded_by_name}",
            notification_type="drawing_approval_needed",
            link=in_app_link,
            project_id=project_id
        )
        logger.info(f"In-app notification created for drawing approval: {drawing_name}")
        
        # 2. Send WhatsApp using TEMPLATE (works outside 24h window)
        if owner.get('mobile'):
            try:
                from template_notification_service import template_notification_service
                
                # Use the drawing_approval_needed template
                result = await template_notification_service.notify_drawing_approval_needed(
                    phone_number=owner['mobile'],
                    owner_name=owner.get('name', 'Sir/Madam'),
                    project_name=project_name,
                    drawing_name=drawing_name,
                    uploader_name=uploaded_by_name,
                    portal_url=deep_link,
                    owner_id=owner['id'],
                    project_id=project_id,
                    drawing_id=drawing_id
                )
                
                if result.get('success'):
                    logger.info(f"WhatsApp template notification sent for drawing approval: {drawing_name}")
                else:
                    # Fallback to SMS
                    sms_message = f"Drawing '{drawing_name}' needs your approval for {project_name}. Uploaded by {uploaded_by_name}. View: {deep_link}"
                    await notification_service.send_sms(owner['mobile'], sms_message)
                    logger.info(f"SMS approval notification sent for: {drawing_name}")
                    
            except ImportError:
                # Template service not available, use freeform
                whatsapp_message = f"""📤 *Drawing Uploaded for Approval*

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
👤 *Uploaded by:* {uploaded_by_name}

Please review and approve: {deep_link}"""
                await notification_service.send_whatsapp(owner['mobile'], whatsapp_message)
        
        # Email notifications disabled - WhatsApp/SMS only
        # (Email only for OTP, registration, and welcome messages)
        
        # Mark the upload time for reminder tracking
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {
                "uploaded_for_review_at": datetime.now(timezone.utc).isoformat(),
                "approval_reminder_count": 0
            }}
        )
        
        logger.info(f"All approval notifications sent for drawing: {drawing_name}")
        
    except Exception as e:
        logger.error(f"Error sending immediate approval notification: {str(e)}")


# Background task for periodic reminder checks
async def reminder_scheduler():
    """
    Background task that runs every 15 minutes to check for pending approvals
    and send reminders as needed
    """
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            logger.error(f"Reminder scheduler error: {str(e)}")
        
        # Wait 15 minutes before next check
        await asyncio.sleep(900)  # 900 seconds = 15 minutes
