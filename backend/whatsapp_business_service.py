"""
WhatsApp Business API Service
Handles sending messages via Meta's WhatsApp Business Platform
"""
import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WhatsAppBusinessService:
    """Service to send messages via WhatsApp Business API"""
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v21.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp Business API credentials not configured")
    
    async def send_message(self, to: str, message: str) -> dict:
        """
        Send a WhatsApp message using WhatsApp Business API
        
        Args:
            to: Phone number in E.164 format (e.g., +919374720431)
            message: Message text to send
            
        Returns:
            dict with success status and message_id or error
        """
        try:
            # Remove 'whatsapp:' prefix if present
            if to.startswith('whatsapp:'):
                to = to.replace('whatsapp:', '')
            
            # Ensure it starts with +
            if not to.startswith('+'):
                to = f'+{to}'
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message
                }
            }
            
            logger.info(f"Sending WhatsApp message to {to[:8]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                response_data = response.json()
                
                if response.status_code == 200:
                    message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                    logger.info(f"WhatsApp message sent successfully: {message_id}")
                    return {
                        'success': True,
                        'message_id': message_id,
                        'status': 'sent'
                    }
                else:
                    error_message = response_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"WhatsApp API error: {error_message}")
                    return {
                        'success': False,
                        'error': error_message,
                        'status_code': response.status_code
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"WhatsApp API timeout for {to}")
            return {
                'success': False,
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
whatsapp_business_service = WhatsAppBusinessService()
