"""
Invite Service - Send invitations via SMS with WhatsApp opt-in instructions
Since WhatsApp Business API requires user to message first (24-hour window rule),
we send SMS inviting them to connect on WhatsApp for future notifications.
"""

import os
import logging
from typing import Optional
from notification_service import notification_service

logger = logging.getLogger(__name__)

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tasktracker-bugs.preview.emergentagent.com')

# WhatsApp Business Number
WHATSAPP_NUMBER = "+917016779166"

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
    Send invitation via SMS with WhatsApp opt-in instructions
    
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
        
        # Create SMS message with WhatsApp opt-in
        sms_message = f"""Hi {name}!

{invited_by_name} from 4th Dimension Architects has invited you to join as a {invitee_label}.

📱 REGISTER HERE:
{registration_url}

💬 FOR WHATSAPP UPDATES:
Save our number {WHATSAPP_NUMBER} and send "Hi" to receive project notifications on WhatsApp.

Welcome aboard!
- 4th Dimension Architects"""

        # Send SMS
        result = await notification_service.send_sms(
            phone_number=phone,
            message=sms_message
        )
        
        if result.get('success'):
            logger.info(f"SMS invite sent to {name} ({phone}) as {invitee_type}")
            return {
                "success": True,
                "message": f"SMS invite sent to {name}",
                "message_sid": result.get('message_sid'),
                "channel": "sms"
            }
        else:
            logger.error(f"Failed to send SMS invite: {result.get('error')}")
            return {
                "success": False,
                "message": f"Failed to send SMS invite: {result.get('error')}"
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
    Send SMS asking user to opt-in to WhatsApp notifications
    
    Args:
        name: User's name
        phone: Phone number
        context: What notifications they'll receive (e.g., "project updates", "drawing notifications")
    """
    try:
        sms_message = f"""Hi {name}!

To receive {context} on WhatsApp from 4th Dimension Architects:

1️⃣ Save this number: {WHATSAPP_NUMBER}
2️⃣ Open WhatsApp and send "Hi" to us

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
