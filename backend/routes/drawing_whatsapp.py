"""
Drawing WhatsApp Routes
Send drawings via WhatsApp with file attachments
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from motor.motor_asyncio import AsyncIOMotorClient
import jwt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["drawings-whatsapp"])

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")


async def get_current_user_from_token(authorization: str = Header(None)):
    """Extract and verify user from JWT token - simplified auth for routes"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_identifier = payload.get("sub") or payload.get("user_id")
        
        if not user_identifier:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_identifier}, {"_id": 0})
        if not user:
            user = await db.users.find_one({"email": user_identifier}, {"_id": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/drawings/{drawing_id}/send-whatsapp")
async def send_drawing_via_whatsapp(
    drawing_id: str,
    phone_number: str = Query(..., description="Recipient phone number"),
    include_file: bool = Query(True, description="Include drawing file as attachment"),
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Send drawing approval request via WhatsApp with optional file attachment.
    The drawing file (PDF/image) can be sent directly on WhatsApp.
    """
    try:
        drawing = await db.project_drawings.find_one(
            {"id": drawing_id, "deleted_at": None},
            {"_id": 0}
        )
        
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        project = await db.projects.find_one(
            {"id": drawing.get('project_id'), "deleted_at": None},
            {"_id": 0}
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        is_owner = current_user.get('is_owner', False)
        is_team_leader = project.get('team_leader_id') == current_user.get('id')
        
        if not is_owner and not is_team_leader:
            raise HTTPException(status_code=403, detail="Not authorized to send this drawing")
        
        app_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://pmapp-stability.preview.emergentagent.com')
        # Use Drawing Review Page format
        drawing_link = f"{app_url}/projects/{project['id']}/drawing/{drawing_id}"
        
        message = (
            f"📋 *Drawing for Review*\n\n"
            f"📁 *Drawing:* {drawing.get('name', 'Unnamed')}\n"
            f"🏗️ *Project:* {project.get('title', 'Unknown')}\n"
            f"📂 *Category:* {drawing.get('category', 'N/A')}\n\n"
        )
        
        if drawing.get('under_review'):
            message += "⏳ *Status:* Pending Approval\n\n"
            message += "Please review and approve this drawing.\n\n"
        
        message += f"🔗 *View in portal:* {drawing_link}"
        
        media_url = None
        if include_file and drawing.get('file_url'):
            file_url = drawing.get('file_url')
            if file_url.startswith('/'):
                media_url = f"{app_url}{file_url}"
            else:
                media_url = file_url
        
        try:
            from async_notifications import async_notification_service
            
            if media_url:
                async_notification_service.queue_whatsapp_with_media(
                    phone=phone_number,
                    media_url=media_url,
                    message=message
                )
                logger.info(f"Queued WhatsApp with media for drawing {drawing_id}")
            else:
                async_notification_service.queue_whatsapp(
                    phone=phone_number,
                    message=message
                )
            
            await db.whatsapp_notifications.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": current_user.get('id'),
                "recipient_phone": phone_number,
                "message_type": "drawing_review",
                "drawing_id": drawing_id,
                "project_id": project['id'],
                "include_file": include_file,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "delivery_status": "queued"
            })
            
            return {
                "success": True,
                "message": "Drawing sent to WhatsApp queue",
                "drawing_name": drawing.get('name'),
                "project_name": project.get('title'),
                "include_file": include_file and bool(media_url)
            }
            
        except ImportError:
            from notification_service import notification_service
            await notification_service.send_whatsapp(phone_number, message)
            
            return {
                "success": True,
                "message": "Drawing notification sent via WhatsApp (text only)",
                "drawing_name": drawing.get('name')
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send drawing via WhatsApp error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drawings/{drawing_id}/request-approval")
async def request_drawing_approval(
    drawing_id: str,
    send_file: bool = Query(True, description="Send drawing file on WhatsApp"),
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Request approval for a drawing - sends notification to owner with optional file attachment.
    """
    try:
        drawing = await db.project_drawings.find_one(
            {"id": drawing_id, "deleted_at": None},
            {"_id": 0}
        )
        
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        project = await db.projects.find_one(
            {"id": drawing.get('project_id'), "deleted_at": None},
            {"_id": 0}
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        
        if not owner or not owner.get('mobile'):
            raise HTTPException(status_code=400, detail="Owner contact not available")
        
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {
                "under_review": True,
                "review_requested_at": datetime.now(timezone.utc).isoformat(),
                "review_requested_by": current_user.get('id')
            }}
        )
        
        app_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://pmapp-stability.preview.emergentagent.com')
        # Use Drawing Review Page format
        drawing_link = f"{app_url}/projects/{project['id']}/drawing/{drawing_id}"
        
        message = (
            f"📋 *Approval Required*\n\n"
            f"📁 *Drawing:* {drawing.get('name', 'Unnamed')}\n"
            f"🏗️ *Project:* {project.get('title', 'Unknown')}\n"
            f"👤 *Submitted by:* {current_user.get('name', 'Team Member')}\n\n"
            f"Please review and approve this drawing.\n\n"
            f"🔗 {drawing_link}"
        )
        
        media_url = None
        if send_file and drawing.get('file_url'):
            file_url = drawing.get('file_url')
            if file_url.startswith('/'):
                media_url = f"{app_url}{file_url}"
            else:
                media_url = file_url
        
        try:
            from async_notifications import async_notification_service
            
            if media_url:
                async_notification_service.queue_whatsapp_with_media(
                    phone=owner['mobile'],
                    media_url=media_url,
                    message=message
                )
            else:
                async_notification_service.queue_whatsapp(
                    phone=owner['mobile'],
                    message=message
                )
            
            await db.notifications.insert_one({
                "id": f"notif_{datetime.now(timezone.utc).timestamp()}_{owner['id']}",
                "user_id": owner['id'],
                "type": "drawing_approval_needed",
                "title": "Drawing Approval Required",
                "message": f"{drawing.get('name')} from {project.get('title')} needs your approval",
                "link": f"/projects/{project['id']}/drawing/{drawing_id}",
                "project_id": project['id'],
                "read": False,
                "created_at": datetime.now(timezone.utc)
            })
            
            return {
                "success": True,
                "message": "Approval request sent",
                "drawing_name": drawing.get('name'),
                "sent_with_file": bool(media_url)
            }
            
        except ImportError:
            from notification_service import notification_service
            await notification_service.send_whatsapp(owner['mobile'], message)
            
            return {
                "success": True,
                "message": "Approval request sent (text only)"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request drawing approval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dummy function for compatibility
def set_auth_dependency(auth_func):
    """Legacy function - no longer needed with Header-based auth"""
    pass
