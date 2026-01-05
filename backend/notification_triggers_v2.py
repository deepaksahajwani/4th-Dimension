"""
Complete Notification Triggers - All notification types
Implements the notification system using WhatsApp templates
Uses template_notification_service for consistent template-based messaging
All notifications are now non-blocking using async queue
Magic links are used for secure one-click authentication from notifications
"""

import os
import logging
import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from notification_service import notification_service, message_templates, APP_URL
from email_templates import get_welcome_email_content
from whatsapp_templates import WHATSAPP_TEMPLATES

# Import template notification service
try:
    from template_notification_service import template_notification_service
except ImportError:
    template_notification_service = None

# Import async notification service for non-blocking delivery
try:
    from async_notifications import async_notification_service
    USE_ASYNC_NOTIFICATIONS = True
except ImportError:
    async_notification_service = None
    USE_ASYNC_NOTIFICATIONS = False

# Import magic link helper for secure notification links
try:
    from services.magic_link_helper import (
        create_project_magic_link,
        create_drawing_magic_link,
        create_drawing_review_magic_link,
        create_comment_magic_link,
        create_dashboard_magic_link,
        get_user_info_for_magic_link,
        get_user_info_by_email
    )
    USE_MAGIC_LINKS = True
except ImportError:
    USE_MAGIC_LINKS = False
    logger = logging.getLogger(__name__)
    logger.warning("Magic link helper not available - using direct links")

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def get_magic_link_for_project(
    recipient_id: str,
    project_id: str,
    drawing_id: str = None
) -> str:
    """
    Generate a magic link for project access, or fallback to direct link.
    
    Args:
        recipient_id: The user ID who will receive this link
        project_id: The project to link to
        drawing_id: Optional drawing to highlight
    
    Returns:
        Magic link URL or direct link as fallback
    """
    if USE_MAGIC_LINKS:
        try:
            user = await get_user_info_for_magic_link(recipient_id)
            if user:
                return await create_project_magic_link(
                    user_id=user["id"],
                    user_email=user["email"],
                    user_role=user.get("role", "client"),
                    project_id=project_id,
                    drawing_id=drawing_id
                )
        except Exception as e:
            logger.warning(f"Failed to create magic link, using direct link: {e}")
    
    # Fallback to direct link
    url = f"{APP_URL}/projects/{project_id}"
    if drawing_id:
        url += f"?drawing={drawing_id}"
    return url

async def get_magic_link_for_drawing(recipient_id: str, project_id: str, drawing_id: str = None):
    """
    Generate a magic link for a drawing notification.
    Uses the Drawing Review Page for a dedicated single-item view.
    
    Args:
        recipient_id: The user ID who will receive this link
        project_id: The project ID
        drawing_id: The drawing ID to review
    
    Returns:
        Magic link URL or direct link as fallback
    """
    if USE_MAGIC_LINKS and drawing_id:
        try:
            user = await get_user_info_for_magic_link(recipient_id)
            if user:
                return await create_drawing_review_magic_link(
                    user_id=user["id"],
                    user_email=user["email"],
                    user_role=user.get("role", "client"),
                    project_id=project_id,
                    drawing_id=drawing_id
                )
        except Exception as e:
            logger.warning(f"Failed to create magic link, using direct link: {e}")
    
    # Fallback to direct link using Drawing Review Page format
    if drawing_id:
        return f"{APP_URL}/projects/{project_id}/drawing/{drawing_id}"
    return f"{APP_URL}/projects/{project_id}"


async def get_magic_link_for_drawing_review(
    recipient_id: str,
    project_id: str,
    drawing_id: str
) -> str:
    """
    Generate a magic link for dedicated drawing review page.
    """
    if USE_MAGIC_LINKS:
        try:
            user = await get_user_info_for_magic_link(recipient_id)
            if user:
                return await create_drawing_review_magic_link(
                    user_id=user["id"],
                    user_email=user["email"],
                    user_role=user.get("role", "client"),
                    project_id=project_id,
                    drawing_id=drawing_id
                )
        except Exception as e:
            logger.warning(f"Failed to create magic link: {e}")
    
    return f"{APP_URL}/projects/{project_id}/drawing/{drawing_id}"


async def get_magic_link_for_comment(
    recipient_id: str,
    project_id: str,
    drawing_id: str,
    comment_id: str
) -> str:
    """
    Generate a magic link for comment notification.
    """
    if USE_MAGIC_LINKS:
        try:
            user = await get_user_info_for_magic_link(recipient_id)
            if user:
                return await create_comment_magic_link(
                    user_id=user["id"],
                    user_email=user["email"],
                    user_role=user.get("role", "client"),
                    project_id=project_id,
                    drawing_id=drawing_id,
                    comment_id=comment_id
                )
        except Exception as e:
            logger.warning(f"Failed to create magic link: {e}")
    
    return f"{APP_URL}/projects/{project_id}?drawing={drawing_id}&comment={comment_id}"


async def get_magic_link_for_dashboard(recipient_id: str) -> str:
    """
    Generate a magic link for dashboard access.
    """
    if USE_MAGIC_LINKS:
        try:
            user = await get_user_info_for_magic_link(recipient_id)
            if user:
                return await create_dashboard_magic_link(
                    user_id=user["id"],
                    user_email=user["email"],
                    user_role=user.get("role", "client")
                )
        except Exception as e:
            logger.warning(f"Failed to create magic link: {e}")
    
    return f"{APP_URL}/dashboard"


def queue_whatsapp_async(phone: str, message: str = None, content_sid: str = None, variables: dict = None):
    """Queue WhatsApp notification for async delivery (non-blocking)"""
    if USE_ASYNC_NOTIFICATIONS and async_notification_service:
        if content_sid:
            async_notification_service.queue_whatsapp_template(
                phone=phone,
                content_sid=content_sid,
                variables=variables or {}
            )
        elif message:
            async_notification_service.queue_whatsapp(phone=phone, message=message)
        logger.debug(f"Queued WhatsApp notification to {phone}")
    else:
        # Fallback to sync - create task to avoid blocking
        asyncio.create_task(_send_whatsapp_background(phone, message, content_sid, variables))


async def _send_whatsapp_background(phone: str, message: str = None, content_sid: str = None, variables: dict = None):
    """Background task for WhatsApp when async service not available"""
    try:
        if content_sid and template_notification_service:
            await template_notification_service.send_notification(
                template_key=None,
                phone=phone,
                content_sid=content_sid,
                variables=variables or {}
            )
        elif message:
            await notification_service.send_whatsapp(phone, message)
    except Exception as e:
        logger.error(f"Background WhatsApp send failed: {e}")


