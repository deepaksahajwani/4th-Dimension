"""
Async Notification Service
Non-blocking notification delivery for WhatsApp, Email, and SMS
"""

import asyncio
import logging
import os
from typing import Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Notification queue for background processing
notification_queue: asyncio.Queue = asyncio.Queue()


class AsyncNotificationService:
    """
    Async notification service that processes notifications in background.
    Notifications are queued and processed without blocking the main request.
    """
    
    def __init__(self):
        self.is_running = False
        self.worker_task = None
        self.twilio_client = None
        self.sendgrid_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Twilio and SendGrid clients"""
        try:
            from twilio.rest import Client
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("Twilio client initialized for async notifications")
        except Exception as e:
            logger.warning(f"Twilio client init failed: {e}")
        
        try:
            from sendgrid import SendGridAPIClient
            api_key = os.environ.get('SENDGRID_API_KEY')
            if api_key:
                self.sendgrid_client = SendGridAPIClient(api_key)
                logger.info("SendGrid client initialized for async notifications")
        except Exception as e:
            logger.warning(f"SendGrid client init failed: {e}")
    
    async def start_worker(self):
        """Start the background worker to process notifications"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._process_queue())
        logger.info("Async notification worker started")
    
    async def stop_worker(self):
        """Stop the background worker"""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Async notification worker stopped")
    
    async def _process_queue(self):
        """Background worker that processes notifications from the queue"""
        while self.is_running:
            try:
                # Wait for notification with timeout
                try:
                    notification = await asyncio.wait_for(
                        notification_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process notification
                await self._send_notification(notification)
                notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification based on its type"""
        notif_type = notification.get('type')
        
        try:
            if notif_type == 'whatsapp':
                await self._send_whatsapp(notification)
            elif notif_type == 'whatsapp_template':
                await self._send_whatsapp_template(notification)
            elif notif_type == 'whatsapp_media':
                await self._send_whatsapp_with_media(notification)
            elif notif_type == 'email':
                await self._send_email(notification)
            elif notif_type == 'sms':
                await self._send_sms(notification)
            
            # Log success
            await self._log_notification(notification, 'success')
            
        except Exception as e:
            logger.error(f"Failed to send {notif_type} notification: {e}")
            await self._log_notification(notification, 'failed', str(e))
    
    async def _send_whatsapp_with_media(self, notification: Dict[str, Any]):
        """Send WhatsApp message with media attachment (PDF/image)"""
        if not self.twilio_client:
            logger.warning("Twilio client not available for WhatsApp media")
            return
        
        phone = notification.get('phone')
        media_url = notification.get('media_url')
        message = notification.get('message', '')
        
        from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        to_number = f"whatsapp:{phone}" if not phone.startswith('whatsapp:') else phone
        
        try:
            # Send message with media
            msg = self.twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                body=message,
                media_url=[media_url] if media_url else None
            )
            logger.info(f"WhatsApp media sent: {msg.sid}")
        except Exception as e:
            logger.error(f"WhatsApp media send failed: {e}")
            raise
    
    async def _send_whatsapp(self, notification: Dict[str, Any]):
        """Send freeform WhatsApp message (only works within 24h window)"""
        if not self.twilio_client:
            return
        
        phone = notification.get('phone')
        message = notification.get('message')
        
        # Check 24h window before attempting freeform
        if not await self._check_24h_window(phone):
            logger.info(f"Skipping freeform WhatsApp to {phone} - outside 24h window")
            return
        
        from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        to_number = f"whatsapp:{phone}" if not phone.startswith('whatsapp:') else phone
        
        try:
            msg = self.twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                body=message
            )
            logger.info(f"WhatsApp sent: {msg.sid}")
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            raise
    
    async def _send_whatsapp_template(self, notification: Dict[str, Any]):
        """Send WhatsApp template message (works outside 24h window)"""
        if not self.twilio_client:
            return
        
        phone = notification.get('phone')
        content_sid = notification.get('content_sid')
        variables = notification.get('variables', {})
        
        from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        to_number = f"whatsapp:{phone}" if not phone.startswith('whatsapp:') else phone
        
        try:
            msg = self.twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                content_sid=content_sid,
                content_variables=variables
            )
            logger.info(f"WhatsApp template sent: {msg.sid}")
        except Exception as e:
            logger.error(f"WhatsApp template send failed: {e}")
            raise
    
    async def _send_email(self, notification: Dict[str, Any]):
        """Send email via SendGrid"""
        if not self.sendgrid_client:
            return
        
        from sendgrid.helpers.mail import Mail
        
        sender = os.environ.get('SENDER_EMAIL', 'contact@4thdimensionarchitect.com')
        
        message = Mail(
            from_email=sender,
            to_emails=notification.get('to_email'),
            subject=notification.get('subject'),
            html_content=notification.get('html_content')
        )
        
        try:
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent: {response.status_code}")
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            raise
    
    async def _send_sms(self, notification: Dict[str, Any]):
        """Send SMS via Twilio"""
        if not self.twilio_client:
            return
        
        phone = notification.get('phone')
        message = notification.get('message')
        
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        if not from_number:
            return
        
        try:
            msg = self.twilio_client.messages.create(
                from_=from_number,
                to=phone,
                body=message
            )
            logger.info(f"SMS sent: {msg.sid}")
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            raise
    
    async def _check_24h_window(self, phone: str) -> bool:
        """
        Check if we're within the 24h WhatsApp conversation window.
        Returns True if we can send freeform messages.
        """
        try:
            # Check last inbound message from this number
            last_inbound = await db.whatsapp_messages.find_one(
                {
                    "phone": phone,
                    "direction": "inbound"
                },
                sort=[("timestamp", -1)]
            )
            
            if not last_inbound:
                return False
            
            last_time = last_inbound.get('timestamp')
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
            
            # Check if within 24 hours
            now = datetime.now(timezone.utc)
            hours_diff = (now - last_time).total_seconds() / 3600
            
            return hours_diff < 24
            
        except Exception as e:
            logger.error(f"Error checking 24h window: {e}")
            return False  # Default to false to avoid failed freeform attempts
    
    async def _log_notification(self, notification: Dict[str, Any], status: str, error: str = None):
        """Log notification to database asynchronously"""
        try:
            log_entry = {
                "type": notification.get('type'),
                "recipient": notification.get('phone') or notification.get('to_email'),
                "status": status,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    k: v for k, v in notification.items() 
                    if k not in ['phone', 'to_email', 'html_content', 'message']
                }
            }
            await db.notification_logs.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    # Public API - Queue notifications for async processing
    
    def queue_whatsapp(self, phone: str, message: str, **kwargs):
        """Queue a WhatsApp message for async delivery"""
        asyncio.create_task(notification_queue.put({
            'type': 'whatsapp',
            'phone': phone,
            'message': message,
            **kwargs
        }))
    
    def queue_whatsapp_template(self, phone: str, content_sid: str, variables: Dict, **kwargs):
        """Queue a WhatsApp template message for async delivery"""
        asyncio.create_task(notification_queue.put({
            'type': 'whatsapp_template',
            'phone': phone,
            'content_sid': content_sid,
            'variables': variables,
            **kwargs
        }))
    
    def queue_whatsapp_with_media(self, phone: str, media_url: str, message: str = '', **kwargs):
        """Queue a WhatsApp message with media attachment"""
        asyncio.create_task(notification_queue.put({
            'type': 'whatsapp_media',
            'phone': phone,
            'media_url': media_url,
            'message': message,
            **kwargs
        }))
    
    def queue_email(self, to_email: str, subject: str, html_content: str, **kwargs):
        """Queue an email for async delivery"""
        asyncio.create_task(notification_queue.put({
            'type': 'email',
            'to_email': to_email,
            'subject': subject,
            'html_content': html_content,
            **kwargs
        }))
    
    def queue_sms(self, phone: str, message: str, **kwargs):
        """Queue an SMS for async delivery"""
        asyncio.create_task(notification_queue.put({
            'type': 'sms',
            'phone': phone,
            'message': message,
            **kwargs
        }))


# Singleton instance
async_notification_service = AsyncNotificationService()
