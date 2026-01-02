"""
WhatsApp Template Configuration

This file contains all WhatsApp Business API template configurations.
Templates must be pre-approved by Meta before use.

IMPORTANT: Update template SIDs after Meta approval.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TemplateStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


@dataclass
class WhatsAppTemplate:
    """WhatsApp template configuration"""
    name: str
    sid: str
    status: TemplateStatus
    variables: List[str]  # Variable names in order
    description: str
    fallback_sms: str  # SMS fallback message template


# ============================================
# APPROVED TEMPLATES (Ready to use)
# ============================================

TEMPLATES = {
    # User Registration & Invitations
    "user_approved": WhatsAppTemplate(
        name="4d_user_approved_v2",
        sid="HX87566b3df94104dcf48df9e8819b1e13d",
        status=TemplateStatus.APPROVED,
        variables=["user_name", "role", "portal_url"],
        description="Registration approved notification",
        fallback_sms="Hi {user_name}, your registration as {role} has been approved! Access portal: {portal_url}"
    ),
    
    "invitation": WhatsAppTemplate(
        name="4d_invitation",
        sid="HX6b1d5f9a7a01af474f0875e734e9d548",
        status=TemplateStatus.APPROVED,
        variables=["invitee_name", "inviter_name", "role", "register_url"],
        description="General invitation to register",
        fallback_sms="Hi {invitee_name}, {inviter_name} has invited you to join 4th Dimension as {role}. Register: {register_url}"
    ),
    
    "new_invitation": WhatsAppTemplate(
        name="new_4d_invitation",
        sid="HX2a73a67f15f212fc2d7e5b1295468d2c",
        status=TemplateStatus.APPROVED,
        variables=["invitee_name", "company_name", "register_url"],
        description="New user invitation",
        fallback_sms="Hi {invitee_name}, you've been invited to join {company_name}. Register: {register_url}"
    ),
    
    # Project Notifications
    "project_created_client": WhatsAppTemplate(
        name="4d_project_created_client",
        sid="HX465fd35b0d97f4b51b6bce3e14cb9afd",
        status=TemplateStatus.APPROVED,
        variables=["client_name", "project_name", "team_leader", "portal_url"],
        description="New project notification to client",
        fallback_sms="Hi {client_name}, your project '{project_name}' has been created! Team Leader: {team_leader}. View: {portal_url}"
    ),
    
    "project_created_team": WhatsAppTemplate(
        name="4d_project_created_team",
        sid="HXa8d19f666431bbae451c42409d809cca",
        status=TemplateStatus.APPROVED,
        variables=["team_member_name", "project_name", "client_name", "portal_url"],
        description="New project notification to team",
        fallback_sms="Hi {team_member_name}, new project '{project_name}' for client {client_name}. View: {portal_url}"
    ),
    
    # Drawing Notifications
    "drawing_issued": WhatsAppTemplate(
        name="4d_drawing_issued",
        sid="HX379f0ac393af21dfebcb69cbcc339634",
        status=TemplateStatus.APPROVED,
        variables=["recipient_name", "drawing_name", "project_name", "revision", "portal_url"],
        description="Drawing issued notification",
        fallback_sms="Hi {recipient_name}, drawing '{drawing_name}' (Rev {revision}) issued for '{project_name}'. View: {portal_url}"
    ),
    
    # Task Notifications
    "task_assigned": WhatsAppTemplate(
        name="4d_task_assigned",
        sid="HXddd309318f53cb50eb38a4b40aaa13e2",
        status=TemplateStatus.APPROVED,
        variables=["assignee_name", "task_name", "project_name", "due_date", "portal_url"],
        description="Task assignment notification",
        fallback_sms="Hi {assignee_name}, task '{task_name}' assigned for '{project_name}'. Due: {due_date}. View: {portal_url}"
    ),
    
    # ============================================
    # PENDING TEMPLATES (Awaiting Meta approval)
    # Update SIDs once approved
    # ============================================
    
    "drawing_uploaded": WhatsAppTemplate(
        name="4d_drawing_uploaded",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["recipient_name", "project_name", "drawing_name", "uploader_name", "portal_url"],
        description="New drawing uploaded notification",
        fallback_sms="Hi {recipient_name}, new drawing '{drawing_name}' uploaded for '{project_name}' by {uploader_name}. View: {portal_url}"
    ),
    
    "drawing_revised": WhatsAppTemplate(
        name="4d_drawing_revised",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["recipient_name", "project_name", "drawing_name", "revision", "updater_name", "portal_url"],
        description="Drawing revision notification",
        fallback_sms="Hi {recipient_name}, drawing '{drawing_name}' revised to Rev {revision} for '{project_name}'. View: {portal_url}"
    ),
    
    "drawing_approved": WhatsAppTemplate(
        name="4d_drawing_approved",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["client_name", "project_name", "drawing_name", "revision", "portal_url"],
        description="Drawing approved notification",
        fallback_sms="Hi {client_name}, drawing '{drawing_name}' (Rev {revision}) approved for '{project_name}'. View: {portal_url}"
    ),
    
    "new_comment": WhatsAppTemplate(
        name="4d_new_comment",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["recipient_name", "commenter_name", "project_name", "comment_preview", "portal_url"],
        description="New comment notification",
        fallback_sms="Hi {recipient_name}, {commenter_name} commented on '{project_name}': \"{comment_preview}\" View: {portal_url}"
    ),
    
    "3d_images_uploaded": WhatsAppTemplate(
        name="4d_3d_images_uploaded",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["client_name", "project_name", "category", "count", "portal_url"],
        description="3D images uploaded notification",
        fallback_sms="Hi {client_name}, {count} new 3D images uploaded for '{project_name}' ({category}). View: {portal_url}"
    ),
    
    "project_update": WhatsAppTemplate(
        name="4d_project_update",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["client_name", "project_name", "percentage", "update_text", "portal_url"],
        description="Project status update notification",
        fallback_sms="Hi {client_name}, project '{project_name}' is now {percentage}% complete. {update_text} View: {portal_url}"
    ),
    
    "drawing_issued_contractor": WhatsAppTemplate(
        name="4d_drawing_issued_contractor",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["contractor_name", "project_name", "drawing_name", "revision", "contractor_type", "portal_url"],
        description="Drawing issued to contractor notification",
        fallback_sms="Hi {contractor_name}, drawing '{drawing_name}' (Rev {revision}) issued for '{project_name}'. Your role: {contractor_type}. View: {portal_url}"
    ),
    
    "revision_requested": WhatsAppTemplate(
        name="4d_revision_requested",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["team_leader_name", "project_name", "drawing_name", "requester_name", "reason", "portal_url"],
        description="Revision request notification",
        fallback_sms="Hi {team_leader_name}, revision requested for '{drawing_name}' on '{project_name}' by {requester_name}. Reason: {reason}. View: {portal_url}"
    ),
    
    "consultant_notification": WhatsAppTemplate(
        name="4d_consultant_notification",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["consultant_name", "project_name", "update_type", "details", "portal_url"],
        description="General consultant notification",
        fallback_sms="Hi {consultant_name}, update on '{project_name}': {update_type} - {details}. View: {portal_url}"
    ),
    
    "drawing_approval_needed": WhatsAppTemplate(
        name="4d_drawing_approval_needed",
        sid="PENDING_APPROVAL",
        status=TemplateStatus.PENDING,
        variables=["owner_name", "project_name", "drawing_name", "uploader_name", "portal_url"],
        description="Drawing approval request notification",
        fallback_sms="Hi {owner_name}, drawing '{drawing_name}' needs approval for '{project_name}'. Uploaded by: {uploader_name}. Review: {portal_url}"
    ),
}


def get_template(template_key: str) -> Optional[WhatsAppTemplate]:
    """Get a template by its key"""
    return TEMPLATES.get(template_key)


def is_template_approved(template_key: str) -> bool:
    """Check if a template is approved and ready to use"""
    template = TEMPLATES.get(template_key)
    return template is not None and template.status == TemplateStatus.APPROVED


def get_approved_templates() -> Dict[str, WhatsAppTemplate]:
    """Get all approved templates"""
    return {k: v for k, v in TEMPLATES.items() if v.status == TemplateStatus.APPROVED}


def get_pending_templates() -> Dict[str, WhatsAppTemplate]:
    """Get all pending templates"""
    return {k: v for k, v in TEMPLATES.items() if v.status == TemplateStatus.PENDING}


def update_template_sid(template_key: str, new_sid: str) -> bool:
    """
    Update a template SID after Meta approval.
    Call this when a pending template gets approved.
    """
    if template_key in TEMPLATES:
        TEMPLATES[template_key].sid = new_sid
        TEMPLATES[template_key].status = TemplateStatus.APPROVED
        return True
    return False