def queue_email_async(to_email: str, subject: str, html_content: str):
    """Queue email notification for async delivery (non-blocking)"""
    if USE_ASYNC_NOTIFICATIONS and async_notification_service:
        async_notification_service.queue_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )
        logger.debug(f"Queued email notification to {to_email}")
    else:
        # Fallback to sync - create task to avoid blocking
        asyncio.create_task(_send_email_background(to_email, subject, html_content))


async def _send_email_background(to_email: str, subject: str, html_content: str):
    """Background task for email when async service not available"""
    try:
        await notification_service.send_email(to_email, subject, html_content)
    except Exception as e:
        logger.error(f"Background email send failed: {e}")


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Helper to get user by ID"""
    return await db.users.find_one({"id": user_id}, {"_id": 0})


async def get_project_by_id(project_id: str) -> Optional[Dict]:
    """Helper to get project by ID"""
    return await db.projects.find_one({"id": project_id}, {"_id": 0})


# ============================================
# 1. USER REGISTRATION
# ============================================
async def notify_user_registration(user_data: Dict):
    """
    Trigger: New user registers
    Recipients: Owner (approval needed), Registrant (confirmation)
    Channels: In-App, WhatsApp, Email
    """
    try:
        user_name = user_data.get('name')
        user_email = user_data.get('email')
        user_role = user_data.get('role')
        # user_id available for future notification enhancements
        _ = user_data.get('id')
        
        # Get owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if not owner:
            logger.error("No owner found for registration notification")
            return
        
        # Notify owner
        owner_message = message_templates.user_registration_owner(
            user_name, user_role, user_email
        )
        await notification_service.send_notification(
            user_ids=[owner['id']],
            title="New User Registration",
            message=owner_message,
            notification_type="user_registration",
            channels=['in_app', 'whatsapp'],
            link="/pending-registrations"
        )
        
        # Notify registrant
        registrant_message = message_templates.user_registration_registrant(user_name)
        
        # Send email to registrant
        email_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Registration Received</h2>
                <p>{registrant_message}</p>
            </body>
        </html>
        """
        
        # Note: Freeform WhatsApp only works if user messaged first (24hr window)
        # For new registrations, we rely on email and in-app notifications
        if user_data.get('mobile'):
            try:
                await notification_service.send_whatsapp(user_data['mobile'], registrant_message)
            except Exception as wa_error:
                logger.warning(f"WhatsApp to registrant failed (expected if outside 24hr window): {wa_error}")
        
        await notification_service.send_email(
            to_email=user_email,
            subject="Registration Pending Approval - 4th Dimension",
            html_content=email_html
        )
        
        logger.info(f"User registration notifications sent for {user_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_user_registration: {str(e)}")


# ============================================
# 2. USER APPROVAL
# ============================================
async def notify_user_approval(user_id: str):
    """
    Trigger: Owner approves new user
    Recipients: Owner (confirmation), Approved User (welcome)
    Channels: In-App, WhatsApp (template), Email
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return
        
        user_name = user.get('name')
        user_email = user.get('email')
        user_mobile = user.get('mobile')
        user_role = user.get('role', 'team_member')
        user_designation = user.get('designation') or user_role.replace('_', ' ').title()
        
        # Get owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        # Notify owner (confirmation)
        owner_message = message_templates.user_approved_owner(user_name)
        await notification_service.send_notification(
            user_ids=[owner['id']],
            title="User Approved",
            message=owner_message,
            notification_type="user_approved",
            channels=['in_app']
        )
        
        # Notify approved user using WhatsApp TEMPLATE (v2 with 5 variables)
        whatsapp_sent = False
        if user_mobile:
            template_sid = WHATSAPP_TEMPLATES.get("user_approved")
            if template_sid:
                # Get approver name (owner)
                approver_name = owner.get('name', 'Admin') if owner else 'Admin'
                # Format approval date
                from datetime import datetime, timezone
                approval_date = datetime.now(timezone.utc).strftime("%d %b %Y")
                
                result = await notification_service.send_whatsapp_template(
                    phone_number=user_mobile,
                    content_sid=template_sid,
                    content_variables={
                        "1": user_name,
                        "2": user_designation,
                        "3": approver_name,
                        "4": approval_date,
                        "5": APP_URL
                    }
                )
                whatsapp_sent = result.get('success', False)
                if whatsapp_sent:
                    logger.info(f"WhatsApp welcome sent to {user_name}")
            
            # Fallback to SMS if WhatsApp template failed
            if not whatsapp_sent:
                sms_message = f"""🎉 Welcome to 4th Dimension, {user_name}!

Your registration as {user_designation} has been approved.

🔐 Login to your account: {APP_URL}

Reply START to receive WhatsApp notifications.

