"""
Simplified Invite Service - Send WhatsApp invites to register
"""

import os
import logging
from typing import Optional
from notification_service import notification_service

logger = logging.getLogger(__name__)

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pmfourth.preview.emergentagent.com')


async def send_registration_invite(
    name: str,
    phone: str,
    invitee_type: str,
    invited_by_name: str
) -> dict:
    """
    Send WhatsApp invite to register
    
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
        
        # Create personalized message based on invitee type
        messages = {
            'team_member': f"""Hello {name}!

{invited_by_name} from 4th Dimension Architects has invited you to join our team.

You've been invited to register on our project management platform where you can:
✅ Collaborate on architectural projects
✅ Manage drawings and revisions
✅ Track project progress
✅ Communicate with the team

Please register here: {registration_url}

After registration, your account will be reviewed and approved.

Welcome to the team!

- 4th Dimension Architects""",

            'client': f"""Dear {name},

{invited_by_name} from 4th Dimension Architects has invited you to our client portal.

As our valued client, you can:
✅ Track your project progress in real-time
✅ Review and comment on drawings
✅ View project milestones
✅ Manage payments
✅ Stay updated with notifications

Please register here: {registration_url}

Select "Client" as your role during registration.

We look forward to serving you!

Best regards,
4th Dimension Architects""",

            'contractor': f"""Hello {name},

{invited_by_name} from 4th Dimension Architects has invited you to register as a contractor on our platform.

As a registered contractor, you can:
✅ View project details and drawings
✅ Receive notifications about project updates
✅ Communicate with the project team
✅ Track your assigned tasks

Please register here: {registration_url}

Select "Contractor" as your role during registration.

Looking forward to working with you!

- 4th Dimension Architects""",

            'consultant': f"""Hello {name},

{invited_by_name} from 4th Dimension Architects has invited you to register as a consultant on our platform.

As a registered consultant, you can:
✅ Access project drawings and documentation
✅ Provide expert feedback and recommendations
✅ Collaborate with the project team
✅ Receive timely notifications

Please register here: {registration_url}

Select "Consultant" as your role during registration.

We value your expertise!

- 4th Dimension Architects"""
        }
        
        message = messages.get(invitee_type, messages['team_member'])
        
        # Send WhatsApp message
        result = await notification_service.send_whatsapp(
            phone_number=phone,
            message=message
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
