"""
Complete Notification Triggers - All 12 notification types
Implements the notification system as per the specification
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from notification_service import notification_service, message_templates, APP_URL
from email_templates import get_welcome_email_content

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


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
        user_id = user_data.get('id')
        
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
        
        if user_data.get('mobile'):
            await notification_service.send_whatsapp(user_data['mobile'], registrant_message)
        
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
    Channels: In-App, WhatsApp, Email
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return
        
        user_name = user.get('name')
        user_email = user.get('email')
        user_mobile = user.get('mobile')
        
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
        
        # Notify approved user (welcome)
        user_message = message_templates.user_approved_registrant(user_name)
        
        # Generate professional HTML email template (English only)
        login_url = f"{APP_URL}"
        email_subject, email_html = get_welcome_email_content(user, login_url)
        
        # Send WhatsApp notification
        if user_mobile:
            await notification_service.send_whatsapp(user_mobile, user_message)
        
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
    Channels: WhatsApp
    Message: Formal for client, casual for team
    """
    try:
        project = await get_project_by_id(project_id)
        if not project:
            return
        
        project_name = project.get('name')
        client_id = project.get('client_id')
        team_leader_id = project.get('team_leader_id')
        
        # Get client
        client = await get_user_by_id(client_id)
        if not client:
            logger.error(f"Client not found for project {project_id}")
            return
        
        # Get team leader
        team_leader = await get_user_by_id(team_leader_id)
        if not team_leader:
            logger.error(f"Team leader not found for project {project_id}")
            return
        
        # Get owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        # Message to client (formal)
        client_message = message_templates.project_created_client(
            client_name=client.get('name'),
            project_name=project_name,
            team_leader_name=team_leader.get('name'),
            team_leader_phone=team_leader.get('mobile', 'N/A')
        )
        
        # Send WhatsApp notification to client
        if client.get('mobile'):
            await notification_service.send_whatsapp(client['mobile'], client_message)
        
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
        
        if client.get('email'):
            await notification_service.send_email(
                to_email=client['email'],
                subject=email_subject,
                html_content=email_html
            )
        
        # Message to team leader (casual)
        team_message = message_templates.project_created_team(
            project_name=project_name,
            client_name=client.get('name'),
            client_phone=client.get('mobile', 'N/A')
        )
        
        # Notify team leader and owner
        await notification_service.send_notification(
            user_ids=[team_leader_id, owner['id']],
            title=f"New Project: {project_name}",
            message=team_message,
            notification_type="project_created",
            channels=['in_app', 'whatsapp'],
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
        
        project_name = project.get('name')
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
    Channels: WhatsApp
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        uploader = await get_user_by_id(uploaded_by_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, uploader, owner]):
            return
        
        message = f"""📤 Drawing Uploaded for Approval

📁 Project: {project.get('name')}
📐 Drawing: {drawing.get('name')}
👤 Uploaded by: {uploader.get('name')}
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
        
        logger.info(f"Drawing upload notification sent for {drawing.get('name')}")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_uploaded: {str(e)}")


# ============================================
# 6. DRAWING APPROVED
# ============================================
async def notify_drawing_approved(project_id: str, drawing_id: str):
    """
    Trigger: Drawing is approved
    Recipients: Team Leader
    Channels: WhatsApp
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
        
        message = f"""✅ Drawing Approved - Ready to Issue

📁 Project: {project.get('name')}
📐 Drawing: {drawing.get('name')}
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
        
        logger.info(f"Drawing approval notification sent for {drawing.get('name')}")
        
    except Exception as e:
        logger.error(f"Error in notify_drawing_approved: {str(e)}")


# ============================================
# 7. DRAWING REVISED (by Owner/Team Leader)
# ============================================
async def notify_drawing_revised_internal(project_id: str, drawing_id: str, revised_by_id: str):
    """
    Trigger: Drawing revised by owner or team leader
    Recipients: Team Leader
    Channels: WhatsApp
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
        
        message = f"""🔄 Drawing Revision Required

📁 Project: {project.get('name')}
📐 Drawing: {drawing.get('name')}
👤 Revised by: {revised_by.get('name')}

Please review the revision comments and update the drawing.

View Revision: {APP_URL}/projects/{project_id}/drawings/{drawing_id}"""
        
        await notification_service.send_notification(
            user_ids=[team_leader_id],
            title="Drawing Revision Request",
            message=message,
            notification_type="drawing_revised_internal",
            channels=['in_app', 'whatsapp'],
            link=f"/projects/{project_id}/drawings/{drawing_id}",
            project_id=project_id
        )
        
        logger.info(f"Internal drawing revision notification sent")
        
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

📁 Project: {project.get('name')}
📐 Drawing: {drawing.get('name')}
👤 Revised by: {revised_by.get('name')}

Please review the comments and take necessary action.

