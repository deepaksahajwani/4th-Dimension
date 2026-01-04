"""
Comments Router - Project and Drawing Comments
Refactored from server.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from pathlib import Path
import logging
import uuid
import os

from utils.auth import get_current_user, User
from utils.database import get_database
from pydantic import BaseModel

db = get_database()
router = APIRouter(tags=["Comments"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


from typing import List

class DrawingCommentCreate(BaseModel):
    comment_text: str
    requires_revision: bool = False


class DrawingCommentUpdate(BaseModel):
    comment_text: str


# ==================== PROJECT COMMENTS ====================

@router.get("/projects/{project_id}/comments")
async def get_project_comments(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a project"""
    try:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comments = await db.project_comments.find(
            {"project_id": project_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(500)
        
        return comments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch comments")


@router.post("/projects/{project_id}/comments")
async def create_project_comment(
    project_id: str,
    text: str = Form(""),
    file: UploadFile = File(None),
    voice_note: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a project (supports text, file, voice note)"""
    try:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comment_id = str(uuid.uuid4())
        comment = {
            "id": comment_id,
            "project_id": project_id,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "user_role": current_user.role,
            "text": text,
            "file_url": None,
            "file_name": None,
            "voice_note_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Handle file upload
        if file and file.filename:
            file_ext = os.path.splitext(file.filename)[1]
            safe_filename = f"{comment_id}_file{file_ext}"
            file_path = UPLOAD_DIR / "comments" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            comment["file_url"] = f"/api/uploads/comments/{safe_filename}"
            comment["file_name"] = file.filename
        
        # Handle voice note upload
        if voice_note and voice_note.filename:
            voice_ext = os.path.splitext(voice_note.filename)[1] or ".webm"
            safe_voice_name = f"{comment_id}_voice{voice_ext}"
            voice_path = UPLOAD_DIR / "comments" / safe_voice_name
            voice_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await voice_note.read()
            with open(voice_path, "wb") as f:
                f.write(content)
            
            comment["voice_note_url"] = f"/api/uploads/comments/{safe_voice_name}"
        
        await db.project_comments.insert_one(comment)
        
        # Send notifications
        try:
            from notification_triggers_v2 import notify_project_comment
            await notify_project_comment(
                project_id=project_id,
                project_name=project.get('title', 'Project'),
                commenter_id=current_user.id,
                commenter_name=current_user.name,
                commenter_role=current_user.role,
                comment_text=text[:100] if text else "Voice/File message"
            )
        except Exception as e:
            logger.warning(f"Failed to send comment notification: {e}")
        
        return {"message": "Comment added successfully", "comment": comment}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create comment")


@router.delete("/projects/{project_id}/comments/{comment_id}")
async def delete_project_comment(
    project_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a project comment (owner/admin or comment author only)"""
    try:
        comment = await db.project_comments.find_one({"id": comment_id}, {"_id": 0})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check permission
        if comment["user_id"] != current_user.id and not current_user.is_owner and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        # Delete associated files
        if comment.get("file_url"):
            file_path = UPLOAD_DIR / comment["file_url"].replace("/api/uploads/", "")
            if file_path.exists():
                file_path.unlink()
        
        if comment.get("voice_note_url"):
            voice_path = UPLOAD_DIR / comment["voice_note_url"].replace("/api/uploads/", "")
            if voice_path.exists():
                voice_path.unlink()
        
        await db.project_comments.delete_one({"id": comment_id})
        
        return {"message": "Comment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")


# ==================== DRAWING COMMENTS ====================

@router.post("/drawings/{drawing_id}/comments")
async def create_drawing_comment(
    drawing_id: str,
    comment_data: DrawingCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a drawing"""
    from models_projects import DrawingComment
    
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    comment = DrawingComment(
        drawing_id=drawing_id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        comment_text=comment_data.comment_text
    )
    
    comment_dict = comment.model_dump()
    comment_dict['created_at'] = comment_dict['created_at'].isoformat()
    comment_dict['updated_at'] = comment_dict['updated_at'].isoformat()
    
    await db.drawing_comments.insert_one(comment_dict)
    
    # If comment requires revision, update drawing status
    if comment_data.requires_revision:
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {
                "$set": {
                    "has_pending_revision": True,
                    "status": "revision_needed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Drawing {drawing_id} marked for revision due to comment")
    
    # Increment comment count
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {
            "$inc": {
                "comment_count": 1,
                "unread_comments": 1
            }
        }
    )
    
    # Create in-app notifications
    try:
        project = await db.projects.find_one({"id": drawing.get("project_id")}, {"_id": 0})
        if project:
            notification_users = set()
            
            if project.get("lead_architect_id") and project["lead_architect_id"] != current_user.id:
                notification_users.add(project["lead_architect_id"])
            
            owner = await db.users.find_one({"role": "owner"}, {"_id": 0, "id": 1})
            if owner and owner["id"] != current_user.id:
                notification_users.add(owner["id"])
            
            for user_id in notification_users:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "comment_added",
                    "title": "New Comment on Drawing",
                    "message": f"{current_user.name} commented on {drawing.get('name', 'a drawing')} in {project.get('title', 'a project')}",
                    "related_id": comment_dict["id"],
                    "related_type": "comment",
                    "project_id": drawing.get("project_id"),
                    "project_name": project.get("title"),
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by_id": current_user.id,
                    "created_by_name": current_user.name
                }
                await db.notifications.insert_one(notification)
    except Exception as e:
        logger.warning(f"Failed to create comment notifications: {e}")
    
    # Send WhatsApp notification
    try:
        from notification_triggers_v2 import notify_owner_drawing_comment
        await notify_owner_drawing_comment(
            drawing_id=drawing_id,
            drawing_name=drawing.get('name', 'Drawing'),
            project_id=drawing.get('project_id'),
            project_name=project.get('title', 'Project') if project else 'Project',
            commenter_id=current_user.id,
            commenter_name=current_user.name,
            comment_text=comment_data.comment_text
        )
    except Exception as e:
        logger.warning(f"Failed to send WhatsApp notification for comment: {e}")
    
    return comment_dict


@router.get("/drawings/{drawing_id}/comments")
async def get_drawing_comments(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a drawing"""
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    comments = await db.drawing_comments.find(
        {"drawing_id": drawing_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Mark as read if user is owner or team leader
    if current_user.is_owner or current_user.role == "team_leader":
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {"unread_comments": 0}}
        )
    
    return comments


@router.delete("/drawings/{drawing_id}/comments/{comment_id}")
async def delete_drawing_comment(
    drawing_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a drawing comment"""
    comment = await db.drawing_comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check permission
    if comment["user_id"] != current_user.id and not current_user.is_owner and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    await db.drawing_comments.delete_one({"id": comment_id})
    
    # Decrement comment count
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$inc": {"comment_count": -1}}
    )
    
    return {"message": "Comment deleted successfully"}


@router.put("/drawings/{drawing_id}/comments/{comment_id}/read")
async def mark_comment_read(
    drawing_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a comment as read"""
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Comment marked as read"}


# ==================== DRAWING COMMENT UPDATES ====================

@router.put("/drawings/comments/{comment_id}")
async def update_drawing_comment(
    comment_id: str,
    comment_data: DrawingCommentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by comment author)"""
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {
            "comment_text": comment_data.comment_text,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_comment = await db.drawing_comments.find_one({"id": comment_id}, {"_id": 0})
    return updated_comment


@router.delete("/drawings/comments/{comment_id}")
async def delete_drawing_comment_by_id(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by comment author) - soft delete"""
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Comment deleted successfully"}


@router.post("/drawings/comments/{comment_id}/upload-reference")
async def upload_comment_reference(
    comment_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple reference files (images/PDFs) for a comment"""
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add files to your own comments")
    
    uploaded_files = []
    current_files = comment.get('reference_files', [])
    
    # Allowed file types
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
        '.dwg', '.dxf', '.dwf', '.dgn',
        '.xls', '.xlsx', '.csv',
        '.ppt', '.pptx',
        '.zip', '.rar', '.7z'
    ]
    
    upload_dir = Path("uploads/comment_references")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed"
            )
        
        unique_filename = f"{comment_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(uploaded_files)}{file_extension}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_url = f"/uploads/comment_references/{unique_filename}"
        uploaded_files.append({
            "url": file_url,
            "filename": file.filename,
            "original_name": file.filename
        })
        current_files.append(file_url)
    
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"reference_files": current_files}}
    )
    
    return {
        "uploaded_files": uploaded_files,
        "total_files": len(current_files),
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)"
    }


@router.post("/drawings/comments/{comment_id}/upload-voice")
async def upload_comment_voice_note(
    comment_id: str,
    voice_note: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload voice note for a comment"""
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add voice notes to your own comments")
    
    allowed_extensions = ['.webm', '.mp3', '.wav', '.m4a', '.ogg']
    file_extension = Path(voice_note.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only audio files are allowed")
    
    upload_dir = Path("uploads/voice_notes")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"voice_{comment_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.webm"
    file_path = upload_dir / unique_filename
    
    with open(file_path, "wb") as buffer:
        content = await voice_note.read()
        buffer.write(content)
    
    voice_url = f"/uploads/voice_notes/{unique_filename}"
    
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"voice_note_url": voice_url}}
    )
    
    # Send notification for voice note
    try:
        drawing = await db.project_drawings.find_one({"id": comment.get("drawing_id")}, {"_id": 0})
        if drawing:
            from notification_triggers import notify_voice_note_added
            await notify_voice_note_added(
                project_id=drawing.get("project_id"),
                drawing_name=drawing.get("name", "Unknown Drawing"),
                commenter_id=current_user.id,
                comment_id=comment_id
            )
    except Exception as e:
        logger.warning(f"Failed to send voice note notification: {e}")
    
    return {"voice_url": voice_url, "message": "Voice note uploaded successfully"}


# ==================== FILE SERVING ====================

@router.get("/comments/file/{filename}")
async def get_comment_file(filename: str):
    """Serve comment file attachments (legacy path)"""
    file_path = Path("/app/backend/uploads/comments") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path))


@router.get("/comments/voice/{filename}")
async def get_comment_voice(filename: str):
    """Serve comment voice notes (legacy path)"""
    file_path = Path("/app/backend/uploads/voice_notes") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Voice note not found")
    return FileResponse(str(file_path), media_type="audio/webm")


@router.get("/uploads/comments/{filename}")
async def serve_comment_file(filename: str):
    """Serve uploaded comment files"""
    file_path = UPLOAD_DIR / "comments" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    extension = file_path.suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webm': 'audio/webm',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4'
    }
    
    media_type = media_types.get(extension, 'application/octet-stream')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        }
    )
