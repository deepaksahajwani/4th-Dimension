"""
Magic Link Router
Handles authentication via magic link tokens from WhatsApp/Email notifications.

Flow:
1. User clicks magic link in notification
2. Backend validates token (exists, not expired, not used)
3. Backend marks token as used (single-use)
4. Backend creates authenticated session (JWT)
5. Backend redirects to destination with auth cookie/token
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse, HTMLResponse
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

APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://slim-api.preview.emergentagent.com')


def create_jwt_token(user: dict) -> str:
    """Create JWT token for authenticated user (same as normal login)"""
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    
    payload = {
        "sub": user.get("id"),
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
async def handle_magic_link(token: str, response: Response):
    """
    Handle magic link authentication.
    
    Flow:
    1. Validate token (exists, not expired, not used)
    2. Mark token as used (atomic operation)
    3. Get user and validate
    4. Create JWT session
    5. Redirect to destination with auth
    """
    try:
        # Step 1 & 2: Validate and consume token (atomic)
        token_data = await consume_magic_token(token)
        
        if not token_data:
            # Token invalid, expired, or already used
            logger.warning(f"Invalid magic link access attempt: {token[:16]}...")
            
            # Redirect to login page with error message
            return RedirectResponse(
                url=f"{APP_URL}/login?error=link_expired&message=This link has expired or already been used. Please log in normally.",
                status_code=302
            )
        
        # Step 3: Get and validate user
        user = await get_user_for_token(token_data)
        
        if not user:
            logger.warning(f"User not found for magic token: {token_data.get('user_id')}")
            return RedirectResponse(
                url=f"{APP_URL}/login?error=user_not_found",
                status_code=302
            )
        
        # Check user is approved
        if user.get("approval_status") != "approved":
            logger.warning(f"Unapproved user tried to use magic link: {user.get('id')}")
            return RedirectResponse(
                url=f"{APP_URL}/login?error=account_pending",
                status_code=302
            )
        
        # Step 4: Create JWT token
        jwt_token = create_jwt_token(user)
        
        # Step 5: Build destination URL
        destination = build_destination_url(token_data)
        
        # Log successful authentication
        logger.info(f"Magic link auth successful: user={user.get('id')}, dest={destination}")
        
        # Create redirect URL with token in query param
        # Frontend will extract this and store in localStorage
        redirect_url = f"{APP_URL}{destination}"
        
        # Return HTML that stores token and redirects
        # This is more reliable than cookie-based approach for cross-domain scenarios
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authenticating...</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 16px;
                    backdrop-filter: blur(10px);
                }}
                .spinner {{
                    border: 4px solid rgba(255,255,255,0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                h2 {{ margin: 0 0 10px; font-weight: 500; }}
                p {{ margin: 0; opacity: 0.8; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h2>Authenticating...</h2>
                <p>Please wait while we sign you in</p>
            </div>
            <script>
                // Store the JWT token
                localStorage.setItem('token', '{jwt_token}');
                
                // Store user info for immediate use
                localStorage.setItem('user', JSON.stringify({{
                    id: '{user.get("id", "")}',
                    email: '{user.get("email", "")}',
                    name: '{user.get("name", "")}',
                    role: '{user.get("role", "")}',
                    is_owner: {str(user.get("is_owner", False)).lower()}
                }}));
                
                // Redirect to destination
                setTimeout(function() {{
                    window.location.href = '{destination}';
                }}, 500);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content, status_code=200)
        
    except Exception as e:
        logger.error(f"Magic link error: {e}")
        return RedirectResponse(
            url=f"{APP_URL}/login?error=server_error",
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