- 4th Dimension Architects
+917016779016"""
                
                await notification_service.send_sms(user_mobile, sms_message)
                logger.info(f"SMS welcome sent to {user_name} (WhatsApp fallback)")
        
        # Generate professional HTML email template (English only)
        login_url = f"{APP_URL}"
        email_subject, email_html = get_welcome_email_content(user, login_url)
        
        # Send professional HTML email
        await notification_service.send_email(
            to_email=user_email,
            subject=email_subject,
            html_content=email_html
        )
        
        logger.info(f"User approval notifications sent for {user_name} with professional HTML template")
        
    except Exception as e:
        logger.error(f"Error in notify_user_approval: {str(e)}")


# ============================================
# 3. PROJECT CREATION
# ============================================
async def notify_project_creation(project_id: str):
    """
    Trigger: New project is created
    Recipients: Owner, Client, Team Leader
    Channels: WhatsApp (templates), Email
    Message: Formal for client, casual for team
    """
    try:
        project = await get_project_by_id(project_id)
        if not project:
            logger.error(f"Project not found: {project_id}")
            return
        
        project_name = project.get('title') or project.get('name', 'Untitled Project')
        client_id = project.get('client_id')
        team_leader_id = project.get('team_leader_id')
        
        # Get client - try clients collection first, then users collection
        client = None
        if client_id:
            client = await db.clients.find_one({"id": client_id}, {"_id": 0})
            if not client:
                client = await get_user_by_id(client_id)
        if not client:
            logger.warning(f"Client not found for project {project_id}, client_id: {client_id}")
        
        # Get team leader
        team_leader = await get_user_by_id(team_leader_id) if team_leader_id else None
        if not team_leader:
            logger.warning(f"Team leader not found for project {project_id}, team_leader_id: {team_leader_id}")
        
        # Get owner (available for future notification enhancements)
        _ = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        # Send WhatsApp to CLIENT using TEMPLATE
        if client and client.get('phone'):
            template_sid = WHATSAPP_TEMPLATES.get("project_created_client")
            if template_sid:
                try:
                    await notification_service.send_whatsapp_template(
                        phone_number=client['phone'],
                        content_sid=template_sid,
                        content_variables={
                            "1": client.get('name', client.get('contact_person', 'Valued Client')),
                            "2": project_name,
                            "3": team_leader.get('name', 'Our Team') if team_leader else 'Our Team',
                            "4": team_leader.get('mobile', 'Contact via portal') if team_leader else 'Contact via portal',
                            "5": APP_URL
                        }
                    )
                    logger.info(f"WhatsApp template sent to client for project {project_name}")
                except Exception as wa_error:
                    logger.warning(f"WhatsApp template to client failed: {wa_error}")
        
        # Send email notification to client
        project_url = f"{APP_URL}/projects/{project_id}"
        email_subject = f"Your Project is Ready - {project_name}"
        email_html = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Your Project is Ready! 🎉</h1>
                        <p style="color: #6B7280; font-size: 16px;">4th Dimension - Design Excellence</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {client.get('name')},</h2>
                    
                    <p style="font-size: 16px; color: #374151; margin: 20px 0;">
                        Great news! Your project <strong style="color: #4F46E5;">{project_name}</strong> has been set up and is now ready for collaboration.
                    </p>
                    
                    <div style="background: #EEF2FF; padding: 25px; border-radius: 10px; margin: 25px 0; border-left: 4px solid #4F46E5;">
                        <h3 style="color: #4F46E5; margin-top: 0;">What You Can Do Now:</h3>
                        <ul style="margin: 15px 0; padding-left: 20px; color: #374151;">
                            <li style="margin: 10px 0;">View project details and timelines</li>
                            <li style="margin: 10px 0;">Review design drawings and plans</li>
                            <li style="margin: 10px 0;">Add comments and feedback on designs</li>
                            <li style="margin: 10px 0;">Track project progress in real-time</li>
                            <li style="margin: 10px 0;">Download drawings and documents</li>
                        </ul>
                    </div>
                    
                    <div style="background: #D1FAE5; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <p style="margin: 0 0 10px 0;"><strong style="color: #065F46;">👤 Your Team Leader:</strong></p>
                        <p style="margin: 5px 0; color: #047857;"><strong>{team_leader.get('name')}</strong></p>
                        <p style="margin: 5px 0; color: #047857;">📱 {team_leader.get('mobile', 'Contact via portal')}</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{project_url}" 
                           style="display: inline-block; background: #4F46E5; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            View Your Project
                        </a>
                    </div>
                    
                    <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin-top: 30px;">
                        <p style="margin: 0; font-size: 14px; color: #6B7280;">
                            <strong>Need help?</strong> Contact us at contact@4thdimensionarchitect.com or call +91 98765 43210
                        </p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB; text-align: center;">
                        <p style="color: #9CA3AF; font-size: 12px; margin: 5px 0;">
                            © 4th Dimension - Design Excellence
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        if client and client.get('email'):
            await notification_service.send_email(
                to_email=client['email'],
                subject=email_subject,
                html_content=email_html
            )
        
        # Send to TEAM LEADER using TEMPLATE
        if team_leader and team_leader.get('mobile'):
            template_sid = WHATSAPP_TEMPLATES.get("project_created_team")
            if template_sid:
                try:
                    await notification_service.send_whatsapp_template(
                        phone_number=team_leader['mobile'],
                        content_sid=template_sid,
                        content_variables={
                            "1": project_name,
                            "2": client.get('name', client.get('contact_person', 'Client')) if client else 'Client',
                            "3": client.get('phone', client.get('mobile', 'N/A')) if client else 'N/A',
                            "4": APP_URL
                        }
                    )
                    logger.info(f"WhatsApp template sent to team leader for project {project_name}")
                except Exception as wa_error:
                    logger.warning(f"WhatsApp template to team leader failed: {wa_error}")
            
            # In-app notification for team leader
            await notification_service.send_notification(
                user_ids=[team_leader_id],
                title=f"New Project: {project_name}",
                message=f"You've been assigned as team leader for {project_name}",
                notification_type="project_created",
                channels=['in_app'],
                link=f"/projects/{project_id}",
                project_id=project_id
            )
        
        logger.info(f"Project creation notifications sent for {project_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_project_creation: {str(e)}")


# ============================================
# 4. CONTRACTOR/CONSULTANT ADDED
# ============================================
async def notify_contractor_consultant_added(
    project_id: str,
    person_id: str,
    person_type: str  # 'contractor' or 'consultant'
):
    """
    Trigger: Contractor or consultant is added to project
    Recipients: Owner, Contractor/Consultant, Client, Team Leader
    Channels: WhatsApp
    """
    try:
        project = await get_project_by_id(project_id)
        if not project:
            return
        
        project_name = project.get('title') or project.get('name')
        client_id = project.get('client_id')
        team_leader_id = project.get('team_leader_id')
        
        person = await get_user_by_id(person_id)
        if not person:
            return
        
        person_name = person.get('name')
        person_role = person.get('role', person_type)
        person_mobile = person.get('mobile')
        person_email = person.get('email')
        
        # Get related users
        client = await get_user_by_id(client_id)
        team_leader = await get_user_by_id(team_leader_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        # Message to contractor/consultant
        person_message = f"""Welcome to the project, {person_name}!

📁 Project: {project_name}
🎯 Your Role: {person_role}
👤 Client: {client.get('name') if client else 'N/A'}
📞 Team Leader: {team_leader.get('name') if team_leader else 'N/A'}

Your responsibilities:
• Complete assigned tasks on time
• Communicate progress regularly
• Maintain quality standards

View project: {APP_URL}/projects/{project_id}

Let's create something great together! 🚀"""
        
        if person_mobile:
            await notification_service.send_whatsapp(person_mobile, person_message)
        
        # Message to client
        if client and client.get('mobile'):
            client_message = f"""Dear {client.get('name')},

A {person_type} has been onboarded for your project "{project_name}".

👤 Name: {person_name}
🎯 Role: {person_role}
📞 Contact: {person_mobile or 'N/A'}
📧 Email: {person_email}

{person_name} brings expertise and experience to ensure quality delivery of your project.

For any queries, please contact your Team Leader: {team_leader.get('name') if team_leader else 'N/A'}

Best regards,
4th Dimension Architects"""
            
            await notification_service.send_whatsapp(client['mobile'], client_message)
        
        # Simple message to owner and team leader
        team_message = f"""✅ {person_type.title()} Onboarded

📁 Project: {project_name}
👤 {person_name} ({person_role})

View: {APP_URL}/projects/{project_id}"""
        
        notification_recipients = [owner['id']]
        if team_leader_id:
            notification_recipients.append(team_leader_id)
        
        await notification_service.send_notification(
            user_ids=notification_recipients,
            title=f"{person_type.title()} Added",
            message=team_message,
            notification_type=f"{person_type}_added",
            channels=['in_app', 'whatsapp'],
            link=f"/projects/{project_id}",
            project_id=project_id
        )
        
        logger.info(f"{person_type} added notification sent for {person_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_contractor_consultant_added: {str(e)}")


