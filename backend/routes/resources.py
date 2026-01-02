"""
Resource Management API Routes
CRUD operations for company resources (documents, templates, tutorials, etc.)
"""

import os
import logging
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from motor.motor_asyncio import AsyncIOMotorClient

from models_resources import (
    Resource, ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceCategory, ResourceType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# File upload directory
UPLOAD_DIR = "/app/backend/uploads/resources"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import auth dependency from server
from server import get_current_user, require_owner, User


@router.get("", response_model=List[ResourceResponse])
async def get_resources(
    category: Optional[ResourceCategory] = None,
    search: Optional[str] = None,
    featured_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Get all resources (filtered by user's role visibility)
    """
    try:
        query = {}
        
        # Filter by category
        if category:
            query["category"] = category.value
        
        # Filter featured only
        if featured_only:
            query["featured"] = True
        
        # Text search
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]
        
        # Get resources
        resources = await db.resources.find(query, {"_id": 0}).sort([
            ("featured", -1),
            ("order", 1),
            ("created_at", -1)
        ]).to_list(1000)
        
        # Filter by visibility
        user_role = current_user.role
        filtered_resources = []
        for r in resources:
            visible_to = r.get("visible_to", ["all"])
            if "all" in visible_to or user_role in visible_to or current_user.is_owner:
                # Get creator name
                creator = await db.users.find_one({"id": r.get("created_by")}, {"_id": 0, "name": 1})
                r["created_by_name"] = creator.get("name") if creator else "Unknown"
                filtered_resources.append(r)
        
        return filtered_resources
        
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_resource_categories():
    """
    Get all resource categories with counts
    """
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        results = await db.resources.aggregate(pipeline).to_list(100)
        
        categories = {}
        for cat in ResourceCategory:
            categories[cat.value] = {
                "name": cat.value.replace("_", " ").title(),
                "count": 0
            }
        
        for r in results:
            if r["_id"] in categories:
                categories[r["_id"]]["count"] = r["count"]
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a single resource by ID
    """
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Check visibility
        visible_to = resource.get("visible_to", ["all"])
        if "all" not in visible_to and current_user.role not in visible_to and not current_user.is_owner:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")
        
        # Get creator name
        creator = await db.users.find_one({"id": resource.get("created_by")}, {"_id": 0, "name": 1})
        resource["created_by_name"] = creator.get("name") if creator else "Unknown"
        
        return resource
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=Resource)
async def create_resource(
    resource: ResourceCreate,
    current_user: User = Depends(require_owner)
):
    """
    Create a new resource (Owner only)
    """
    try:
        resource_dict = resource.model_dump()
        resource_dict["id"] = str(uuid4())
        resource_dict["created_by"] = current_user.id
        resource_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        resource_dict["download_count"] = 0
        resource_dict["category"] = resource.category.value
        resource_dict["type"] = resource.type.value
        
        await db.resources.insert_one(resource_dict)
        
        # Remove MongoDB _id before returning
        resource_dict.pop("_id", None)
        
        logger.info(f"Resource created: {resource_dict['title']} by {current_user.name}")
        return resource_dict
        
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{resource_id}/upload")
async def upload_resource_file(
    resource_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_owner)
):
    """
    Upload a file for a resource (Owner only)
    """
    try:
        # Check resource exists
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Validate file type
        allowed_types = {
            # Documents
            "application/pdf": "pdf",
            "application/msword": "document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
            # Spreadsheets
            "application/vnd.ms-excel": "spreadsheet",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "spreadsheet",
            # Presentations
            "application/vnd.ms-powerpoint": "presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "presentation",
            # Images
            "image/jpeg": "image",
            "image/png": "image",
            # Videos
            "video/mp4": "video",
            "video/webm": "video",
            # CAD Files (AutoCAD)
            "application/acad": "cad",
            "application/x-acad": "cad",
            "application/autocad_dwg": "cad",
            "application/dwg": "cad",
            "application/x-dwg": "cad",
            "image/vnd.dwg": "cad",
            "image/x-dwg": "cad",
            "application/octet-stream": "cad",  # DWG files often come as octet-stream
            # Other CAD formats
            "application/dxf": "cad",
            "application/x-dxf": "cad",
        }
        
        # Also allow by file extension for CAD files (since MIME types can be unreliable)
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        cad_extensions = ['dwg', 'dxf', 'dwt', 'dws']
        
        content_type = file.content_type
        if content_type not in allowed_types and file_ext not in cad_extensions:
            raise HTTPException(status_code=400, detail=f"File type {content_type} (.{file_ext}) not allowed")
        
        # Determine file type
        if file_ext in cad_extensions:
            file_type = "cad"
        else:
            file_type = allowed_types.get(content_type, "document")
        
        # Generate unique filename
        unique_filename = f"{resource_id}_{uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update resource with file info
        file_url = f"/api/resources/{resource_id}/download"
        await db.resources.update_one(
            {"id": resource_id},
            {"$set": {
                "url": file_url,
                "file_name": file.filename,
                "file_size": len(content),
                "mime_type": content_type,
                "type": file_type,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"File uploaded for resource {resource_id}: {file.filename}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "file_size": len(content),
            "url": file_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resource_id}/public-view")
async def public_view_resource(
    resource_id: str,
    token: str = Query(None, description="Optional view token for authentication")
):
    """
    Public endpoint for viewing resource files (for Office Online viewer)
    This endpoint allows unauthenticated access for document viewers
    """
    from fastapi.responses import FileResponse
    
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Find the file
        file_pattern = f"{resource_id}_"
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_pattern):
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                return FileResponse(
                    path=file_path,
                    filename=resource.get("file_name", filename),
                    media_type=resource.get("mime_type", "application/octet-stream"),
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving resource for view: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resource_id}/download")
async def download_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download a resource file
    """
    from fastapi.responses import FileResponse
    
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Check visibility
        visible_to = resource.get("visible_to", ["all"])
        if "all" not in visible_to and current_user.role not in visible_to and not current_user.is_owner:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")
        
        # Find the file
        file_pattern = f"{resource_id}_"
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_pattern):
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                # Increment download count
                await db.resources.update_one(
                    {"id": resource_id},
                    {"$inc": {"download_count": 1}}
                )
                
                return FileResponse(
                    path=file_path,
                    filename=resource.get("file_name", filename),
                    media_type=resource.get("mime_type", "application/octet-stream"),
                    headers={
                        "Content-Disposition": f'attachment; filename="{resource.get("file_name", filename)}"',
                        "Cache-Control": "no-cache"
                    }
                )
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resource_id}/view-url")
async def get_resource_view_url(
    resource_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a URL to view the resource in browser using Microsoft Office Online viewer
    """
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Check visibility
        visible_to = resource.get("visible_to", ["all"])
        if "all" not in visible_to and current_user.role not in visible_to and not current_user.is_owner:
            raise HTTPException(status_code=403, detail="You don't have access to this resource")
        
        if not resource.get("url"):
            raise HTTPException(status_code=400, detail="No file attached to this resource")
        
        # Get the base URL from environment or request
        base_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://pm-system.preview.emergentagent.com')
        
        # Build the public view URL (no auth required for Office Online viewer)
        public_file_url = f"{base_url}/api/resources/{resource_id}/public-view"
        
        # For Office documents, use Microsoft Office Online viewer
        file_name = resource.get("file_name", "").lower()
        
        if any(ext in file_name for ext in ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']):
            # Use Microsoft Office Online viewer
            import urllib.parse
            encoded_url = urllib.parse.quote(public_file_url, safe='')
            view_url = f"https://view.officeapps.live.com/op/view.aspx?src={encoded_url}"
            return {"view_url": view_url, "viewer": "microsoft"}
        elif file_name.endswith('.pdf'):
            # PDFs can be viewed directly in browser
            return {"view_url": public_file_url, "viewer": "browser"}
        else:
            # Use Google Docs viewer as fallback
            import urllib.parse
            encoded_url = urllib.parse.quote(public_file_url, safe='')
            view_url = f"https://docs.google.com/viewer?url={encoded_url}&embedded=true"
            return {"view_url": view_url, "viewer": "google"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting view URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{resource_id}", response_model=Resource)
async def update_resource(
    resource_id: str,
    update_data: ResourceUpdate,
    current_user: User = Depends(require_owner)
):
    """
    Update a resource (Owner only)
    """
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Build update dict (only non-None values)
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Convert enums to values
        if "category" in update_dict:
            update_dict["category"] = update_dict["category"].value
        if "type" in update_dict:
            update_dict["type"] = update_dict["type"].value
        
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.resources.update_one(
            {"id": resource_id},
            {"$set": update_dict}
        )
        
        # Return updated resource
        updated = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        logger.info(f"Resource updated: {resource_id} by {current_user.name}")
        return updated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    current_user: User = Depends(require_owner)
):
    """
    Delete a resource (Owner only)
    """
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Delete file if exists
        file_pattern = f"{resource_id}_"
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_pattern):
                file_path = os.path.join(UPLOAD_DIR, filename)
                os.remove(file_path)
                break
        
        # Delete from database
        await db.resources.delete_one({"id": resource_id})
        
        logger.info(f"Resource deleted: {resource_id} by {current_user.name}")
        
        return {"success": True, "message": "Resource deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults")
async def seed_default_resources(
    current_user: User = Depends(require_owner)
):
    """
    Seed default resources (Owner only) - for initial setup
    """
    try:
        # Check if resources already exist
        count = await db.resources.count_documents({})
        if count > 0:
            return {"success": False, "message": f"Resources already exist ({count} found). Delete them first to re-seed."}
        
        default_resources = [
            # Onboarding
            {"title": "Welcome to 4th Dimension", "description": "Introduction to our firm, culture, and values", "category": "onboarding", "type": "pdf", "featured": True, "order": 1},
            {"title": "Employee Handbook", "description": "Complete guide to company policies, benefits, and procedures", "category": "onboarding", "type": "pdf", "featured": True, "order": 2},
            {"title": "IT Setup Guide", "description": "How to set up your workstation, email, and software", "category": "onboarding", "type": "pdf", "order": 3},
            
            # Company Standards
            {"title": "Drawing Standards Manual", "description": "Standard conventions for architectural drawings", "category": "standards", "type": "pdf", "featured": True, "order": 1},
            {"title": "CAD Layer Standards", "description": "AutoCAD layer naming conventions and colors", "category": "standards", "type": "pdf", "order": 2},
            {"title": "Brand Guidelines", "description": "Logo usage, colors, fonts, and presentation standards", "category": "standards", "type": "pdf", "order": 3},
            {"title": "Title Block Standards", "description": "Standard title block format for all drawings", "category": "standards", "type": "pdf", "order": 4},
            
            # Templates
            {"title": "Project Proposal Template", "description": "Standard template for client proposals", "category": "templates", "type": "document", "order": 1},
            {"title": "Site Visit Report Template", "description": "Template for documenting site visits", "category": "templates", "type": "document", "order": 2},
            {"title": "Meeting Minutes Template", "description": "Standard format for meeting documentation", "category": "templates", "type": "document", "order": 3},
            {"title": "BOQ Template", "description": "Bill of Quantities template for project estimation", "category": "templates", "type": "spreadsheet", "order": 4},
            {"title": "Invoice Template", "description": "Standard invoice format for billing", "category": "templates", "type": "spreadsheet", "order": 5},
            
            # Tutorials
            {"title": "Portal User Guide", "description": "How to use the 4th Dimension project portal", "category": "tutorials", "type": "pdf", "featured": True, "order": 1},
            {"title": "Drawing Upload Tutorial", "description": "Step-by-step guide to uploading and managing drawings", "category": "tutorials", "type": "video", "order": 2},
            {"title": "Client Communication Best Practices", "description": "Tips for effective client communication", "category": "tutorials", "type": "pdf", "order": 3},
            
            # Policies
            {"title": "Leave Policy", "description": "Guidelines for leave applications and approvals", "category": "policies", "type": "pdf", "order": 1},
            {"title": "Work From Home Policy", "description": "Remote work guidelines and expectations", "category": "policies", "type": "pdf", "order": 2},
            {"title": "Expense Reimbursement Policy", "description": "How to submit and get reimbursed for expenses", "category": "policies", "type": "pdf", "order": 3},
            {"title": "Site Safety Guidelines", "description": "Safety protocols for site visits", "category": "policies", "type": "pdf", "order": 4},
            
            # Tools & Software
            {"title": "AutoCAD Quick Reference", "description": "Keyboard shortcuts and common commands", "category": "tools", "type": "pdf", "order": 1},
            {"title": "SketchUp Tips & Tricks", "description": "Advanced techniques for 3D modeling", "category": "tools", "type": "video", "order": 2},
            {"title": "Software Download Links", "description": "Licensed software and installation guides", "category": "tools", "type": "link", "external_link": "#", "order": 3},
        ]
        
        now = datetime.now(timezone.utc).isoformat()
        for resource in default_resources:
            resource["id"] = str(uuid4())
            resource["created_by"] = current_user.id
            resource["created_at"] = now
            resource["download_count"] = 0
            resource["visible_to"] = ["all"]
            resource["tags"] = []
            if "featured" not in resource:
                resource["featured"] = False
        
        await db.resources.insert_many(default_resources)
        
        logger.info(f"Seeded {len(default_resources)} default resources")
        
        return {
            "success": True,
            "message": f"Successfully created {len(default_resources)} default resources",
            "count": len(default_resources)
        }
        
    except Exception as e:
        logger.error(f"Error seeding resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
