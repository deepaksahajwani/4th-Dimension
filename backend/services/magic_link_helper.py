"""
Magic Link Helper for Notifications
Provides easy-to-use functions for generating magic links in notification triggers.
"""

import logging
from typing import Optional, Dict, Any

from services.magic_link_service import (
    generate_magic_token,
    get_magic_link_url,
    DestinationType
)
from utils.database import get_database

logger = logging.getLogger(__name__)

db = get_database()


async def create_project_magic_link(
    user_id: str,
    user_email: str,
    user_role: str,
    project_id: str,
    drawing_id: Optional[str] = None
) -> str:
    """
    Create a magic link to a project page.
    
    Args:
        user_id: The recipient user's ID
        user_email: The recipient's email
        user_role: The recipient's role
        project_id: The project to link to
        drawing_id: Optional - highlight specific drawing
    
    Returns:
        The full magic link URL
    """
    extra_params = {}
    if drawing_id:
        extra_params["drawing_id"] = drawing_id
    
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.PROJECT,
        destination_id=project_id,
        extra_params=extra_params
    )
    
    return get_magic_link_url(token)


async def create_drawing_magic_link(
    user_id: str,
    user_email: str,
    user_role: str,
    project_id: str,
    drawing_id: str
) -> str:
    """
    Create a magic link to a specific drawing.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.DRAWING,
        destination_id=drawing_id,
        extra_params={"project_id": project_id}
    )
    
    return get_magic_link_url(token)


async def create_drawing_review_magic_link(
    user_id: str,
    user_email: str,
    user_role: str,
    project_id: str,
    drawing_id: str
) -> str:
    """
    Create a magic link to the dedicated drawing review page.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.DRAWING_REVIEW,
        destination_id=drawing_id,
        extra_params={"project_id": project_id}
    )
    
    return get_magic_link_url(token)


async def create_image_review_magic_link(
    user_id: str,
    user_email: str,
    user_role: str,
    project_id: str,
    image_id: str
) -> str:
    """
    Create a magic link to the 3D image review page.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.IMAGE_REVIEW,
        destination_id=image_id,
        extra_params={"project_id": project_id}
    )
    
    return get_magic_link_url(token)


async def create_comment_magic_link(
    user_id: str,
    user_email: str,
    user_role: str,
    project_id: str,
    drawing_id: str,
    comment_id: str
) -> str:
    """
    Create a magic link to a specific comment.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.COMMENT,
        destination_id=comment_id,
        extra_params={
            "project_id": project_id,
            "drawing_id": drawing_id
        }
    )
    
    return get_magic_link_url(token)


async def create_dashboard_magic_link(
    user_id: str,
    user_email: str,
    user_role: str
) -> str:
    """
    Create a magic link to the dashboard.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.DASHBOARD,
        destination_id="main"
    )
    
    return get_magic_link_url(token)


async def create_pending_approvals_magic_link(
    user_id: str,
    user_email: str,
    user_role: str
) -> str:
    """
    Create a magic link to the pending approvals page.
    """
    token = await generate_magic_token(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        destination_type=DestinationType.PENDING_APPROVALS,
        destination_id="list"
    )
    
    return get_magic_link_url(token)


async def get_user_info_for_magic_link(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user info needed for magic link generation.
    """
    user = await db.users.find_one(
        {"id": user_id, "deleted_at": None},
        {"_id": 0, "id": 1, "email": 1, "role": 1}
    )
    return user


async def get_user_info_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user info by email for magic link generation.
    """
    user = await db.users.find_one(
        {"email": email, "deleted_at": None},
        {"_id": 0, "id": 1, "email": 1, "role": 1}
    )
    return user