# ============================================
# 5. DRAWING UPLOADED
# ============================================
async def notify_drawing_uploaded(project_id: str, drawing_id: str, uploaded_by_id: str):
    """
    Trigger: Drawing is uploaded
    Recipients: Owner
    Channels: WhatsApp (template), In-App
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        uploader = await get_user_by_id(uploaded_by_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, uploader, owner]):
            return
        
        project_name = project.get('title') or project.get('name')
        drawing_name = drawing.get('name')
        uploader_name = uploader.get('name')
        
        # Use template notification service if available
        if template_notification_service and owner.get('mobile'):
            await template_notification_service.notify_drawing_approval_needed(
                phone_number=owner['mobile'],
                owner_name=owner.get('name', 'Admin'),
                project_name=project_name,
                drawing_name=drawing_name,
                uploader_name=uploader_name,
                owner_id=owner['id'],
                project_id=project_id,
                drawing_id=drawing_id
            )
        else:
            # Fallback to freeform message
            message = f"""📤 Drawing Uploaded for Approval

📁 Project: {project_name}
📐 Drawing: {drawing_name}
👤 Uploaded by: {uploader_name}
📅 Date: {datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p')}

Please review and approve.

View: {APP_URL}/projects/{project_id}/drawings"""
            
            await notification_service.send_notification(
                user_ids=[owner['id']],
                title="Drawing Approval Needed",
                message=message,
                notification_type="drawing_uploaded",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawings",
                project_id=project_id
            )
        
        logger.info(f"Drawing upload notification sent for {drawing_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_uploaded: {str(e)}")


# ============================================
# 6. DRAWING APPROVED
# ============================================
async def notify_drawing_approved(project_id: str, drawing_id: str):
    """
    Trigger: Drawing is approved
    Recipients: Team Leader
    Channels: WhatsApp (template), In-App
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        
        if not all([project, drawing]):
            return
        
        team_leader_id = project.get('team_leader_id')
        if not team_leader_id:
            logger.warning(f"No team leader assigned for project {project_id}")
            return
        
        team_leader = await get_user_by_id(team_leader_id)
        if not team_leader:
            return
        
        project_name = project.get('title') or project.get('name')
        drawing_name = drawing.get('name')
        revision = str(drawing.get('current_revision', 0))
        
        # Use template notification service if available
        if template_notification_service and team_leader.get('mobile'):
            await template_notification_service.notify_drawing_approved(
                phone_number=team_leader['mobile'],
                recipient_name=team_leader.get('name'),
                project_name=project_name,
                drawing_name=drawing_name,
                revision=revision,
                recipient_id=team_leader_id,
                project_id=project_id,
                drawing_id=drawing_id
            )
        else:
            # Fallback to freeform message
            message = f"""✅ Drawing Approved - Ready to Issue

📁 Project: {project_name}
📐 Drawing: {drawing_name}
🎯 Status: Approved

You can now issue this drawing to the client.

View & Issue: {APP_URL}/projects/{project_id}/drawings"""
            
            await notification_service.send_notification(
                user_ids=[team_leader_id],
                title="Drawing Approved",
                message=message,
                notification_type="drawing_approved",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawings",
                project_id=project_id
            )
        
        logger.info(f"Drawing approval notification sent for {drawing_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_approved: {str(e)}")


# ============================================
# 7. DRAWING REVISED (by Owner/Team Leader)
# ============================================
async def notify_drawing_revised_internal(project_id: str, drawing_id: str, revised_by_id: str):
    """
    Trigger: Drawing revised by owner or team leader
    Recipients: Team Leader
    Channels: WhatsApp (template), In-App
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        revised_by = await get_user_by_id(revised_by_id)
        
        if not all([project, drawing, revised_by]):
            return
        
        team_leader_id = project.get('team_leader_id')
        if not team_leader_id or team_leader_id == revised_by_id:
            return  # Don't notify if team leader revised it themselves
        
        team_leader = await get_user_by_id(team_leader_id)
        if not team_leader:
            return
        
        project_name = project.get('title') or project.get('name')
        drawing_name = drawing.get('name')
        
        # Use template notification service
        if template_notification_service and team_leader.get('mobile'):
            await template_notification_service.notify_revision_requested(
                phone_number=team_leader['mobile'],
                team_leader_name=team_leader.get('name'),
                project_name=project_name,
                drawing_name=drawing_name,
                requester_name=revised_by.get('name'),
                reason="Please review and update",
                team_leader_id=team_leader_id,
                project_id=project_id,
                drawing_id=drawing_id
            )
        else:
            # Fallback to freeform message
            message = f"""🔄 Drawing Revision Required

📁 Project: {project_name}
📐 Drawing: {drawing_name}
👤 Revised by: {revised_by.get('name')}

Please review the revision comments and update the drawing.

View Revision: {APP_URL}/projects/{project_id}/drawing/{drawing_id}"""
            
            await notification_service.send_notification(
                user_ids=[team_leader_id],
                title="Drawing Revision Request",
                message=message,
                notification_type="drawing_revised_internal",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawing/{drawing_id}",
                project_id=project_id
            )
        
        logger.info("Internal drawing revision notification sent")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_revised_internal: {str(e)}")


# ============================================
# 8. DRAWING REVISED (by Client/Contractor/Consultant)
# ============================================
async def notify_drawing_revised_external(project_id: str, drawing_id: str, revised_by_id: str):
    """
    Trigger: Drawing revised by client, contractor, or consultant
    Recipients: Owner, Team Leader
    Channels: WhatsApp
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        revised_by = await get_user_by_id(revised_by_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, revised_by, owner]):
            return
        
        team_leader_id = project.get('team_leader_id')
        
        message = f"""🔄 Drawing Revision from {revised_by.get('role', 'External Party').title()}

📁 Project: {project.get('title') or project.get('name')}
📐 Drawing: {drawing.get('name')}
👤 Revised by: {revised_by.get('name')}

Please review the comments and take necessary action.

View Revision: {APP_URL}/projects/{project_id}/drawing/{drawing_id}"""
        
        recipients = [owner['id']]
        if team_leader_id:
            recipients.append(team_leader_id)
        
        await notification_service.send_notification(
            user_ids=recipients,
            title="External Drawing Revision",
            message=message,
            notification_type="drawing_revised_external",
            channels=['in_app', 'whatsapp'],
            link=f"/projects/{project_id}/drawing/{drawing_id}",
            project_id=project_id
        )
        
        logger.info("External drawing revision notification sent")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_revised_external: {str(e)}")


