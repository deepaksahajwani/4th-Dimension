"""
Template-Based Notification Service

This service handles sending notifications using WhatsApp templates
with SMS fallback when templates fail or are pending approval.

Usage:
    from template_notification_service import template_notification_service
    
    # Using convenience methods
    await template_notification_service.notify_drawing_issued(
        phone_number="+919876543210",
        recipient_name="John Doe",
        project_name="Villa Project",
        drawing_name="Floor Plan"
    )
    
    # Using generic method
    await template_notification_service.send_notification(
        template_key="drawing_issued",
        recipient_phone="+919876543210",
        variables={
            "recipient_name": "John",
            "drawing_name": "Floor Plan",
            "project_name": "Villa Project",
            "issue_date": "02 Jan 2025",
            "portal_url": "https://..."
        }
    )
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from whatsapp_templates import (
    get_template,
    get_template_for_event,
    is_template_approved, 
    WhatsAppTemplate,
    TemplateStatus,
    TEMPLATES,
    EVENT_TEMPLATE_MAP
)

logger = logging.getLogger(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
TWILIO_SMS_FROM = os.environ.get('TWILIO_PHONE_NUMBER')
APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://review-page.preview.emergentagent.com')


class TemplateNotificationService:
    """
    Service for sending template-based WhatsApp notifications with SMS fallback.
    
    All 17 templates are now approved and ready to use:
    - User: user_approved, invitation, new_invitation
    - Project: project_created_client, project_created_team, project_update
    - Drawing: drawing_uploaded, drawing_approved, drawing_revised, drawing_issued,
               drawing_issued_contractor, drawing_approval_needed, revision_requested
    - Other: task_assigned, new_comment, 3d_images_uploaded, consultant_notification
    """
    
    def __init__(self):
        self.twilio_client = None
        self.app_url = APP_URL
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
        
        # Try WhatsApp template first (if approved and phone provided)
        if recipient_phone and template.status == TemplateStatus.APPROVED and self.twilio_client:
            whatsapp_result = await self._send_whatsapp_template(
                template, 
                recipient_phone, 
                variables
            )
            result["whatsapp_sent"] = whatsapp_result.get("success", False)
            result["whatsapp_sid"] = whatsapp_result.get("message_sid")
            result["whatsapp_error"] = whatsapp_result.get("error")
        
        # Fallback to SMS if WhatsApp failed or template pending
        if recipient_phone and not result["whatsapp_sent"]:
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
    
    async def send_by_event(
        self,
        event_type: str,
        recipient_phone: str,
        variables: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send notification by event type (maps to template automatically).
        
        Args:
            event_type: Event type (e.g., 'drawing_issued', 'user_approved')
            recipient_phone: Recipient phone number
            variables: Template variables
            **kwargs: Additional arguments passed to send_notification
            
        Returns:
            Dict with success status and details
        """
        template_key = EVENT_TEMPLATE_MAP.get(event_type)
        if not template_key:
            return {
                "success": False,
                "error": f"No template mapped for event: {event_type}"
            }
        return await self.send_notification(
            template_key=template_key,
            recipient_phone=recipient_phone,
            variables=variables,
            **kwargs
        )
    
    async def _send_whatsapp_template(
        self,
        template: WhatsAppTemplate,
        phone: str,
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """Send WhatsApp template message via Twilio"""
        try:
            # Format phone number
            phone = phone.strip()
            if phone.startswith('whatsapp:'):
                phone = phone[9:].strip()
            if not phone.startswith('+'):
                phone = f"+{phone}"
            formatted_phone = f'whatsapp:{phone}'
            
            # Build content variables (numbered 1, 2, 3, etc.)
            content_vars = {}
            for i, var_name in enumerate(template.variables, 1):
                value = variables.get(var_name, "")
                content_vars[str(i)] = str(value) if value else ""
            
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
            logger.error(f"WhatsApp template error for {template.name}: {error_msg}")
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
            # Clean phone number
            clean_phone = phone.replace('whatsapp:', '').strip()
            if not clean_phone.startswith('+'):
                clean_phone = f"+{clean_phone}"
            
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
                template = template.replace(f"{{{key}}}", str(value) if value else "")
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
            logger.debug(f"Notification logging skipped: {str(e)}")
    
    # ============================================
    # CONVENIENCE METHODS FOR SPECIFIC EVENTS
    # ============================================
    
    async def notify_user_approved(
        self,
        phone_number: str,
        user_name: str,
        role: str,
        approver_name: str = "Admin",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify user that their registration was approved."""
        approval_date = datetime.now(timezone.utc).strftime("%d %b %Y")
        return await self.send_notification(
            template_key="user_approved",
            recipient_phone=phone_number,
            variables={
                "user_name": user_name,
                "role": role,
                "approver_name": approver_name,
                "approval_date": approval_date,
                "portal_url": self.app_url
            },
            recipient_id=user_id,
            in_app_title="Welcome! Registration Approved",
            in_app_message=f"Your registration as {role} has been approved.",
            in_app_link="/"
        )
    
    async def notify_invitation(
        self,
        phone_number: str,
        invitee_name: str,
        inviter_name: str,
        role: str,
        register_url: str
    ) -> Dict[str, Any]:
        """Send invitation to new user."""
        return await self.send_notification(
            template_key="invitation",
            recipient_phone=phone_number,
            variables={
                "invitee_name": invitee_name,
                "inviter_name": inviter_name,
                "role": role,
                "register_url": register_url
            },
            create_in_app=False  # New user doesn't have account yet
        )
    
    async def notify_project_created_client(
        self,
        phone_number: str,
        client_name: str,
        project_name: str,
        team_leader_name: str,
        team_leader_phone: str = "Contact via portal",
        client_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify client that their project was created."""
        return await self.send_notification(
            template_key="project_created_client",
            recipient_phone=phone_number,
            variables={
                "client_name": client_name,
                "project_name": project_name,
                "team_leader": team_leader_name,
                "team_leader_phone": team_leader_phone,
                "portal_url": self.app_url
            },
            recipient_id=client_id,
            in_app_title=f"New Project: {project_name}",
            in_app_message=f"Your project '{project_name}' has been created!",
            in_app_link=f"/projects/{project_id}" if project_id else "/projects",
            project_id=project_id
        )
    
    async def notify_project_created_team(
        self,
        phone_number: str,
        project_name: str,
        client_name: str,
        client_phone: str = "N/A",
        team_leader_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify team leader about new project assignment."""
        return await self.send_notification(
            template_key="project_created_team",
            recipient_phone=phone_number,
            variables={
                "project_name": project_name,
                "client_name": client_name,
                "client_phone": client_phone,
                "portal_url": self.app_url
            },
            recipient_id=team_leader_id,
            in_app_title=f"New Project Assigned: {project_name}",
            in_app_message=f"You've been assigned as team leader for '{project_name}'",
            in_app_link=f"/projects/{project_id}" if project_id else "/projects",
            project_id=project_id
        )
    
    async def notify_project_update(
        self,
        phone_number: str,
        client_name: str,
        project_name: str,
        percentage: int,
        update_text: str = "",
        client_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify client about project progress update."""
        return await self.send_notification(
            template_key="project_update",
            recipient_phone=phone_number,
            variables={
                "client_name": client_name,
                "project_name": project_name,
                "percentage": str(percentage),
                "update_text": update_text[:50] if update_text else "",
                "portal_url": self.app_url
            },
            recipient_id=client_id,
            in_app_title=f"Project Update: {project_name}",
            in_app_message=f"Project is now {percentage}% complete",
            in_app_link=f"/projects/{project_id}" if project_id else "/projects",
            project_id=project_id
        )
    
    async def notify_drawing_uploaded(
        self,
        phone_number: str,
        recipient_name: str,
        project_name: str,
        drawing_name: str,
        uploader_name: str,
        portal_url: Optional[str] = None,
        recipient_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify about a new drawing upload."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_uploaded",
            recipient_phone=phone_number,
            variables={
                "recipient_name": recipient_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "uploader_name": uploader_name,
                "portal_url": portal_url or self.app_url
            },
            recipient_id=recipient_id,
            in_app_title=f"New Drawing: {drawing_name}",
            in_app_message=f"New drawing uploaded for '{project_name}' by {uploader_name}",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_drawing_approval_needed(
        self,
        phone_number: str,
        owner_name: str,
        project_name: str,
        drawing_name: str,
        uploader_name: str,
        portal_url: Optional[str] = None,
        owner_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify owner that a drawing needs approval."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_approval_needed",
            recipient_phone=phone_number,
            variables={
                "owner_name": owner_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "uploader_name": uploader_name,
                "portal_url": portal_url or self.app_url
            },
            recipient_id=owner_id,
            in_app_title=f"Approval Needed: {drawing_name}",
            in_app_message=f"Drawing '{drawing_name}' needs your approval",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_drawing_approved(
        self,
        phone_number: str,
        recipient_name: str,
        project_name: str,
        drawing_name: str,
        revision: str = "0",
        recipient_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify that a drawing was approved."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_approved",
            recipient_phone=phone_number,
            variables={
                "recipient_name": recipient_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "revision": revision,
                "portal_url": self.app_url
            },
            recipient_id=recipient_id,
            in_app_title=f"Drawing Approved: {drawing_name}",
            in_app_message=f"Drawing '{drawing_name}' (Rev {revision}) has been approved",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_drawing_revised(
        self,
        phone_number: str,
        recipient_name: str,
        project_name: str,
        drawing_name: str,
        revision: str,
        updater_name: str,
        portal_url: Optional[str] = None,
        recipient_id: Optional[str] = None,
        project_id: Optional[str] = None,
        revision_number: int = 0,
        revised_by: str = "",
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify about a drawing revision."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_revised",
            recipient_phone=phone_number,
            variables={
                "recipient_name": recipient_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "revision": revision or str(revision_number),
                "updater_name": updater_name or revised_by,
                "portal_url": portal_url or self.app_url
            },
            recipient_id=recipient_id,
            in_app_title=f"Drawing Revised: {drawing_name}",
            in_app_message=f"Drawing '{drawing_name}' updated to Rev {revision or revision_number}",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_drawing_issued(
        self,
        phone_number: str,
        recipient_name: str,
        project_name: str,
        drawing_name: str,
        issue_date: Optional[str] = None,
        portal_url: Optional[str] = None,
        recipient_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify that a drawing was issued."""
        if not issue_date:
            issue_date = datetime.now(timezone.utc).strftime("%d %b %Y")
        
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_issued",
            recipient_phone=phone_number,
            variables={
                "recipient_name": recipient_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "issue_date": issue_date,
                "portal_url": portal_url or self.app_url
            },
            recipient_id=recipient_id,
            in_app_title=f"Drawing Issued: {drawing_name}",
            in_app_message=f"Drawing '{drawing_name}' has been issued",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_drawing_issued_contractor(
        self,
        phone_number: str,
        contractor_name: str,
        project_name: str,
        drawing_name: str,
        revision: str,
        contractor_type: str,
        contractor_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify contractor that a drawing was issued to them."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="drawing_issued_contractor",
            recipient_phone=phone_number,
            variables={
                "contractor_name": contractor_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "revision": revision,
                "contractor_type": contractor_type,
                "portal_url": self.app_url
            },
            recipient_id=contractor_id,
            in_app_title=f"Drawing Issued: {drawing_name}",
            in_app_message=f"Drawing '{drawing_name}' issued for your {contractor_type} work",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_revision_requested(
        self,
        phone_number: str,
        team_leader_name: str,
        project_name: str,
        drawing_name: str,
        requester_name: str,
        reason: str = "See comments",
        team_leader_id: Optional[str] = None,
        project_id: Optional[str] = None,
        drawing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify team leader that a revision was requested."""
        # Build deep-link URL for single-item review page
        if drawing_id and project_id:
            in_app_link = f"/projects/{project_id}/drawing/{drawing_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="revision_requested",
            recipient_phone=phone_number,
            variables={
                "team_leader_name": team_leader_name,
                "project_name": project_name,
                "drawing_name": drawing_name,
                "requester_name": requester_name,
                "reason": reason[:50] if reason else "See comments",
                "portal_url": self.app_url
            },
            recipient_id=team_leader_id,
            in_app_title=f"Revision Requested: {drawing_name}",
            in_app_message=f"{requester_name} requested revision for '{drawing_name}'",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_task_assigned(
        self,
        phone_number: str,
        assignee_name: str,
        task_name: str,
        project_name: str,
        due_date: str,
        assignee_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify about a task assignment."""
        return await self.send_notification(
            template_key="task_assigned",
            recipient_phone=phone_number,
            variables={
                "assignee_name": assignee_name,
                "task_name": task_name,
                "project_name": project_name,
                "due_date": due_date,
                "portal_url": self.app_url
            },
            recipient_id=assignee_id,
            in_app_title=f"New Task: {task_name}",
            in_app_message=f"Task assigned for '{project_name}'. Due: {due_date}",
            in_app_link=f"/projects/{project_id}" if project_id else "/work-tracker",
            project_id=project_id
        )
    
    async def notify_new_comment(
        self,
        phone_number: str,
        recipient_name: str,
        commenter_name: str,
        project_name: str,
        comment_preview: str,
        recipient_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify about a new comment."""
        return await self.send_notification(
            template_key="new_comment",
            recipient_phone=phone_number,
            variables={
                "recipient_name": recipient_name,
                "commenter_name": commenter_name,
                "project_name": project_name,
                "comment_preview": comment_preview[:100] if comment_preview else "",
                "portal_url": self.app_url
            },
            recipient_id=recipient_id,
            in_app_title=f"New Comment from {commenter_name}",
            in_app_message=f"Comment on '{project_name}': {comment_preview[:50]}...",
            in_app_link=f"/projects/{project_id}" if project_id else "/projects",
            project_id=project_id
        )
    
    async def notify_3d_images_uploaded(
        self,
        phone_number: str,
        client_name: str,
        project_name: str,
        category: str,
        count: int,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        image_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify client about new 3D images."""
        # Build deep-link URL for single-item review page if a specific image is provided
        if image_id and project_id:
            in_app_link = f"/projects/{project_id}/3d-image/{image_id}"
        elif project_id:
            in_app_link = f"/projects/{project_id}"
        else:
            in_app_link = "/projects"
        
        return await self.send_notification(
            template_key="3d_images_uploaded",
            recipient_phone=phone_number,
            variables={
                "client_name": client_name,
                "project_name": project_name,
                "category": category,
                "count": str(count),
                "portal_url": self.app_url
            },
            recipient_id=client_id,
            in_app_title=f"New 3D Images: {category}",
            in_app_message=f"{count} new 3D images uploaded for '{project_name}'",
            in_app_link=in_app_link,
            project_id=project_id
        )
    
    async def notify_consultant(
        self,
        phone_number: str,
        consultant_name: str,
        project_name: str,
        update_type: str,
        details: str,
        consultant_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Notify consultant about project update."""
        return await self.send_notification(
            template_key="consultant_notification",
            recipient_phone=phone_number,
            variables={
                "consultant_name": consultant_name,
                "project_name": project_name,
                "update_type": update_type,
                "details": details[:100] if details else "",
                "portal_url": self.app_url
            },
            recipient_id=consultant_id,
            in_app_title=f"{update_type}: {project_name}",
            in_app_message=details[:100] if details else update_type,
            in_app_link=f"/projects/{project_id}" if project_id else "/projects",
            project_id=project_id
        )
    
    # ============================================
    # BULK NOTIFICATION METHODS
    # ============================================
    
    async def notify_multiple_recipients(
        self,
        template_key: str,
        recipients: List[Dict[str, Any]],
        common_variables: Dict[str, str],
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Send same notification to multiple recipients.
        
        Args:
            template_key: Template to use
            recipients: List of dicts with 'phone', 'name', 'id' keys
            common_variables: Variables common to all notifications
            project_id: Associated project ID
            
        Returns:
            List of results for each recipient
        """
        results = []
        for recipient in recipients:
            variables = common_variables.copy()
            variables["recipient_name"] = recipient.get("name", "")
            
            result = await self.send_notification(
                template_key=template_key,
                recipient_phone=recipient.get("phone", ""),
                variables=variables,
                recipient_id=recipient.get("id"),
                project_id=project_id
            )
            results.append(result)
        
        return results


# Singleton instance
template_notification_service = TemplateNotificationService()


# Convenience function for backward compatibility
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
                "issue_date": "02 Jan 2025",
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
