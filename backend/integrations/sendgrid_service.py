"""
SendGrid Integration Service

Dedicated layer for all email communications via SendGrid.
This service handles:
- Email sending
- Delivery tracking
- Error handling and logging
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, TrackingSettings, ClickTracking

logger = logging.getLogger(__name__)


class SendGridService:
    """
    Singleton service for SendGrid email communications.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@4thdimension.com')
        self.sender_name = os.environ.get('SENDER_NAME', '4th Dimension Architects')
        
        self.client = None
        if self.api_key:
            try:
                self.client = SendGridAPIClient(self.api_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {str(e)}")
        else:
            logger.warning("SendGrid API key not configured")
        
        self._initialized = True
    
    @property
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured"""
        return self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get SendGrid service status"""
        return {
            "service": "sendgrid",
            "configured": self.is_configured,
            "sender_email": self.sender_email,
            "sender_name": self.sender_name
        }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            plain_content: Plain text alternative (optional)
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional)
            
        Returns:
            Dict with success status and details
        """
        result = {
            "success": False,
            "channel": "email",
            "to": to_email,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": None,
            "error_message": None
        }
        
        if not self.is_configured:
            result["error_message"] = "SendGrid not configured"
            logger.warning("Email send failed: SendGrid not configured")
            return result
        
        try:
            # Create email with display name
            from_email = Email(self.sender_email, self.sender_name)
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Add plain text if provided
            if plain_content:
                message.add_content(plain_content, "text/plain")
            
            # Disable click tracking to prevent URL rewriting issues
            tracking_settings = TrackingSettings()
            tracking_settings.click_tracking = ClickTracking(enable=False, enable_text=False)
            message.tracking_settings = tracking_settings
            
            # Add CC recipients
            if cc:
                for cc_email in cc:
                    message.add_cc(cc_email)
            
            # Add BCC recipients
            if bcc:
                for bcc_email in bcc:
                    message.add_bcc(bcc_email)
            
            # Send the email
            response = self.client.send(message)
            
            result["success"] = True
            result["status_code"] = response.status_code
            
            logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"Email failed to {to_email}: {str(e)}")
        
        return result
    
    async def send_bulk_email(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        html_content: str
    ) -> Dict[str, Any]:
        """
        Send emails to multiple recipients.
        
        Args:
            recipients: List of dicts with 'email' and optional 'name'
            subject: Email subject
            html_content: HTML body content
            
        Returns:
            Dict with overall success and individual results
        """
        results = {
            "success": True,
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for recipient in recipients:
            email = recipient.get('email')
            if email:
                result = await self.send_email(email, subject, html_content)
                results["details"].append(result)
                if result["success"]:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["success"] = False
        
        return results


# Singleton instance
sendgrid_service = SendGridService()