# ============================================
# 9. DRAWING ISSUED
# ============================================
async def notify_drawing_issued(
    project_id: str,
    drawing_id: str,
    recipient_ids: List[str],
    issued_by_id: str
):
    """
    Trigger: Drawing is issued
    Recipients: Selected recipients + Owner (mandatory)
    Channels: WhatsApp (template), In-App
    Message: Uses approved WhatsApp templates based on recipient type
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        issued_by = await get_user_by_id(issued_by_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, issued_by, owner]):
            logger.error("Drawing issued notification failed: Missing data")
            return
        
        project_name = project.get('title') or project.get('name')
        drawing_name = drawing.get('name')
        revision = str(drawing.get('current_revision', 0))
        issue_date = datetime.now(timezone.utc).strftime('%d %b %Y')
        
        # Ensure owner is in recipients
        if owner['id'] not in recipient_ids:
            recipient_ids.append(owner['id'])
        
        for recipient_id in recipient_ids:
            recipient = await get_user_by_id(recipient_id)
            if not recipient:
                # Try clients collection
                recipient = await db.clients.find_one({"id": recipient_id}, {"_id": 0})
            if not recipient:
                # Try contractors collection
                recipient = await db.contractors.find_one({"id": recipient_id}, {"_id": 0})
            if not recipient:
                logger.warning(f"Drawing issued: Recipient not found: {recipient_id}")
                continue
            
            recipient_name = recipient.get('name', recipient.get('contact_person', 'User'))
            recipient_phone = recipient.get('mobile', recipient.get('phone'))
            recipient_role = recipient.get('role', recipient.get('contractor_type', ''))
            
            # Use template notification service
            if template_notification_service and recipient_phone:
                # Check if recipient is a contractor
                is_contractor = recipient_role in ['contractor'] or recipient.get('contractor_type')
                
                if is_contractor:
                    # Use contractor-specific template
                    await template_notification_service.notify_drawing_issued_contractor(
                        phone_number=recipient_phone,
                        contractor_name=recipient_name,
                        project_name=project_name,
                        drawing_name=drawing_name,
                        revision=revision,
                        contractor_type=recipient.get('contractor_type', 'Contractor'),
                        contractor_id=recipient_id,
                        project_id=project_id,
                        drawing_id=drawing_id
                    )
                else:
                    # Use general drawing issued template
                    await template_notification_service.notify_drawing_issued(
                        phone_number=recipient_phone,
                        recipient_name=recipient_name,
                        project_name=project_name,
                        drawing_name=drawing_name,
                        issue_date=issue_date,
                        recipient_id=recipient_id,
                        project_id=project_id,
                        drawing_id=drawing_id
                    )
            
            # Send in-app notification
            await notification_service.create_in_app_notification(
                user_id=recipient_id,
                title=f"Drawing Issued: {drawing_name}",
                message=f"Drawing '{drawing_name}' for project '{project_name}' has been issued.",
                notification_type="drawing_issued",
                link=f"/projects/{project_id}/drawing/{drawing_id}",
                project_id=project_id
            )
        
        logger.info(f"Drawing issued notifications sent for {drawing_name} to {len(recipient_ids)} recipients")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_issued: {str(e)}")


# ============================================
# 10. COMMENT ON DRAWING
# ============================================
async def notify_drawing_comment(
    project_id: str,
    drawing_id: str,
    commenter_id: str,
    comment_text: str,
    recipient_ids: List[str]
):
    """
    Trigger: Comment is made on drawing
    Recipients: Selected recipients + Owner (mandatory)
    Channels: WhatsApp
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        commenter = await get_user_by_id(commenter_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, commenter, owner]):
            return
        
        # Ensure owner is in recipients
        if owner['id'] not in recipient_ids:
            recipient_ids.append(owner['id'])
        
        # Remove commenter from recipients (don't notify themselves)
        recipient_ids = [r for r in recipient_ids if r != commenter_id]
        
        for recipient_id in recipient_ids:
            recipient = await get_user_by_id(recipient_id)
            if not recipient:
                continue
            
            is_client = recipient.get('role') == 'client'
            
            if is_client:
                # Formal message for client
                message = f"""Dear {recipient.get('name')},

A comment has been added to a drawing in your project "{project.get('title') or project.get('name')}".

📐 Drawing: {drawing.get('name')}
👤 Comment by: {commenter.get('name')}
💬 Comment: "{comment_text[:100]}..."

Please review the comment using the link below:
{APP_URL}/projects/{project_id}/drawing/{drawing_id}

Best regards,
4th Dimension Architects"""
            else:
                # Casual message for team
                message = f"""💬 New Comment on Drawing

📁 {project.get('title') or project.get('name')}
📐 {drawing.get('name')}
👤 {commenter.get('name')}: "{comment_text[:100]}..."

View: {APP_URL}/projects/{project_id}/drawing/{drawing_id}"""
            
            await notification_service.send_notification(
                user_ids=[recipient_id],
                title=f"Comment: {drawing.get('name')}",
                message=message,
                notification_type="drawing_comment",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawing/{drawing_id}",
                project_id=project_id
            )
        
        logger.info("Drawing comment notifications sent")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_comment: {str(e)}")


# ============================================
# 11. FEES PAID (by Client)
# ============================================
async def notify_fees_paid_by_client(project_id: str, amount: float, payment_mode: str, client_id: str):
    """
    Trigger: Client marks fees as paid
    Recipients: Owner
    Channels: WhatsApp
    Note: Requires client dashboard module
    """
    try:
        project = await get_project_by_id(project_id)
        client = await get_user_by_id(client_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, client, owner]):
            return
        
        message = f"""💰 Payment Notification

📁 Project: {project.get('title') or project.get('name')}
👤 Client: {client.get('name')}
💵 Amount: ₹{amount:,.2f}
💳 Mode: {payment_mode.title()}
📅 Date: {datetime.now(timezone.utc).strftime('%d %b %Y')}

Status: Client has marked this payment as made
Action: Please verify and confirm receipt

View: {APP_URL}/accounting"""
        
        await notification_service.send_notification(
            user_ids=[owner['id']],
            title="Payment Notification",
            message=message,
            notification_type="fees_paid_client",
            channels=['in_app', 'whatsapp'],
            link="/accounting",
            project_id=project_id
        )
        
        logger.info(f"Fees paid notification sent for project {project.get('title') or project.get('name')}")
        
    except Exception as e:
        logger.error(f"Error in notify_fees_paid_by_client: {str(e)}")


