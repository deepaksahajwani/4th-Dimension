"""
WhatsApp Notification Service for 4th Dimension Architecture Firm
Handles all WhatsApp alerts via Twilio
"""

import os
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class WhatsAppNotificationService:
    """Service for sending WhatsApp notifications via Twilio"""
    
    def __init__(self):
        """Initialize Twilio client with credentials from environment"""
        # Use os.environ instead of os.getenv to ensure .env is loaded
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not found - WhatsApp notifications will be disabled")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info(f"✅ WhatsApp Notification Service initialized (Sandbox mode)")
                logger.info(f"   Using WhatsApp number: {self.whatsapp_number}")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                self.client = None
    
    def validate_indian_phone(self, phone_number: str) -> bool:
        """
        Validates that a phone number is a valid Indian mobile number.
        Accepts formats: +919876543210, 9876543210, 919876543210
        """
        normalized = phone_number.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        
        # Check E.164 format: +91 followed by 10 digits starting with 6, 7, 8, or 9
        pattern = r"^\+91[6-9]\d{9}$"
        if re.match(pattern, normalized):
            return True
        
        # Check without + sign
        pattern = r"^91[6-9]\d{9}$"
        if re.match(pattern, normalized):
            return True
        
        # Check 10-digit format
        pattern = r"^[6-9]\d{9}$"
        if re.match(pattern, normalized):
            return True
        
        return False
    
    def normalize_indian_phone(self, phone_number: str) -> Optional[str]:
        """
        Converts various Indian phone number formats to WhatsApp E.164 format.
        Returns format: whatsapp:+919876543210
        """
        if not phone_number:
            return None
        
        # Remove common formatting characters
        normalized = phone_number.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        
        # Remove whatsapp: prefix if present
        if normalized.startswith("whatsapp:"):
            normalized = normalized.replace("whatsapp:", "")
        
        # If it starts with 0, remove it and add +91
        if normalized.startswith("0"):
            normalized = "+91" + normalized[1:]
        
        # If it doesn't start with +, add +91
        if not normalized.startswith("+"):
            if len(normalized) == 10:
                normalized = "+91" + normalized
            elif len(normalized) == 12 and normalized.startswith("91"):
                normalized = "+" + normalized
        
        # Validate the result
        if self.validate_indian_phone(normalized):
            return f"whatsapp:{normalized}" if not normalized.startswith("whatsapp:") else normalized
        
        logger.error(f"Invalid phone number format: {phone_number}")
        return None
    
    def send_message(
        self,
        to_number: str,
        message_body: str,
        media_url: Optional[str] = None
    ) -> Dict:
        """
        Send a WhatsApp message to a recipient.
        
        Args:
            to_number: Recipient phone number (will be normalized)
            message_body: Text message content
            media_url: Optional URL to media file (image, PDF, etc.)
        
        Returns:
            Dict with success status and message details
        """
        if not self.client:
            logger.warning("WhatsApp client not initialized - message not sent")
            return {
                "success": False,
                "error": "WhatsApp service not configured"
            }
        
        try:
            # Normalize phone number
            normalized_number = self.normalize_indian_phone(to_number)
            if not normalized_number:
                return {
                    "success": False,
                    "error": f"Invalid phone number format: {to_number}"
                }
            
            # Prepare message parameters
            message_params = {
                "from_": self.whatsapp_number,
                "to": normalized_number,
                "body": message_body
            }
            
            # Add media if provided
            if media_url:
                message_params["media_url"] = [media_url]
            
            # Send message
            message = self.client.messages.create(**message_params)
            
            logger.info(f"WhatsApp message sent successfully. SID: {message.sid}, To: {normalized_number}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio error sending WhatsApp message: {e.msg} (Code: {e.code})")
            return {
                "success": False,
                "error": e.msg,
                "error_code": e.code
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_bulk_messages(
        self,
        recipients: List[str],
        message_body: str,
        media_url: Optional[str] = None
    ) -> Dict:
        """
        Send the same message to multiple recipients.
        
        Args:
            recipients: List of phone numbers
            message_body: Message content
            media_url: Optional media URL
        
        Returns:
            Dict with success/failure counts and details
        """
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for phone_number in recipients:
            result = self.send_message(phone_number, message_body, media_url)
            
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "phone": phone_number,
                "status": "sent" if result["success"] else "failed",
                "message_sid": result.get("message_sid"),
                "error": result.get("error")
            })
        
        logger.info(f"Bulk message sent: {results['success']}/{results['total']} successful")
        return results


