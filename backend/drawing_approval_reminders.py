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
    
    # Deep link to the specific drawing
    deep_link = f"{APP_URL}/projects/{project_id}?drawing={drawing_id}"
    
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
    Sends: In-app, WhatsApp, SMS (fallback), and Email
    """
    try:
        owner = await get_owner_info()
        if not owner:
            logger.warning("Owner not found for immediate approval notification")
            return
        
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        project_name = project.get('title', 'Project') if project else 'Project'
        
        # Deep link to the specific drawing
        deep_link = f"{APP_URL}/projects/{project_id}?drawing={drawing_id}"
        
        from notification_service import notification_service
        
        whatsapp_message = f"""📤 *NEW: Drawing Uploaded for Approval*

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
👤 *Uploaded by:* {uploaded_by_name}
📅 *Time:* {datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p')}

Please review and approve this drawing.

👉 *Click to view & approve:*
{deep_link}

⏰ You will receive hourly reminders if not approved within 6 hours."""
        
        # 1. Create in-app notification FIRST (always works)
        await notification_service.create_in_app_notification(
            user_id=owner['id'],
            title="Drawing Approval Needed",
            message=f"📤 {drawing_name} uploaded for approval by {uploaded_by_name}",
            notification_type="drawing_approval_needed",
            link=f"/projects/{project_id}?drawing={drawing_id}",
            project_id=project_id
        )
        logger.info(f"In-app notification created for drawing approval: {drawing_name}")
        
        # 2. Send WhatsApp if owner has mobile
        if owner.get('mobile'):
            result = await notification_service.send_whatsapp(owner['mobile'], whatsapp_message)
            if result.get('success'):
                logger.info(f"WhatsApp approval notification sent for: {drawing_name}")
            else:
                # Fallback to SMS
                await notification_service.send_sms(owner['mobile'], whatsapp_message)
                logger.info(f"SMS approval notification sent for: {drawing_name}")
        
        # 3. Send Email notification
        if owner.get('email'):
            email_subject = f"Drawing Approval Needed - {drawing_name}"
            email_html = f"""
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                </head>
                <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                    <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #F59E0B; font-size: 28px; margin-bottom: 10px;">📤 Drawing Uploaded for Approval</h1>
                            <p style="color: #6B7280; font-size: 16px;">Action Required</p>
                        </div>
                        
                        <div style="background: #FEF3C7; padding: 25px; border-radius: 10px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                            <h3 style="color: #92400E; margin-top: 0;">Drawing Details:</h3>
                            <p style="margin: 10px 0;"><strong>📁 Drawing:</strong> {drawing_name}</p>
                            <p style="margin: 10px 0;"><strong>🏗️ Project:</strong> {project_name}</p>
                            <p style="margin: 10px 0;"><strong>👤 Uploaded by:</strong> {uploaded_by_name}</p>
                            <p style="margin: 10px 0;"><strong>📅 Time:</strong> {datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p')}</p>
                        </div>
                        
                        <p style="font-size: 16px; color: #374151;">Please review and approve this drawing at your earliest convenience.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{deep_link}" style="display: inline-block; background: #F59E0B; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                                View & Approve Drawing
                            </a>
                        </div>
                        
                        <p style="font-size: 14px; color: #6B7280; text-align: center;">
                            ⏰ You will receive hourly reminders if this drawing is not approved within 6 hours.
                        </p>
                        
                        <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                            <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            await notification_service.send_email(owner['email'], email_subject, email_html)
            logger.info(f"Email approval notification sent for: {drawing_name}")
        
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