# ============================================
# 12. FEES RECEIVED (by Owner)
# ============================================
async def notify_fees_received_by_owner(
    project_id: str,
    amount: float,
    payment_mode: str,
    client_id: str,
    invoice_url: Optional[str] = None
):
    """
    Trigger: Owner records fees received
    Recipients: Owner, Client
    Channels: WhatsApp (for cash), Email with invoice (for cheque/online)
    """
    try:
        project = await get_project_by_id(project_id)
        client = await get_user_by_id(client_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, client, owner]):
            return
        
        payment_date = datetime.now(timezone.utc).strftime('%d %b %Y')
        
        # Client notification (formal)
        client_message = f"""Dear {client.get('name')},

Thank you for your payment for project "{project.get('title') or project.get('name')}".

💵 Amount Received: ₹{amount:,.2f}
💳 Payment Mode: {payment_mode.title()}
📅 Date: {payment_date}

Your payment has been successfully recorded in our system.

For any queries, please contact us.

Best regards,
4th Dimension Architects"""
        
        # Send to client
        if payment_mode.lower() in ['cheque', 'online', 'bank transfer']:
            # Send email with invoice
            if invoice_url:
                email_html = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2>Payment Receipt</h2>
                        <p>{client_message.replace(chr(10), '<br>')}</p>
                        <p><a href="{invoice_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">Download Invoice</a></p>
                    </body>
                </html>
                """
                
                await notification_service.send_email(
                    to_email=client.get('email'),
                    subject=f"Payment Receipt - {project.get('title') or project.get('name')}",
                    html_content=email_html
                )
        else:
            # Send WhatsApp for cash
            if client.get('mobile'):
                await notification_service.send_whatsapp(client['mobile'], client_message)
        
        # Owner notification
        owner_message = f"""✅ Payment Received

📁 Project: {project.get('title') or project.get('name')}
👤 Client: {client.get('name')}
💵 Amount: ₹{amount:,.2f}
💳 Mode: {payment_mode.title()}
📅 Date: {payment_date}

View: {APP_URL}/accounting"""
        
        if owner.get('mobile'):
            await notification_service.send_whatsapp(owner['mobile'], owner_message)
        
        await notification_service.create_in_app_notification(
            user_id=owner['id'],
            title="Payment Received",
            message=owner_message,
            notification_type="fees_received",
            link="/accounting",
            project_id=project_id
        )
        
        logger.info(f"Fees received notifications sent for project {project.get('title') or project.get('name')}")
        
    except Exception as e:
        logger.error(f"Error in notify_fees_received_by_owner: {str(e)}")


# ============================================
# 13. PROJECT TEAM ASSIGNMENT
# ============================================
async def notify_project_assignment(
    project: Dict,
    person_id: str,
    person_type: str,  # 'contractor', 'consultant', 'co_client'
    role_type: str  # 'Civil', 'Structural', 'Spouse', etc.
):
    """
    Trigger: Contractor/Consultant/Co-Client assigned to project
    Recipients: The assigned person
    Channels: WhatsApp, SMS (fallback), Email
    """
    try:
        project_title = project.get('title') or project.get('name', 'Untitled Project')
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        owner_name = owner.get('name', '4th Dimension Architects') if owner else '4th Dimension Architects'
        
        # Get person details based on type
        person = None
        collection = None
        
        if person_type == 'contractor':
            person = await db.contractors.find_one({"id": person_id}, {"_id": 0})
            collection = 'contractors'
        elif person_type == 'consultant':
            person = await db.consultants.find_one({"id": person_id}, {"_id": 0})
        elif person_type == 'co_client':
            person = await db.co_clients.find_one({"id": person_id}, {"_id": 0})
        
        if not person:
            logger.warning(f"Person not found: {person_type} {person_id}")
            return
        
        person_name = person.get('name', 'Team Member')
        person_phone = person.get('phone') or person.get('mobile')
        person_email = person.get('email')
        
        # Create appropriate message based on person type
        if person_type == 'contractor':
            whatsapp_message = f"""🏗️ *New Project Assignment*

Hi {person_name}!

You have been assigned as *{role_type} Contractor* for the following project:

📁 *Project:* {project_title}
📍 *Location:* {project.get('site_address', 'As per discussion')}
👔 *Firm:* 4th Dimension Architects

*What's Next?*
• Log in to the 4D portal to view project details and drawings
• You'll receive notifications for relevant updates
• Contact us for any queries

Portal: {APP_URL}

Looking forward to a successful collaboration!

Best regards,
{owner_name}
_4th Dimension Architects_"""
            
            email_subject = f"Project Assignment - {role_type} Contractor for {project_title}"
            
        elif person_type == 'consultant':
            whatsapp_message = f"""🔬 *Consultant Engagement*

Dear {person_name},

We are pleased to engage you as *{role_type} Consultant* for:

📁 *Project:* {project_title}
📍 *Location:* {project.get('site_address', 'As per discussion')}
👔 *Firm:* 4th Dimension Architects

*Your Role:*
• Provide {role_type.lower()} design and consultation
• Review and approve relevant drawings
• Coordinate with the project team

Portal Access: {APP_URL}

We look forward to your expert guidance on this project.

Warm regards,
{owner_name}
_4th Dimension Architects_"""
            
            email_subject = f"Consultant Engagement - {role_type} for {project_title}"
            
        else:  # co_client
            relationship = person.get('relationship', 'Associate')
            client = await db.users.find_one({"id": project.get('client_id')}, {"_id": 0})
            client_name = client.get('name', 'the client') if client else 'the client'
            
            whatsapp_message = f"""🏠 *Project Access Granted*

Hi {person_name}!

{client_name} has added you as *{relationship}* to their project:

📁 *Project:* {project_title}
📍 *Location:* {project.get('site_address', 'Your property')}

*As an associate, you can:*
• View all project drawings and updates
• Add comments and feedback
• Track project progress

Log in to view: {APP_URL}

Welcome aboard!

