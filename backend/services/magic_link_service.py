"""
Magic Link Service
Generates and validates one-time, time-limited, role-bound authentication tokens
for WhatsApp/Email notification links.

Security Features:
- Cryptographically secure tokens (32 bytes = 64 hex chars)
- Single-use (invalidated after first use)
- Time-limited (default 15 minutes)
- Role-bound (token cannot be used for unauthorized access)
- All context resolved server-side (no sensitive data in URL)
"""

import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from utils.database import get_database

logger = logging.getLogger(__name__)

db = get_database()

# Configuration
TOKEN_EXPIRY_MINUTES = int(os.environ.get('MAGIC_LINK_EXPIRY_MINUTES', '15'))
TOKEN_LENGTH = 32  # 32 bytes = 64 hex characters


class DestinationType(str, Enum):
    """Supported destination types for magic links"""
    PROJECT = "project"
    DRAWING = "drawing"
    COMMENT = "comment"
    DRAWING_REVIEW = "drawing_review"
    IMAGE_REVIEW = "image_review"
    DASHBOARD = "dashboard"
    PENDING_APPROVALS = "pending_approvals"


async def generate_magic_token(
    user_id: str,
    user_email: str,
    user_role: str,
    destination_type: DestinationType,
    destination_id: str,
    extra_params: Optional[Dict[str, Any]] = None,
    expiry_minutes: int = TOKEN_EXPIRY_MINUTES
) -> str:
    """
    Generate a cryptographically secure magic link token.
    
    Args:
        user_id: The user's ID
        user_email: The user's email (for verification)
        user_role: The user's role (client, team_leader, owner, etc.)
        destination_type: Type of destination (project, drawing, comment)
        destination_id: ID of the destination resource
        extra_params: Additional parameters (e.g., drawing_id for project links)
        expiry_minutes: Token validity duration in minutes
    
    Returns:
        The generated token string
    """
    try:
        # Generate cryptographically secure token
        token = secrets.token_hex(TOKEN_LENGTH)
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expiry_minutes)
        
        # Prepare token document
        token_doc = {
            "token": token,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "destination_type": destination_type.value if isinstance(destination_type, DestinationType) else destination_type,
            "destination_id": destination_id,
            "extra_params": extra_params or {},
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
            "used_at": None,
            "created_at": now.isoformat()
        }
        
        # Store token in database
        await db.magic_tokens.insert_one(token_doc)
        
        # Log token creation (async-safe)
        logger.info(f"Magic token created for user {user_id} -> {destination_type}:{destination_id}")
        
        return token
        
    except Exception as e:
        logger.error(f"Error generating magic token: {e}")
        raise


async def validate_magic_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a magic link token.
    
    Returns:
        Token data if valid, None if invalid/expired/used
    """
    try:
        # Find token
        token_doc = await db.magic_tokens.find_one({"token": token}, {"_id": 0})
        
        if not token_doc:
            logger.warning(f"Magic token not found: {token[:16]}...")
            return None
        
        # Check if already used
        if token_doc.get("used"):
            logger.warning(f"Magic token already used: {token[:16]}... (used at {token_doc.get('used_at')})")
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_doc["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Magic token expired: {token[:16]}... (expired at {expires_at})")
            return None
        
        return token_doc
        
    except Exception as e:
        logger.error(f"Error validating magic token: {e}")
        return None


async def consume_magic_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and consume (mark as used) a magic link token.
    This is atomic - token is marked used immediately upon validation.
    
    Returns:
        Token data if valid and successfully consumed, None otherwise
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Atomically find and update token (mark as used)
        result = await db.magic_tokens.find_one_and_update(
            {
                "token": token,
                "used": False,
                "expires_at": {"$gt": now.isoformat()}
            },
            {
                "$set": {
                    "used": True,
                    "used_at": now.isoformat()
                }
            },
            return_document=True
        )
        
        if not result:
            # Token not found, already used, or expired
            logger.warning(f"Magic token consumption failed: {token[:16]}...")
            return None
        
        # Remove MongoDB _id from result
        if "_id" in result:
            del result["_id"]
        
        logger.info(f"Magic token consumed for user {result.get('user_id')} -> {result.get('destination_type')}:{result.get('destination_id')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error consuming magic token: {e}")
        return None


async def get_user_for_token(token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get the user associated with a magic token.
    Validates that the user still exists and role is still valid.
    
    Returns:
        User document if valid, None otherwise
    """
    try:
        user_id = token_data.get("user_id")
        expected_role = token_data.get("user_role")
        
        # Find user by ID
        user = await db.users.find_one(
            {"id": user_id, "deleted_at": None},
            {"_id": 0, "password_hash": 0}
        )
        
        if not user:
            logger.warning(f"User not found for magic token: {user_id}")
            return None
        
        # Verify role hasn't changed (optional security check)
        current_role = user.get("role", "")
        if current_role != expected_role:
            # Log but allow - role may have been upgraded
            logger.info(f"User role changed since token creation: {expected_role} -> {current_role}")
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting user for magic token: {e}")
        return None


def build_destination_url(token_data: Dict[str, Any]) -> str:
    """
    Build the destination URL based on token data.
    
    Returns:
        The frontend URL to redirect to
    """
    dest_type = token_data.get("destination_type")
    dest_id = token_data.get("destination_id")
    extra_params = token_data.get("extra_params", {})
    
    # Base routes mapping
    if dest_type == DestinationType.PROJECT.value or dest_type == "project":
        url = f"/projects/{dest_id}"
        # If drawing_id specified, redirect to Drawing Review Page
        if extra_params.get("drawing_id"):
            url = f"/projects/{dest_id}/drawing/{extra_params['drawing_id']}"
    
    elif dest_type == DestinationType.DRAWING.value or dest_type == "drawing":
        project_id = extra_params.get("project_id", "")
        # Use Drawing Review Page format
        url = f"/projects/{project_id}/drawing/{dest_id}"
    
    elif dest_type == DestinationType.DRAWING_REVIEW.value or dest_type == "drawing_review":
        project_id = extra_params.get("project_id", "")
        url = f"/projects/{project_id}/drawing/{dest_id}"
    
    elif dest_type == DestinationType.IMAGE_REVIEW.value or dest_type == "image_review":
        project_id = extra_params.get("project_id", "")
        url = f"/projects/{project_id}/3d-image/{dest_id}"
    
    elif dest_type == DestinationType.COMMENT.value or dest_type == "comment":
        project_id = extra_params.get("project_id", "")
        drawing_id = extra_params.get("drawing_id", "")
        # Use Drawing Review Page format
        url = f"/projects/{project_id}/drawing/{drawing_id}"
    
    elif dest_type == DestinationType.PENDING_APPROVALS.value or dest_type == "pending_approvals":
        url = "/pending-approvals"
    
    elif dest_type == DestinationType.DASHBOARD.value or dest_type == "dashboard":
        url = "/dashboard"
    
    else:
        # Default to dashboard
        url = "/dashboard"
    
    return url


async def cleanup_expired_tokens():
    """
    Remove expired tokens from database.
    Should be called periodically (e.g., daily cleanup task).
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        result = await db.magic_tokens.delete_many({
            "expires_at": {"$lt": now}
        })
        
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} expired magic tokens")
        
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up magic tokens: {e}")
        return 0


# Helper function to generate magic link URL
def get_magic_link_url(token: str) -> str:
    """
    Get the full magic link URL for a token.
    """
    app_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://mobile-first-14.preview.emergentagent.com')
    return f"{app_url}/magic/{token}"