# Create a singleton instance
whatsapp_service = WhatsAppNotificationService()


# ============================================================================
# Notification Templates - Pre-defined messages for different events
# ============================================================================

class NotificationTemplates:
    """Pre-defined message templates for different notification types"""
    
    @staticmethod
    def user_registered(user_name: str, user_role: str) -> str:
        """New user registration notification for owner"""
        return (
            f"🔔 *New User Registration*\n\n"
            f"Name: {user_name}\n"
            f"Role: {user_role}\n\n"
            f"Please review and approve in the Admin Panel."
        )
    
    @staticmethod
    def user_approved(user_name: str) -> str:
        """User approval confirmation"""
        return (
            f"✅ *Welcome to 4th Dimension!*\n\n"
            f"Hello {user_name},\n\n"
            f"Your account has been approved! You can now login and access all features.\n\n"
            f"Thank you for joining our team!"
        )
    
    @staticmethod
    def drawing_uploaded(project_name: str, drawing_name: str, uploaded_by: str) -> str:
        """Drawing uploaded/updated notification"""
        return (
            f"📐 *New Drawing Upload*\n\n"
            f"Project: {project_name}\n"
            f"Drawing: {drawing_name}\n"
            f"Uploaded by: {uploaded_by}\n\n"
            f"Login to review the drawing."
        )
    
    @staticmethod
    def new_comment(project_name: str, commenter_name: str, comment_preview: str) -> str:
        """New comment notification"""
        preview = comment_preview[:50] + "..." if len(comment_preview) > 50 else comment_preview
        return (
            f"💬 *New Comment*\n\n"
            f"Project: {project_name}\n"
            f"From: {commenter_name}\n"
            f"Comment: {preview}\n\n"
            f"Login to view and reply."
        )
    
    @staticmethod
    def task_assigned(task_name: str, project_name: str, deadline: str) -> str:
        """Task assignment notification"""
        return (
            f"📋 *New Task Assigned*\n\n"
            f"Task: {task_name}\n"
            f"Project: {project_name}\n"
            f"Deadline: {deadline}\n\n"
            f"Login to view task details."
        )
    
    @staticmethod
    def task_deadline_approaching(task_name: str, project_name: str, hours_remaining: int) -> str:
        """Task deadline reminder"""
        return (
            f"⏰ *Task Deadline Approaching*\n\n"
            f"Task: {task_name}\n"
            f"Project: {project_name}\n"
            f"Time Remaining: {hours_remaining} hours\n\n"
            f"Please complete the task soon!"
        )
    
    @staticmethod
    def milestone_completed(project_name: str, milestone_name: str) -> str:
        """Milestone completion notification"""
        return (
            f"🎉 *Milestone Completed!*\n\n"
            f"Project: {project_name}\n"
            f"Milestone: {milestone_name}\n\n"
            f"Congratulations on reaching this milestone!"
        )
    
    @staticmethod
    def payment_due(project_name: str, amount: str, due_date: str) -> str:
        """Payment due notification"""
        return (
            f"💰 *Payment Due*\n\n"
            f"Project: {project_name}\n"
            f"Amount: ₹{amount}\n"
            f"Due Date: {due_date}\n\n"
            f"Please process the payment."
        )
    
    @staticmethod
    def payment_received(project_name: str, amount: str, payer_name: str) -> str:
        """Payment received confirmation"""
        return (
            f"✅ *Payment Received*\n\n"
            f"Project: {project_name}\n"
            f"Amount: ₹{amount}\n"
            f"From: {payer_name}\n\n"
            f"Payment has been recorded successfully."
        )
    
    @staticmethod
    def site_visit_scheduled(project_name: str, visit_date: str, visit_time: str) -> str:
        """Site visit notification"""
        return (
            f"📍 *Site Visit Scheduled*\n\n"
            f"Project: {project_name}\n"
            f"Date: {visit_date}\n"
            f"Time: {visit_time}\n\n"
            f"Please be present at the site."
        )
    
    @staticmethod
    def daily_progress_report(date: str, projects_count: int, tasks_completed: int, highlights: str) -> str:
        """Daily progress summary for owner"""
        return (
            f"📊 *Daily Progress Report - {date}*\n\n"
            f"Active Projects: {projects_count}\n"
            f"Tasks Completed: {tasks_completed}\n\n"
            f"Highlights:\n{highlights}\n\n"
            f"Keep up the great work!"
        )


# Create service instance - will initialize when imported (after .env is loaded)
whatsapp_service = WhatsAppNotificationService()

# Export for easy access
templates = NotificationTemplates()