View Revision: {APP_URL}/projects/{project_id}/drawings/{drawing_id}"""
        
        recipients = [owner['id']]
        if team_leader_id:
            recipients.append(team_leader_id)
        
        await notification_service.send_notification(
            user_ids=recipients,
            title="External Drawing Revision",
            message=message,
            notification_type="drawing_revised_external",
            channels=['in_app', 'whatsapp'],
            link=f"/projects/{project_id}/drawings/{drawing_id}",
            project_id=project_id
        )
        
        logger.info(f"External drawing revision notification sent")
        
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
    Channels: WhatsApp
    Message: Formal for client, casual for team
    """
    try:
        project = await get_project_by_id(project_id)
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        issued_by = await get_user_by_id(issued_by_id)
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not all([project, drawing, issued_by, owner]):
            logger.error(f"Drawing issued notification failed: Missing data (project={project is not None}, drawing={drawing is not None})")
            return
        
        project_name = project.get('name')
        drawing_name = drawing.get('name')
        issue_date = datetime.now(timezone.utc).strftime('%d %b %Y')
        status = "Revised" if drawing.get('revision_number', 0) > 0 else "New"
        
        # Ensure owner is in recipients
        if owner['id'] not in recipient_ids:
            recipient_ids.append(owner['id'])
        
        recipient_names = []
        
        for recipient_id in recipient_ids:
            recipient = await get_user_by_id(recipient_id)
            if not recipient:
                logger.warning(f"Drawing issued: Recipient not found: {recipient_id}")
                continue
            
            recipient_names.append(recipient.get('name'))
            recipient_role = recipient.get('role', '')
            
            # Determine if client (formal) or team (casual)
            is_client = recipient_role == 'client'
            
            logger.info(f"[DRAWING ISSUED] Is client: {is_client}")
            
            if is_client:
                # Formal message for client
                message = message_templates.drawing_issued_client(
                    client_name=recipient.get('name'),
                    project_name=project_name,
                    drawing_name=drawing_name,
                    issue_date=issue_date,
                    status=status,
                    project_id=project_id,
                    drawing_id=drawing_id
                )
            else:
                # Casual message for team
                message = message_templates.drawing_issued_team(
                    project_name=project_name,
                    drawing_name=drawing_name,
                    status=status,
                    recipients=recipient_names,
                    project_id=project_id
                )
            
            logger.info(f"[DRAWING ISSUED] Message prepared: {message[:100]}...")
            logger.info(f"[DRAWING ISSUED] Calling send_notification with channels=['in_app', 'whatsapp']")
            
            # Send notification
            result = await notification_service.send_notification(
                user_ids=[recipient_id],
                title=f"Drawing Issued: {drawing_name}",
                message=message,
                notification_type="drawing_issued",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawings/{drawing_id}",
                project_id=project_id
            )
            
            logger.info(f"[DRAWING ISSUED] Notification result for {recipient.get('name')}: {result}")
        
        logger.info(f"[DRAWING ISSUED] All notifications completed for {drawing_name}")
        
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

A comment has been added to a drawing in your project "{project.get('name')}".

📐 Drawing: {drawing.get('name')}
👤 Comment by: {commenter.get('name')}
💬 Comment: "{comment_text[:100]}..."

Please review the comment using the link below:
{APP_URL}/projects/{project_id}/drawings/{drawing_id}#comment

Best regards,
4th Dimension Architects"""
            else:
                # Casual message for team
                message = f"""💬 New Comment on Drawing

📁 {project.get('name')}
📐 {drawing.get('name')}
👤 {commenter.get('name')}: "{comment_text[:100]}..."

View: {APP_URL}/projects/{project_id}/drawings/{drawing_id}#comment"""
            
            await notification_service.send_notification(
                user_ids=[recipient_id],
                title=f"Comment: {drawing.get('name')}",
                message=message,
                notification_type="drawing_comment",
                channels=['in_app', 'whatsapp'],
                link=f"/projects/{project_id}/drawings/{drawing_id}#comment",
                project_id=project_id
            )
        
        logger.info(f"Drawing comment notifications sent")
        
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

📁 Project: {project.get('name')}
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
        
        logger.info(f"Fees paid notification sent for project {project.get('name')}")
        
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

Thank you for your payment for project "{project.get('name')}".

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
                    subject=f"Payment Receipt - {project.get('name')}",
                    html_content=email_html
                )
        else:
            # Send WhatsApp for cash
            if client.get('mobile'):
                await notification_service.send_whatsapp(client['mobile'], client_message)
        
        # Owner notification
        owner_message = f"""✅ Payment Received

📁 Project: {project.get('name')}
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
        
        logger.info(f"Fees received notifications sent for project {project.get('name')}")
        
    except Exception as e:
        logger.error(f"Error in notify_fees_received_by_owner: {str(e)}")
