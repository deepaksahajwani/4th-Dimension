"""
Invite Service - Send invitations via WhatsApp (preferred) or SMS (fallback)
Strategy:
1. Try WhatsApp template first (approved templates work for business-initiated messages)
2. Fall back to SMS if WhatsApp template fails
3. Include prompt for users to reply "START" to enable future freeform messages
"""

import os
import logging
from typing import Optional
from notification_service import notification_service
from whatsapp_templates import WHATSAPP_TEMPLATES

logger = logging.getLogger(__name__)

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://arch-manager-1.preview.emergentagent.com')

# WhatsApp Business Number (Production)
WHATSAPP_NUMBER = "+917016779016"

# Keyword for users to reply to open 24-hour conversation window
REPLY_KEYWORD = "START"

# Human-readable invitee type labels
INVITEE_TYPE_LABELS = {
    'team_member': 'Team Member',
    'client': 'Client',
    'contractor': 'Contractor',
    'consultant': 'Consultant',
    'vendor': 'Vendor'
}


async def send_registration_invite(
    name: str,
    phone: str,
    invitee_type: str,
    invited_by_name: str
) -> dict:
    """
    Send invitation - sends BOTH WhatsApp template AND SMS to ensure delivery
    
    Args:
        name: Name of person being invited
        phone: Phone number (should include country code)
        invitee_type: 'team_member', 'client', 'contractor', 'consultant'
        invited_by_name: Name of person sending invite
    
    Returns:
        dict with success status and message
    """
    try:
        # Generate registration link
        registration_url = f"{APP_URL}/register"
        
        # Get human-readable invitee type
        invitee_label = INVITEE_TYPE_LABELS.get(invitee_type, invitee_type.replace('_', ' ').title())
        
        results = {"whatsapp": None, "sms": None}
        
        # Try WhatsApp template first (primary method for business-initiated messages)
        template_sid = WHATSAPP_TEMPLATES.get("invitation")
        
        if template_sid:
            logger.info(f"Sending WhatsApp template invitation to {name} ({phone})...")
            template_result = await notification_service.send_whatsapp_template(
                phone_number=phone,
                content_sid=template_sid,
                content_variables={
                    "1": name,
                    "2": invited_by_name,
                    "3": invitee_label,
                    "4": registration_url
                }
            )
            
            if template_result.get('success'):
                logger.info(f"WhatsApp template invite sent to {name} ({phone}) as {invitee_type}")
                results["whatsapp"] = "sent"
            else:
                logger.warning(f"WhatsApp template failed for {phone}: {template_result.get('error')}")
                results["whatsapp"] = "failed"
        
        # ALWAYS send SMS as backup (WhatsApp delivery can fail silently with error 63049)
        logger.info(f"Sending SMS invite to {name} ({phone}) as backup...")
        
        sms_message = f"""Hi {name}!

{invited_by_name} from 4th Dimension Architects has invited you to join as a {invitee_label}.

📱 REGISTER HERE:
{registration_url}

💬 FOR WHATSAPP UPDATES:
1. Save our number: {WHATSAPP_NUMBER}
2. Send "{REPLY_KEYWORD}" to us on WhatsApp
3. Start receiving instant project notifications!

Welcome aboard!
- 4th Dimension Architects"""

        sms_result = await notification_service.send_sms(
            phone_number=phone,
            message=sms_message
        )
        
        if sms_result.get('success'):
            logger.info(f"SMS invite sent to {name} ({phone}) as {invitee_type}")
            results["sms"] = "sent"
        else:
            logger.warning(f"SMS invite failed for {phone}: {sms_result.get('error')}")
            results["sms"] = "failed"
        
        # Determine overall success
        if results["whatsapp"] == "sent" or results["sms"] == "sent":
            channels = []
            if results["whatsapp"] == "sent":
                channels.append("WhatsApp")
            if results["sms"] == "sent":
                channels.append("SMS")
            
            return {
                "success": True,
                "message": f"Invite sent to {name} via {' and '.join(channels)}",
                "channels": results
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send invite via both WhatsApp and SMS",
                "channels": results
            }
            
    except Exception as e:
        logger.error(f"Error in send_registration_invite: {str(e)}")
        return {
            "success": False,
            "message": f"Error sending invite: {str(e)}"
        }


async def send_whatsapp_optin_sms(
    name: str,
    phone: str,
    context: str = "project updates"
) -> dict:
    """
    Send SMS asking user to opt-in to WhatsApp notifications by replying START
    """
    try:
        sms_message = f"""Hi {name}!

To receive {context} on WhatsApp from 4th Dimension Architects:

1️⃣ Save this number: {WHATSAPP_NUMBER}
2️⃣ Open WhatsApp and send "{REPLY_KEYWORD}" to us

Once connected, you'll receive instant notifications about your projects!

- 4th Dimension Architects"""

        result = await notification_service.send_sms(
            phone_number=phone,
            message=sms_message
        )
        
        if result.get('success'):
            logger.info(f"WhatsApp opt-in SMS sent to {name} ({phone})")
            return {
                "success": True,
                "message": f"Opt-in SMS sent to {name}",
                "message_sid": result.get('message_sid')
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send opt-in SMS: {result.get('error')}"
            }
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp opt-in SMS: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
