"""
Magic Link Router
Handles authentication via magic link tokens from WhatsApp/Email notifications.

Flow:
1. User clicks magic link in notification
2. Backend validates token (exists, not expired, not used)
3. Backend marks token as used (single-use)
4. Backend creates authenticated session via HTTP-only cookie
5. Backend redirects to destination (no client-side token handling)
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import jwt

from services.magic_link_service import (
    consume_magic_token,
    get_user_for_token,
    build_destination_url
)
from utils.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Magic Links"])

db = get_database()

# JWT Configuration (same as main auth)
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days - same as normal login

# CRITICAL: Use frontend URL for redirects, NOT backend URL
# Magic links must redirect to React app, not backend API
FRONTEND_URL = os.environ.get('REACT_APP_FRONTEND_URL', 'https://pmapp-stability.preview.emergentagent.com')

# Cookie configuration
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds
COOKIE_SECURE = True  # Always secure for production
COOKIE_SAMESITE = "lax"  # Allow cross-site navigation while protecting against CSRF


def create_jwt_token(user: dict) -> str:
    """Create JWT token for authenticated user (same as normal login)"""
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    
    payload = {
        "sub": user.get("email"),  # Use email as subject (same as normal login)
        "user_id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "is_owner": user.get("is_owner", False),
        "name": user.get("name", ""),
        "exp": expiry,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.get("/magic/{token}")
async def handle_magic_link(token: str):
    """
    Handle magic link authentication.
    
    Flow:
    1. Validate token (exists, not expired, not used)
    2. Mark token as used (atomic operation)
    3. Get user and validate
    4. Create JWT and set HTTP-only cookie
    5. Redirect to destination
    """
    try:
        # Step 1 & 2: Validate and consume token (atomic)
        token_data = await consume_magic_token(token)
        
        if not token_data:
            # Token invalid, expired, or already used
            logger.warning(f"Invalid magic link access attempt: {token[:16]}...")
            
            # Redirect to login page with error message
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=link_expired&message=This+link+has+expired+or+already+been+used",
                status_code=302
            )
        
        # Step 3: Get and validate user
        user = await get_user_for_token(token_data)
        
        if not user:
            logger.warning(f"User not found for magic token: {token_data.get('user_id')}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=user_not_found",
                status_code=302
            )
        
        # Check user is approved
        if user.get("approval_status") != "approved":
            logger.warning(f"Unapproved user tried to use magic link: {user.get('id')}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=account_pending",
                status_code=302
            )
        
        # Step 4: Create JWT token
        jwt_token = create_jwt_token(user)
        
        # Step 5: Build destination URL and create redirect response
        destination = build_destination_url(token_data)
        redirect_url = f"{FRONTEND_URL}{destination}"
        
        # Log successful authentication
        logger.info(f"Magic link auth successful: user={user.get('id')}, dest={destination}")
        
        # Create redirect response with HTTP-only cookie
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Set HTTP-only secure cookie
        response.set_cookie(
            key=COOKIE_NAME,
            value=jwt_token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path="/"
        )
        
        # Also set a non-httponly cookie with user info for frontend display
        # (This is safe as it only contains display info, not the auth token)
        import json
        import urllib.parse
        user_info = json.dumps({
            "id": user.get("id", ""),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "role": user.get("role", ""),
            "is_owner": user.get("is_owner", False)
        })
        # URL encode the JSON to handle special characters
        encoded_user_info = urllib.parse.quote(user_info)
        response.set_cookie(
            key="user_info",
            value=encoded_user_info,
            max_age=COOKIE_MAX_AGE,
            httponly=False,  # Frontend can read this
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path="/"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Magic link error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=server_error",
            status_code=302
        )


@router.get("/magic/{token}/validate")
async def validate_magic_link(token: str):
    """
    Validate a magic link without consuming it.
    Used for preflight checks.
    """
    from services.magic_link_service import validate_magic_token
    
    token_data = await validate_magic_token(token)
    
    if not token_data:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "destination_type": token_data.get("destination_type"),
        "expires_at": token_data.get("expires_at")
    }