Best regards,
_4th Dimension Architects_"""
            
            email_subject = f"Project Access - {project_title}"
        
        # Send WhatsApp notification
        whatsapp_sent = False
        if person_phone:
            try:
                # For project assignment, try freeform message first (works if within 24hr window)
                # This is different from registration - they're already in the system
                result = await notification_service.send_whatsapp(person_phone, whatsapp_message)
                whatsapp_sent = result.get('success', False)
                
                if not whatsapp_sent:
                    logger.info(f"Freeform WhatsApp failed for {person_name}, trying SMS fallback")
                    
            except Exception as e:
                logger.warning(f"WhatsApp failed for {person_name}: {str(e)}")
        
        # Send SMS if WhatsApp failed
        if not whatsapp_sent and person_phone:
            sms_message = f"""Hi {person_name}! You've been assigned as {role_type} {person_type.replace('_', ' ').title()} for project "{project_title}" at 4th Dimension Architects. 

View project details: {APP_URL}

- 4th Dimension Architects"""
            await notification_service.send_sms(person_phone, sms_message)
        
        # Send Email
        if person_email:
            email_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .highlight {{ background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{'🏗️ Project Assignment' if person_type == 'contractor' else '🔬 Consultant Engagement' if person_type == 'consultant' else '🏠 Project Access'}</h1>
                    </div>
                    <div class="content">
                        <p>Dear {person_name},</p>
                        
                        <div class="highlight">
                            <p><strong>{'You have been assigned as' if person_type == 'contractor' else 'You have been engaged as' if person_type == 'consultant' else 'You have been added as'}:</strong> {role_type} {person_type.replace('_', ' ').title()}</p>
                            <p><strong>Project:</strong> {project_title}</p>
                            <p><strong>Location:</strong> {project.get('site_address', 'As per discussion')}</p>
                        </div>
                        
                        <p>Please log in to the 4D Architects portal to view project details, drawings, and updates.</p>
                        
                        <center>
                            <a href="{APP_URL}" class="button">Access Portal</a>
                        </center>
                        
                        <div class="footer">
                            <p>Best regards,<br><strong>{owner_name}</strong><br>4th Dimension Architects</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            await notification_service.send_email(
                to_email=person_email,
                subject=email_subject,
                html_content=email_html
            )
        
        logger.info(f"Project assignment notification sent to {person_name} ({person_type})")
        
    except Exception as e:
        logger.error(f"Error in notify_project_assignment: {str(e)}")


# ============================================
# PROJECT COMMENT NOTIFICATIONS
# ============================================

async def notify_project_comment(
    project_id: str,
    comment_id: str,
    commenter_name: str,
    comment_preview: str
):
    """
    Notify owner and team leader when a new project comment is posted.
    Typically from clients/contractors/consultants.
    Uses WhatsApp template for reliable delivery.
    """
    try:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        project_name = project.get('title', 'Project')
        
        # Notify owner using template
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if owner:
            if template_notification_service and owner.get('mobile'):
                await template_notification_service.notify_new_comment(
                    phone_number=owner['mobile'],
                    recipient_name=owner.get('name', 'Admin'),
                    commenter_name=commenter_name,
                    project_name=project_name,
                    comment_preview=comment_preview[:100],
                    recipient_id=owner['id'],
                    project_id=project_id
                )
            else:
                # Fallback to in-app notification
                await notification_service.create_in_app_notification(
                    user_id=owner['id'],
                    title="New Project Comment",
                    message=f"💬 {commenter_name} commented on {project_name}: {comment_preview[:50]}...",
                    notification_type="project_comment",
                    link=f"/projects/{project_id}",
                    project_id=project_id
                )
        
        # Notify team leader if different from owner
        if project.get('team_leader_id'):
            team_leader = await db.users.find_one(
                {"id": project['team_leader_id']},
                {"_id": 0}
            )
            if team_leader and team_leader.get('id') != owner.get('id'):
                if template_notification_service and team_leader.get('mobile'):
                    await template_notification_service.notify_new_comment(
                        phone_number=team_leader['mobile'],
                        recipient_name=team_leader.get('name'),
                        commenter_name=commenter_name,
                        project_name=project_name,
                        comment_preview=comment_preview[:100],
                        recipient_id=team_leader['id'],
                        project_id=project_id
                    )
                else:
                    await notification_service.create_in_app_notification(
                        user_id=team_leader['id'],
                        title="New Project Comment",
                        message=f"💬 {commenter_name} commented on {project_name}",
                        notification_type="project_comment",
                        link=f"/projects/{project_id}",
                        project_id=project_id
                    )
        
        logger.info(f"Project comment notification sent for {project_name}")
        
    except Exception as e:
        logger.error(f"Error in notify_project_comment: {str(e)}")


# ============================================
# DRAWING NOTIFICATIONS - Owner WhatsApp Alerts
# ============================================

async def get_owner_info() -> Optional[Dict]:
    """Get owner user info"""
    return await db.users.find_one({"is_owner": True}, {"_id": 0})


async def notify_owner_drawing_uploaded(
    drawing_id: str,
    drawing_name: str,
    project_id: str,
    uploaded_by_name: str
):
    """
    Notify owner when a drawing is uploaded for review
    Uses template-based WhatsApp for reliable delivery
    Uses magic links for secure one-click authentication
    """
    try:
        owner = await get_owner_info()
        if not owner or not owner.get('mobile'):
            logger.warning("Owner not found or no mobile number for drawing upload notification")
            return
        
        project = await get_project_by_id(project_id)
        project_name = project.get('title', 'Unknown Project') if project else 'Unknown Project'
        
        # Generate magic link for secure auto-login
        deep_link = await get_magic_link_for_project(
            recipient_id=owner['id'],
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        # Use template-based notification
        try:
            from template_notification_service import template_notification_service
            
            result = await template_notification_service.notify_drawing_uploaded(
                phone_number=owner['mobile'],
                recipient_name=owner.get('name', 'Sir/Madam'),
                project_name=project_name,
                drawing_name=drawing_name,
                uploader_name=uploaded_by_name,
                portal_url=deep_link
            )
            
            if result.get('success'):
                logger.info(f"Owner notified of drawing upload (template): {drawing_name}")
            else:
                # Fallback to SMS
                sms_msg = f"New drawing '{drawing_name}' uploaded for '{project_name}' by {uploaded_by_name}. View: {deep_link}"
                await notification_service.send_sms(owner['mobile'], sms_msg)
                
        except ImportError:
            # Fallback to freeform
            message = f"""📤 *Drawing Uploaded for Review*

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
👤 *Uploaded by:* {uploaded_by_name}

