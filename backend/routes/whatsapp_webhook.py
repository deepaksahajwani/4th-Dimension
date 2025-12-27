"""
WhatsApp Webhook Routes
Handles incoming WhatsApp messages from Twilio
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks"])


@router.post("/incoming")
async def whatsapp_webhook_incoming(request: Request):
    """
    Twilio WhatsApp Webhook - receives incoming messages
    Configure this URL in Twilio Console: https://your-domain/api/webhooks/whatsapp/incoming
    """
    try:
        from whatsapp_webhook_handler import handle_incoming_whatsapp
        
        # Parse form data from Twilio
        form_data = await request.form()
        
        from_number = form_data.get('From', '')
        body = form_data.get('Body', '')
        num_media = int(form_data.get('NumMedia', 0))
        
        # Get media URL if present (for voice notes)
        media_url = form_data.get('MediaUrl0') if num_media > 0 else None
        media_content_type = form_data.get('MediaContentType0') if num_media > 0 else None
        
        logger.info(f"Incoming WhatsApp from {from_number[:15]}...: {body[:50] if body else '[Media]'}")
        
        # Process the message and get response
        response_message = await handle_incoming_whatsapp(
            from_number=from_number,
            body=body,
            num_media=num_media,
            media_url=media_url,
            media_content_type=media_content_type
        )
        
        # Return TwiML response
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>'''
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
        # Return empty response on error (Twilio will retry)
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")


@router.get("/incoming")
async def whatsapp_webhook_verify():
    """
    GET endpoint for Twilio webhook verification
    """
    return {"status": "WhatsApp webhook endpoint active", "message": "Configure this URL in your Twilio Console"}


@router.get("/status")
async def whatsapp_webhook_status():
    """
    Check webhook status
    """
    return {
        "status": "active",
        "endpoint": "/api/webhooks/whatsapp/incoming",
        "methods": ["GET", "POST"],
        "description": "Twilio WhatsApp incoming message webhook"
    }
