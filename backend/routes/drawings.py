"""
Drawing Management Routes
Handles drawing operations, uploads, comments, and issue notifications
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging
from uuid import uuid4
from pathlib import Path

from utils.auth import get_current_user, User
from utils.database import get_database
from models_projects import (
    ProjectDrawing, ProjectDrawingUpdate, DrawingStatus,
    DrawingComment, DrawingCommentCreate, DrawingCommentUpdate
)
from drawing_templates import get_template_drawings

db = get_database()
router = APIRouter(prefix="/drawings", tags=["drawings"])
logger = logging.getLogger(__name__)

# File storage settings
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/{drawing_id}")
async def get_drawing(drawing_id: str, current_user: User = Depends(get_current_user)):
    """Get drawing by ID"""
    drawing = await db.project_drawings.find_one({"id": drawing_id, "deleted_at": None}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return drawing


@router.put("/{drawing_id}")
async def update_drawing(
    drawing_id: str,
    drawing_data: ProjectDrawingUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update drawing with issue notification"""
    update_data = drawing_data.model_dump(exclude_unset=True)
    
    # Handle status change to 'issued'
    if update_data.get('status') == 'issued':
        update_data['issued_at'] = datetime.now(timezone.utc).isoformat()
        update_data['is_issued'] = True
        
        # Get the current drawing to find its project and sequence
        current_drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        if current_drawing:
            project_id = current_drawing.get('project_id')
            current_sequence = current_drawing.get('sequence_number', 0)
            
            # Find next drawing in sequence and activate it
            next_drawing = await db.project_drawings.find_one({
                "project_id": project_id,
                "sequence_number": current_sequence + 1,
                "deleted_at": None
            }, {"_id": 0})
            
            if next_drawing:
                # Set due date for next drawing (3 days from now)
                next_due_date = datetime.now(timezone.utc) + timedelta(days=3)
                await db.project_drawings.update_one(
                    {"id": next_drawing['id']},
                    {"$set": {
                        "is_active": True,
                        "due_date": next_due_date.isoformat(),
                        "status": DrawingStatus.PLANNED.value
                    }}
                )
                
                # Create new upcoming drawing from template
                category = current_drawing.get('category')
                template_drawings = get_template_drawings(category)
                new_sequence = current_sequence + 3  # Always 3 ahead
                
                if template_drawings and new_sequence <= len(template_drawings):
                    new_drawing_name = template_drawings[new_sequence - 1]
                    new_drawing = ProjectDrawing(
                        project_id=project_id,
                        category=category,
                        name=new_drawing_name,
                        status=DrawingStatus.PLANNED,
                        due_date=None,
                        is_issued=False,
                        revision_count=0,
                        sequence_number=new_sequence,
                        is_active=False,
                        assigned_to=current_drawing.get('assigned_to'),
                        priority="medium"
                    )
                    new_drawing_dict = new_drawing.model_dump()
                    for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                        if new_drawing_dict.get(field):
                            new_drawing_dict[field] = new_drawing_dict[field].isoformat() if isinstance(new_drawing_dict[field], datetime) else new_drawing_dict[field]
                    
                    await db.project_drawings.insert_one(new_drawing_dict)
                    logger.info(f"Created new drawing #{new_sequence}: {new_drawing_name}")
    
    result = await db.project_drawings.update_one(
        {"id": drawing_id, "deleted_at": None},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    return {"message": "Drawing updated successfully"}


@router.patch("/{drawing_id}/mark-not-applicable")
async def mark_drawing_not_applicable(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark drawing as not applicable and advance sequence"""
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Mark as N/A
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {
            "is_not_applicable": True,
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Advance sequence logic (same as issuing)
    project_id = drawing.get('project_id')
    current_sequence = drawing.get('sequence_number', 0)
    
    next_drawing = await db.project_drawings.find_one({
        "project_id": project_id,
        "sequence_number": current_sequence + 1,
        "deleted_at": None
    }, {"_id": 0})
    
    if next_drawing:
        next_due_date = datetime.now(timezone.utc) + timedelta(days=3)
        await db.project_drawings.update_one(
            {"id": next_drawing['id']},
            {"$set": {
                "is_active": True,
                "due_date": next_due_date.isoformat(),
                "status": DrawingStatus.PLANNED.value
            }}
        )
    
    return {"message": "Drawing marked as not applicable"}


@router.post("/{drawing_id}/notify-issue")
async def notify_drawing_issue(
    drawing_id: str,
    recipient_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Send notification when drawing is issued"""
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    try:
        from notification_triggers_v2 import notify_drawing_issued
        await notify_drawing_issued(
            project_id=drawing['project_id'],
            drawing_id=drawing_id,
            recipient_ids=recipient_ids,
            issued_by_id=current_user.id
        )
        return {"message": "Notification sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/{drawing_id}/comments")
async def add_drawing_comment(
    drawing_id: str,
    comment_data: DrawingCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Add comment to drawing"""
    comment = DrawingComment(
        id=str(uuid4()),
        drawing_id=drawing_id,
        user_id=current_user.id,
        user_name=current_user.name,
        comment_text=comment_data.comment_text,
        reference_files=comment_data.reference_files or [],
        voice_note_url=comment_data.voice_note_url,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    comment_dict = comment.model_dump()
    comment_dict['created_at'] = comment_dict['created_at'].isoformat()
    comment_dict['updated_at'] = comment_dict['updated_at'].isoformat()
    
    await db.drawing_comments.insert_one(comment_dict)
    
    return comment


@router.get("/{drawing_id}/comments")
async def get_drawing_comments(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a drawing"""
    comments = await db.drawing_comments.find(
        {"drawing_id": drawing_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return comments


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: str,
    comment_data: DrawingCommentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a comment"""
    update_data = comment_data.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.drawing_comments.update_one(
        {"id": comment_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found or unauthorized")
    
    return {"message": "Comment updated successfully"}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment"""
    result = await db.drawing_comments.update_one(
        {"id": comment_id, "user_id": current_user.id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found or unauthorized")
    
    return {"message": "Comment deleted successfully"}


@router.post("/upload")
async def upload_drawing_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    drawing_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload drawing file"""
    # Create project-specific upload directory
    project_upload_dir = UPLOAD_DIR / project_id
    project_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = project_upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "filename": unique_filename,
        "file_path": str(file_path),
        "url": f"/uploads/{project_id}/{unique_filename}"
    }


@router.delete("/{drawing_id}")
async def delete_drawing(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete a drawing"""
    result = await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    return {"message": "Drawing deleted successfully"}
