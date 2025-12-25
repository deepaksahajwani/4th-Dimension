"""
Simplified Invite Service - Send WhatsApp invites to register using approved templates
"""

import os
import logging
from typing import Optional
from notification_service import notification_service

logger = logging.getLogger(__name__)

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tasktracker-bugs.preview.emergentagent.com')

# WhatsApp Template Content SID (approved template)
INVITE_TEMPLATE_SID = "HX6b1d5f9a7a01af474f0875e734e9d548"

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
    Send WhatsApp invite to register using approved template
    
    Template variables:
    {{1}} = name (person being invited)
    {{2}} = invited_by_name
    {{3}} = invitee_type (Client, Team Member, etc.)
    {{4}} = registration URL
    
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
        
        # Template variables (must match the template placeholders {{1}}, {{2}}, etc.)
        content_variables = {
            "1": name,
            "2": invited_by_name,
            "3": invitee_label,
            "4": registration_url
        }
        
        # Send WhatsApp message using template
        result = await notification_service.send_whatsapp_template(
            phone_number=phone,
            content_sid=INVITE_TEMPLATE_SID,
            content_variables=content_variables
        )
        
        if result.get('success'):
            logger.info(f"Invite sent to {name} ({phone}) as {invitee_type}")
            return {
                "success": True,
                "message": f"WhatsApp invite sent to {name}",
                "message_sid": result.get('message_sid')
            }
        else:
            logger.error(f"Failed to send invite: {result.get('error')}")
            return {
                "success": False,
                "message": f"Failed to send WhatsApp invite: {result.get('error')}"
            }
            
    except Exception as e:
        logger.error(f"Error in send_registration_invite: {str(e)}")
        return {
            "success": False,
            "message": f"Error sending invite: {str(e)}"
        }
