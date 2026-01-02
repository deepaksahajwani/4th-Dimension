"""
Template-Based Notification Service

This service handles sending notifications using WhatsApp templates
with SMS fallback when templates fail or are pending approval.

Usage:
    from template_notification_service import send_template_notification
    
    await send_template_notification(
        template_key="drawing_issued",
        recipient_phone="+919876543210",
        recipient_name="John Doe",
        variables={
            "recipient_name": "John",
            "drawing_name": "Floor Plan",
            "project_name": "Villa Project",
            "revision": "R1",
            "portal_url": "https://..."
        }
    )
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from whatsapp_templates import (
    get_template, 
    is_template_approved, 
    WhatsAppTemplate,
    TemplateStatus
)

logger = logging.getLogger(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
TWILIO_SMS_FROM = os.environ.get('TWILIO_SMS_FROM')
APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://arch-manager-1.preview.emergentagent.com')


class TemplateNotificationService:
    """
    Service for sending template-based WhatsApp notifications with SMS fallback.
    """
    
    def __init__(self):
        self.twilio_client = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized for template notifications")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
    
    async def send_notification(
        self,
        template_key: str,
        recipient_phone: str,
        variables: Dict[str, str],
        recipient_id: Optional[str] = None,
        create_in_app: bool = True,
        in_app_title: Optional[str] = None,
        in_app_message: Optional[str] = None,
        in_app_link: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification using WhatsApp template with SMS fallback.
        
        Args:
            template_key: Key of the template in whatsapp_templates.py
            recipient_phone: Recipient phone number with country code
            variables: Dictionary of template variables
            recipient_id: User ID for in-app notification
            create_in_app: Whether to create in-app notification
            in_app_title: Title for in-app notification
            in_app_message: Message for in-app notification
            in_app_link: Link for in-app notification
            project_id: Project ID for context
            
        Returns:
            Dict with success status and details
        """
        result = {
            "success": False,
            "template_key": template_key,
            "recipient": recipient_phone,
            "whatsapp_sent": False,
            "sms_sent": False,
            "in_app_sent": False,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        template = get_template(template_key)
        if not template:
            result["error"] = f"Template '{template_key}' not found"
            logger.error(result["error"])
            return result
        
        # Try WhatsApp template first (if approved)
        if template.status == TemplateStatus.APPROVED and self.twilio_client:
            whatsapp_result = await self._send_whatsapp_template(
                template, 
                recipient_phone, 
                variables
            )
            result["whatsapp_sent"] = whatsapp_result.get("success", False)
            result["whatsapp_sid"] = whatsapp_result.get("message_sid")
            result["whatsapp_error"] = whatsapp_result.get("error")
        
        # Fallback to SMS if WhatsApp failed or template pending
        if not result["whatsapp_sent"]:
            sms_result = await self._send_sms_fallback(template, recipient_phone, variables)
            result["sms_sent"] = sms_result.get("success", False)
            result["sms_sid"] = sms_result.get("message_sid")
            result["sms_error"] = sms_result.get("error")
        
        # Create in-app notification
        if create_in_app and recipient_id:
            try:
                from notification_service import notification_service
                await notification_service.create_in_app_notification(
                    user_id=recipient_id,
                    title=in_app_title or template.description,
                    message=in_app_message or self._format_sms(template.fallback_sms, variables),
                    notification_type=template_key,
                    link=in_app_link,
                    project_id=project_id
                )
                result["in_app_sent"] = True
            except Exception as e:
                logger.error(f"In-app notification error: {str(e)}")
        
        # Log the notification
        await self._log_notification(result, template_key, variables)
        
        result["success"] = result["whatsapp_sent"] or result["sms_sent"] or result["in_app_sent"]
        return result
    
    async def _send_whatsapp_template(
        self,
        template: WhatsAppTemplate,
        phone: str,
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """Send WhatsApp template message via Twilio"""
        try:
            # Format phone number
            formatted_phone = phone if phone.startswith('whatsapp:') else f'whatsapp:{phone}'
            
            # Build content variables (numbered 1, 2, 3, etc.)
            content_vars = {}
            for i, var_name in enumerate(template.variables, 1):
                content_vars[str(i)] = variables.get(var_name, "")
            
            # Send via Twilio Content API
            message = self.twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=formatted_phone,
                content_sid=template.sid,
                content_variables=json.dumps(content_vars)
            )
            
            logger.info(f"WhatsApp template sent: {template.name} to {phone} - {message.sid}")
            return {"success": True, "message_sid": message.sid}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"WhatsApp template error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def _send_sms_fallback(
        self,
        template: WhatsAppTemplate,
        phone: str,
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """Send SMS fallback message"""
        if not TWILIO_SMS_FROM or not self.twilio_client:
            return {"success": False, "error": "SMS not configured"}
        
        try:
            # Remove whatsapp: prefix if present
            clean_phone = phone.replace('whatsapp:', '')
            
            # Format the SMS message
            sms_body = self._format_sms(template.fallback_sms, variables)
            
            message = self.twilio_client.messages.create(
                from_=TWILIO_SMS_FROM,
                to=clean_phone,
                body=sms_body
            )
            
            logger.info(f"SMS fallback sent to {phone} - {message.sid}")
            return {"success": True, "message_sid": message.sid}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMS fallback error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _format_sms(self, template: str, variables: Dict[str, str]) -> str:
        """Format SMS message with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable in SMS template: {e}")
            # Try partial formatting
            for key, value in variables.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
    
    async def _log_notification(
        self,
        result: Dict[str, Any],
        template_key: str,
        variables: Dict[str, str]
    ):
        """Log notification to database"""
        try:
            from integrations.notification_logger import notification_logger
            
            channel = "whatsapp_template" if result.get("whatsapp_sent") else "sms" if result.get("sms_sent") else "in_app"
            
            await notification_logger.log(
                notification_type=template_key,
                channel=channel,
                recipient=result.get("recipient", ""),
                success=result.get("success", False),
                error_message=result.get("whatsapp_error") or result.get("sms_error"),
                message_sid=result.get("whatsapp_sid") or result.get("sms_sid"),
                metadata={"variables": variables}
            )
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")


# Singleton instance
template_notification_service = TemplateNotificationService()


# Convenience function
async def send_template_notification(
    template_key: str,
    recipient_phone: str,
    variables: Dict[str, str],
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to send template notification.
    
    Example:
        await send_template_notification(
            template_key="drawing_issued",
            recipient_phone="+919876543210",
            variables={
                "recipient_name": "John",
                "drawing_name": "Floor Plan",
                "project_name": "Villa Project",
                "revision": "R1",
                "portal_url": "https://..."
            }
        )
    """
    return await template_notification_service.send_notification(
        template_key=template_key,
        recipient_phone=recipient_phone,
        variables=variables,
        **kwargs
    )
