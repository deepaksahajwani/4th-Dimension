"""
Unified Notification Service - Handles all notification channels
Sends notifications via In-App, WhatsApp, and Email
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pathlib import Path
from dotenv import load_dotenv
from whatsapp_business_service import whatsapp_business_service

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# App URL
APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tasktracker-bugs.preview.emergentagent.com')

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

# SendGrid Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'contact@4thdimensionarchitect.com')


class NotificationService:
    """Unified notification service for all channels"""
    
    @staticmethod
    async def create_in_app_notification(
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        link: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Create in-app notification"""
        try:
            notification = {
                "id": f"notif_{datetime.now(timezone.utc).timestamp()}_{user_id}",
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "link": link,
                "project_id": project_id,
                "metadata": metadata or {},
                "read": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.notifications.insert_one(notification)
            logger.info(f"In-app notification created for user {user_id}: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating in-app notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_whatsapp_template(
        phone_number: str, 
        content_sid: str, 
        content_variables: Dict
    ) -> Dict:
        """
        Send WhatsApp message using approved template (required for business-initiated messages)
        
        Args:
            phone_number: Recipient phone number
            content_sid: Twilio Content SID (starts with HX)
            content_variables: Dict of template variables {"1": "value1", "2": "value2"}
        """
        try:
            if not phone_number:
                return {"success": False, "error": "Phone number is required"}
            
            logger.info(f"Sending WhatsApp template to {phone_number[:8]}...")
            
            # Format phone number for Twilio
            if phone_number.startswith('whatsapp:'):
                phone_number = phone_number[9:].strip()
            phone_number = phone_number.strip()
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            phone_number = f"whatsapp:{phone_number}"
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            
            import json
            data = {
                "From": TWILIO_WHATSAPP_FROM,
                "To": phone_number,
                "ContentSid": content_sid,
                "ContentVariables": json.dumps(content_variables)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"WhatsApp template sent to {phone_number}: {result.get('sid')}")
                    return {
                        "success": True,
                        "message_sid": result.get('sid'),
                        "status": result.get('status')
                    }
                else:
                    error_msg = response.text
                    logger.error(f"WhatsApp template failed to {phone_number}: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"WhatsApp template error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def send_whatsapp(phone_number: str, message: str) -> Dict:
        """
        Send WhatsApp message via WhatsApp Business API or Twilio (fallback)
        Uses WhatsApp Business API if USE_WHATSAPP_BUSINESS_API=true in .env
        NOTE: Freeform messages only work within 24-hour window after user initiates contact
        """
        try:
            if not phone_number:
                return {"success": False, "error": "Phone number is required"}
            
            # Check which service to use
            use_business_api = os.environ.get('USE_WHATSAPP_BUSINESS_API', 'false').lower() == 'true'
            
            if use_business_api:
                # Use WhatsApp Business API (Meta)
                logger.info(f"Using WhatsApp Business API for {phone_number[:8]}...")
                result = await whatsapp_business_service.send_message(phone_number, message)
                
                if result.get('success'):
                    logger.info(f"WhatsApp sent to {phone_number}: {result.get('message_id')}")
                else:
                    logger.error(f"WhatsApp Business API error: {result.get('error')}")
                
                return result
            else:
                # Fallback to Twilio
                logger.info(f"Using Twilio WhatsApp for {phone_number[:8]}...")
                
                # Format phone number for Twilio - ensure proper format
                # Remove any existing whatsapp: prefix first
                if phone_number.startswith('whatsapp:'):
                    phone_number = phone_number[9:].strip()
                
                # Strip any whitespace
                phone_number = phone_number.strip()
                
                # Ensure the phone number starts with +
                if not phone_number.startswith('+'):
                    # If it starts with a country code (like 91 for India), add +
                    phone_number = f"+{phone_number}"
                
                # Now add the whatsapp: prefix
                phone_number = f"whatsapp:{phone_number}"
                
                url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                
                data = {
                    "From": TWILIO_WHATSAPP_FROM,
                    "To": phone_number,
                    "Body": message
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        data=data,
                        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                        timeout=30.0
                    )
                    
                    if response.status_code == 201:
                        result = response.json()
                        logger.info(f"WhatsApp sent to {phone_number}: {result.get('sid')}")
                        return {
                            "success": True,
                            "message_sid": result.get('sid'),
                            "status": result.get('status')
                        }
                    else:
                        error_msg = response.text
                        logger.error(f"WhatsApp failed to {phone_number}: {error_msg}")
                        return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"WhatsApp error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid"""
        try:
            message = Mail(
                from_email=SENDER_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Email error: {str(e)}")
            return False
    
    @staticmethod
    async def send_notification(
        user_ids: List[str],
        title: str,
        message: str,
        notification_type: str,
        channels: List[str] = ['in_app', 'whatsapp'],
        link: Optional[str] = None,
        project_id: Optional[str] = None,
        email_subject: Optional[str] = None,
        email_html: Optional[str] = None
    ):
        """
        Send notification through multiple channels
        
        Args:
            user_ids: List of user IDs to notify
            title: Notification title
            message: Notification message (for WhatsApp and in-app)
            notification_type: Type of notification
            channels: List of channels ['in_app', 'whatsapp', 'email']
            link: Deep link for in-app notification
            project_id: Associated project ID
            email_subject: Email subject (if email channel is used)
            email_html: HTML content for email (if email channel is used)
        """
        results = []
        
        for user_id in user_ids:
            try:
                # Get user details
                user = await db.users.find_one({"id": user_id}, {"_id": 0})
                if not user:
                    logger.warning(f"User not found: {user_id}")
                    continue
                
                # In-app notification
                if 'in_app' in channels:
                    await NotificationService.create_in_app_notification(
                        user_id=user_id,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        link=link,
                        project_id=project_id
                    )
                
                # WhatsApp notification
                if 'whatsapp' in channels and user.get('mobile'):
                    result = await NotificationService.send_whatsapp(
                        phone_number=user['mobile'],
                        message=message
                    )
                    results.append({"user_id": user_id, "channel": "whatsapp", "result": result})
                elif 'whatsapp' in channels:
                    logger.warning(f"WhatsApp notification skipped: User {user_id} has no mobile number")
                
                # Email notification
                if 'email' in channels and user.get('email') and email_subject and email_html:
                    success = await NotificationService.send_email(
                        to_email=user['email'],
                        subject=email_subject,
                        html_content=email_html
                    )
                    results.append({"user_id": user_id, "channel": "email", "success": success})
                    
            except Exception as e:
                logger.error(f"Error sending notification to {user_id}: {str(e)}")
        
        return results


# Message template generators
class MessageTemplates:
    """Generate formal and casual message templates"""
    
    @staticmethod
    def format_formal(content: str) -> str:
        """Format message in formal tone for clients"""
        return content
    
    @staticmethod
    def format_casual(content: str) -> str:
        """Format message in casual tone for team"""
        return content
    
    @staticmethod
    def user_registration_owner(user_name: str, user_role: str, user_email: str) -> str:
        """Notification to owner about new registration"""
        return f"""🔔 New User Registration

👤 Name: {user_name}
📧 Email: {user_email}
🎯 Role: {user_role}
⏳ Status: Pending Approval

Please review and approve in the Pending Approvals section.

View: {APP_URL}/pending-registrations"""
    
    @staticmethod
    def user_registration_registrant(user_name: str) -> str:
        """Notification to registrant after registration"""
        return f"""Thank you for registering, {user_name}!

Your registration request has been submitted and is pending approval from the administrator.

You will receive a confirmation once your account is approved.

Best regards,
4th Dimension Architects"""
    
    @staticmethod
    def user_approved_owner(user_name: str) -> str:
        """Confirmation to owner after approving user"""
        return f"""✅ User Approved

{user_name} has been successfully approved and can now access the system."""
    
    @staticmethod
    def user_approved_registrant(user_name: str) -> str:
        """Welcome message to newly approved user"""
        return f"""Welcome to 4th Dimension, {user_name}!

Your account has been approved. You can now log in and start collaborating with the team.

Login: {APP_URL}

Best regards,
4th Dimension Architects"""
    
    @staticmethod
    def project_created_client(client_name: str, project_name: str, team_leader_name: str, team_leader_phone: str) -> str:
        """Formal message to client about new project"""
        return f"""Dear {client_name},

Your project "{project_name}" is now live on 4th Dimension!

✅ Track Progress: Monitor your project status in real-time
✅ View Drawings: Access and review all architectural drawings
✅ Stay Updated: Receive notifications on key milestones

Your Team Leader: {team_leader_name}
Contact: {team_leader_phone}

Login to your dashboard: {APP_URL}

For assistance, please feel free to contact us.

Best regards,
4th Dimension Architects"""
    
    @staticmethod
    def project_created_team(project_name: str, client_name: str, client_phone: str) -> str:
        """Casual message to team leader about new project"""
        return f"""🎉 New project assigned to you!

📁 Project: {project_name}
👤 Client: {client_name}
📞 Client Contact: {client_phone}

Your responsibilities:
• Manage drawings workflow
• Coordinate with team
• Keep client updated

View project: {APP_URL}/projects

Let's deliver excellence! 🚀"""
    
    @staticmethod
    def drawing_issued_client(client_name: str, project_name: str, drawing_name: str, 
                              issue_date: str, status: str, project_id: str, drawing_id: str) -> str:
        """Formal message to client about drawing issued"""
        return f"""Dear {client_name},

A drawing has been issued for your project "{project_name}".

📐 Drawing: {drawing_name}
📅 Issued Date: {issue_date}
📋 Status: {status}

Please review the drawing at your earliest convenience.

View Drawing: {APP_URL}/projects/{project_id}/drawings

For any comments, please click the link below to comment on the drawing:
💬 COMMENT: {APP_URL}/projects/{project_id}/drawings/{drawing_id}#comment

Best regards,
4th Dimension Architects"""
    
    @staticmethod
    def drawing_issued_team(project_name: str, drawing_name: str, status: str, 
                           recipients: List[str], project_id: str) -> str:
        """Casual message to team about drawing issued"""
        recipients_list = "\n".join([f"✓ {r}" for r in recipients])
        return f"""📐 Drawing Issued!

📁 {project_name}
🖼️ {drawing_name} - {status}

Recipients notified:
{recipients_list}

View: {APP_URL}/projects/{project_id}/drawings"""


class NotificationServiceSMS:
    """SMS sending capability - separate from main notification service"""
    
    @staticmethod
    async def send_sms(phone_number: str, message: str) -> Dict:
        """
        Send SMS via Twilio
        Use this for invitations since WhatsApp requires user opt-in first
        """
        try:
            if not phone_number:
                return {"success": False, "error": "Phone number is required"}
            
            logger.info(f"Sending SMS to {phone_number[:8]}...")
            
            # Format phone number
            phone_number = phone_number.strip()
            if phone_number.startswith('whatsapp:'):
                phone_number = phone_number[9:].strip()
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            
            # Get SMS phone number (not WhatsApp)
            sms_from = os.environ.get('TWILIO_PHONE_NUMBER', '+12066735535')
            
            data = {
                "From": sms_from,
                "To": phone_number,
                "Body": message
            }
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    url,
                    data=data,
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"SMS sent to {phone_number}: {result.get('sid')}")
                    return {
                        "success": True,
                        "message_sid": result.get('sid'),
                        "status": result.get('status')
                    }
                else:
                    error_msg = response.text
                    logger.error(f"SMS failed to {phone_number}: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"SMS error: {str(e)}")
            return {"success": False, "error": str(e)}


# Add send_sms to the main NotificationService class
NotificationService.send_sms = NotificationServiceSMS.send_sms

notification_service = NotificationService()
message_templates = MessageTemplates()