Please review: {deep_link}"""
            await notification_service.send_whatsapp(owner['mobile'], message)
            
    except Exception as e:
        logger.error(f"Error notifying owner of drawing upload: {str(e)}")


async def notify_owner_drawing_issued(
    drawing_id: str,
    drawing_name: str,
    project_id: str,
    issued_by_name: str,
    revision_number: int = 0
):
    """
    Notify owner when a drawing is issued
    Uses template-based WhatsApp for reliable delivery
    Uses magic links for secure one-click authentication
    """
    try:
        owner = await get_owner_info()
        if not owner or not owner.get('mobile'):
            logger.warning("Owner not found or no mobile number for drawing issue notification")
            return
        
        project = await get_project_by_id(project_id)
        project_name = project.get('title', 'Unknown Project') if project else 'Unknown Project'
        
        revision_text = f" (R{revision_number})" if revision_number > 0 else ""
        
        # Generate magic link for secure auto-login
        deep_link = await get_magic_link_for_project(
            recipient_id=owner['id'],
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        # Use template-based notification
        try:
            from template_notification_service import template_notification_service
            
            result = await template_notification_service.notify_drawing_issued(
                phone_number=owner['mobile'],
                recipient_name=owner.get('name', 'Sir/Madam'),
                project_name=project_name,
                drawing_name=f"{drawing_name}{revision_text}",
                issue_date=datetime.now(timezone.utc).strftime('%d %b %Y'),
                portal_url=deep_link
            )
            
            if result.get('success'):
                logger.info(f"Owner notified of drawing issue (template): {drawing_name}")
            else:
                # Fallback to SMS
                sms_msg = f"Drawing '{drawing_name}{revision_text}' has been issued for '{project_name}'. View: {deep_link}"
                await notification_service.send_sms(owner['mobile'], sms_msg)
                
        except ImportError:
            # Fallback to freeform
            message = f"""✅ *Drawing Issued*

📁 *Drawing:* {drawing_name}{revision_text}
🏗️ *Project:* {project_name}
👤 *Issued by:* {issued_by_name}

View: {deep_link}"""
            await notification_service.send_whatsapp(owner['mobile'], message)
            
    except Exception as e:
        logger.error(f"Error notifying owner of drawing issue: {str(e)}")


async def notify_owner_drawing_comment(
    drawing_id: str,
    drawing_name: str,
    project_id: str,
    commenter_name: str,
    comment_text: str,
    requires_revision: bool = False
):
    """
    Notify owner when a comment is added on a drawing
    Uses template-based WhatsApp for reliable delivery
    Uses magic links for secure one-click authentication
    """
    try:
        owner = await get_owner_info()
        if not owner or not owner.get('mobile'):
            logger.warning("Owner not found or no mobile number for drawing comment notification")
            return
        
        # Don't notify owner if they made the comment
        if commenter_name == owner.get('name'):
            return
        
        project = await get_project_by_id(project_id)
        project_name = project.get('title', 'Unknown Project') if project else 'Unknown Project'
        
        # Truncate comment if too long
        comment_preview = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
        
        # Generate magic link for secure auto-login
        deep_link = await get_magic_link_for_project(
            recipient_id=owner['id'],
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        # Use template-based notification
        try:
            from template_notification_service import template_notification_service
            
            if requires_revision:
                # Use revision_requested template - parameter names differ
                result = await template_notification_service.notify_revision_requested(
                    phone_number=owner['mobile'],
                    team_leader_name=owner.get('name', 'Sir/Madam'),
                    project_name=project_name,
                    drawing_name=drawing_name,
                    requester_name=commenter_name,
                    reason=comment_preview
                )
            else:
                # Use new_comment template - parameter names differ
                result = await template_notification_service.notify_new_comment(
                    phone_number=owner['mobile'],
                    recipient_name=owner.get('name', 'Sir/Madam'),
                    commenter_name=commenter_name,
                    project_name=project_name,
                    comment_preview=comment_preview
                )
            
            if result.get('success'):
                logger.info(f"Owner notified of drawing comment (template): {drawing_name}")
            else:
                # Fallback to SMS
                sms_msg = f"New comment on '{drawing_name}' from {commenter_name}: {comment_preview[:50]}... View: {deep_link}"
                await notification_service.send_sms(owner['mobile'], sms_msg)
                
        except ImportError:
            # Fallback to freeform
            revision_alert = "\n⚠️ *REVISION REQUESTED*" if requires_revision else ""
            message = f"""💬 *New Comment on Drawing*{revision_alert}

📁 *Drawing:* {drawing_name}
🏗️ *Project:* {project_name}
👤 *From:* {commenter_name}

📝 "{comment_preview}"

View & respond: {deep_link}"""
            await notification_service.send_whatsapp(owner['mobile'], message)
            
    except Exception as e:
        logger.error(f"Error notifying owner of drawing comment: {str(e)}")


async def notify_owner_drawing_revision_posted(
    drawing_id: str,
    drawing_name: str,
    project_id: str,
    posted_by_name: str,
    revision_number: int
):
    """
    Notify owner when a revised drawing is posted
    Uses template-based WhatsApp for reliable delivery
    Uses magic links for secure one-click authentication
    """
    try:
        owner = await get_owner_info()
        if not owner or not owner.get('mobile'):
            logger.warning("Owner not found or no mobile number for revision notification")
            return
        
        project = await get_project_by_id(project_id)
        project_name = project.get('title', 'Unknown Project') if project else 'Unknown Project'
        
        # Generate magic link for secure auto-login
        deep_link = await get_magic_link_for_project(
            recipient_id=owner['id'],
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        # Use template-based notification
        try:
            from template_notification_service import template_notification_service
            
            result = await template_notification_service.notify_drawing_revised(
                phone_number=owner['mobile'],
                recipient_name=owner.get('name', 'Sir/Madam'),
                project_name=project_name,
                drawing_name=f"{drawing_name}",
                revision=str(revision_number),
                updater_name=posted_by_name,
                portal_url=deep_link
            )
            
            if result.get('success'):
                logger.info(f"Owner notified of drawing revision (template): {drawing_name} R{revision_number}")
            else:
                # Fallback to SMS
                sms_msg = f"Revised drawing '{drawing_name}' (R{revision_number}) posted for '{project_name}' by {posted_by_name}. View: {deep_link}"
                await notification_service.send_sms(owner['mobile'], sms_msg)
                
        except ImportError:
            # Fallback to freeform
            message = f"""🔄 *Revised Drawing Posted*

📁 *Drawing:* {drawing_name} (R{revision_number})
🏗️ *Project:* {project_name}
👤 *Revised by:* {posted_by_name}

View & approve: {deep_link}"""
            await notification_service.send_whatsapp(owner['mobile'], message)
            
    except Exception as e:
        logger.error(f"Error notifying owner of drawing revision: {str(e)}")
