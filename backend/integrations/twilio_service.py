"""
Twilio Integration Service

Dedicated layer for all Twilio WhatsApp and SMS communications.
This service handles:
- WhatsApp messaging via Twilio
- SMS fallback messaging
- Delivery status tracking
- Error handling and logging
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Singleton service for Twilio communications.
    Provides WhatsApp and SMS messaging capabilities.
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
            
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        self.sms_from = os.environ.get('TWILIO_SMS_FROM')
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
        else:
            logger.warning("Twilio credentials not configured")
        
        self._initialized = True
    
    @property
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured"""
        return self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get Twilio service status"""
        return {
            "service": "twilio",
            "configured": self.is_configured,
            "whatsapp_enabled": bool(self.whatsapp_from),
            "sms_enabled": bool(self.sms_from),
            "account_sid": self.account_sid[:10] + "..." if self.account_sid else None
        }
    
    async def send_whatsapp(
        self,
        to_number: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to_number: Recipient phone number (with country code)
            message: Message content
            media_url: Optional media attachment URL
            
        Returns:
            Dict with success status, message_sid, and error details if any
        """
        result = {
            "success": False,
            "channel": "whatsapp",
            "to": to_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_sid": None,
            "error_code": None,
            "error_message": None
        }
        
        if not self.is_configured:
            result["error_message"] = "Twilio not configured"
            logger.warning("WhatsApp send failed: Twilio not configured")
            return result
        
        try:
            # Format the phone number for WhatsApp
            formatted_to = to_number if to_number.startswith('whatsapp:') else f'whatsapp:{to_number}'
            
            # Prepare message parameters
            msg_params = {
                'from_': self.whatsapp_from,
                'to': formatted_to,
                'body': message
            }
            
            if media_url:
                msg_params['media_url'] = [media_url]
            
            # Send the message
            twilio_message = self.client.messages.create(**msg_params)
            
            result["success"] = True
            result["message_sid"] = twilio_message.sid
            result["status"] = twilio_message.status
            
            logger.info(f"WhatsApp sent to {to_number}: {twilio_message.sid}")
            
        except TwilioRestException as e:
            result["error_code"] = e.code
            result["error_message"] = self._get_friendly_error(e.code, str(e))
            logger.error(f"WhatsApp failed to {to_number}: [{e.code}] {e.msg}")
            
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"WhatsApp error to {to_number}: {str(e)}")
        
        return result
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send an SMS message via Twilio.
        
        Args:
            to_number: Recipient phone number (with country code)
            message: Message content
            
        Returns:
            Dict with success status, message_sid, and error details if any
        """
        result = {
            "success": False,
            "channel": "sms",
            "to": to_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_sid": None,
            "error_code": None,
            "error_message": None
        }
        
        if not self.is_configured:
            result["error_message"] = "Twilio not configured"
            return result
        
        if not self.sms_from:
            result["error_message"] = "SMS sender not configured"
            return result
        
        try:
            # Remove whatsapp: prefix if present
            clean_number = to_number.replace('whatsapp:', '')
            
            twilio_message = self.client.messages.create(
                from_=self.sms_from,
                to=clean_number,
                body=message
            )
            
            result["success"] = True
            result["message_sid"] = twilio_message.sid
            result["status"] = twilio_message.status
            
            logger.info(f"SMS sent to {to_number}: {twilio_message.sid}")
            
        except TwilioRestException as e:
            result["error_code"] = e.code
            result["error_message"] = self._get_friendly_error(e.code, str(e))
            logger.error(f"SMS failed to {to_number}: [{e.code}] {e.msg}")
            
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"SMS error to {to_number}: {str(e)}")
        
        return result
    
    async def send_whatsapp_template(
        self,
        to_number: str,
        template_sid: str,
        template_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp template message (for marketing/notifications).
        
        Args:
            to_number: Recipient phone number
            template_sid: Twilio content template SID
            template_variables: Variables to substitute in template
            
        Returns:
            Dict with success status and details
        """
        result = {
            "success": False,
            "channel": "whatsapp_template",
            "to": to_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_sid": None,
            "error_code": None,
            "error_message": None
        }
        
        if not self.is_configured:
            result["error_message"] = "Twilio not configured"
            return result
        
        try:
            formatted_to = to_number if to_number.startswith('whatsapp:') else f'whatsapp:{to_number}'
            
            msg_params = {
                'from_': self.whatsapp_from,
                'to': formatted_to,
                'content_sid': template_sid
            }
            
            if template_variables:
                msg_params['content_variables'] = str(template_variables)
            
            twilio_message = self.client.messages.create(**msg_params)
            
            result["success"] = True
            result["message_sid"] = twilio_message.sid
            result["status"] = twilio_message.status
            
            logger.info(f"WhatsApp template sent to {to_number}: {twilio_message.sid}")
            
        except TwilioRestException as e:
            result["error_code"] = e.code
            result["error_message"] = self._get_friendly_error(e.code, str(e))
            logger.error(f"WhatsApp template failed to {to_number}: [{e.code}] {e.msg}")
            
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"WhatsApp template error to {to_number}: {str(e)}")
        
        return result
    
    def _get_friendly_error(self, error_code: int, raw_message: str) -> str:
        """
        Convert Twilio error codes to user-friendly messages.
        """
        error_messages = {
            21608: "WhatsApp number not registered or user hasn't opted in",
            21610: "Message blocked - recipient has unsubscribed",
            21614: "Invalid phone number format",
            21617: "Message content too long",
            21211: "Invalid phone number",
            63001: "WhatsApp channel not available",
            63003: "WhatsApp outside allowed window - need template message",
            63007: "WhatsApp rate limit exceeded",
            63016: "WhatsApp message failed to send",
            63049: "Marketing message rate limit - user receiving too many messages",
            30003: "Unreachable destination",
            30004: "Message blocked by carrier",
            30005: "Unknown destination",
            30006: "Landline or unreachable carrier",
            30007: "Message filtered as spam"
        }
        
        return error_messages.get(error_code, f"Error {error_code}: {raw_message}")


# Singleton instance
twilio_service = TwilioService()
