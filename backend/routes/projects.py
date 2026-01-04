"""
Project Management Routes
Handles project CRUD operations, drawings association, and co-clients
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
import logging
from uuid import uuid4

from utils.auth import get_current_user, require_owner, User
from utils.database import get_database
from models_projects import (
    Project as NewProject, ProjectCreate as NewProjectCreate, ProjectUpdate as NewProjectUpdate,
    ProjectDrawing, DrawingStatus
)
from models_coclients import CoClient, CoClientCreate
from drawing_templates import get_template_drawings

db = get_database()
router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=NewProject)
async def create_project(project_data: NewProjectCreate, current_user: User = Depends(get_current_user)):
    """Create a new project with comprehensive details"""
    # Auto-archive if end_date is provided
    archived = False
    if project_data.end_date:
        archived = True
    
    project = NewProject(
        code=project_data.code,
        title=project_data.title,
        project_types=project_data.project_types,
        status=project_data.status,
        client_id=project_data.client_id,
        team_leader_id=project_data.team_leader_id,
        lead_architect_id=project_data.lead_architect_id,
        project_manager_id=project_data.project_manager_id,
        start_date=datetime.fromisoformat(project_data.start_date) if project_data.start_date else None,
        end_date=datetime.fromisoformat(project_data.end_date) if project_data.end_date else None,
        archived=archived,
        site_address=project_data.site_address,
        notes=project_data.notes,
        civil_contractor=project_data.civil_contractor,
        structural_consultant=project_data.structural_consultant,
        tile_marble_contractor=project_data.tile_marble_contractor,
        furniture_contractor=project_data.furniture_contractor,
        electrical_contractor=project_data.electrical_contractor,
        electrical_consultant=project_data.electrical_consultant,
        plumbing_consultant=project_data.plumbing_consultant,
        plumbing_contractor=project_data.plumbing_contractor,
        false_ceiling_contractor=project_data.false_ceiling_contractor,
        furniture_material_supplier=project_data.furniture_material_supplier,
        kitchen_contractor=project_data.kitchen_contractor,
        modular_contractor=project_data.modular_contractor,
        color_contractor=project_data.color_contractor,
        landscape_consultant=project_data.landscape_consultant,
        landscape_contractor=project_data.landscape_contractor,
        automation_consultant=project_data.automation_consultant,
        readymade_furniture_supplier=project_data.readymade_furniture_supplier,
        lights_supplier=project_data.lights_supplier,
        custom_contacts=project_data.custom_contacts,
        brands=project_data.brands,
        assigned_contractors=project_data.assigned_contractors,
        created_by_id=current_user.id
    )
    
    project_dict = project.model_dump()
    # Convert datetimes to ISO strings
    for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
        if project_dict.get(field):
            project_dict[field] = project_dict[field].isoformat() if isinstance(project_dict[field], datetime) else project_dict[field]
    
    await db.projects.insert_one(project_dict)
    
    # Auto-create ONLY first 3 drawings from template lists for each project type
    base_date = project.start_date if project.start_date else datetime.now(timezone.utc)
    
    for project_type in project.project_types:
        template_drawings = get_template_drawings(project_type)
        
        if not template_drawings:
            logger.warning(f"No template drawings found for project type: {project_type}")
            continue
        
        # Create ONLY first 3 drawings from template
        for i in range(min(3, len(template_drawings))):
            drawing_name = template_drawings[i]
            sequence_num = i + 1
            
            # Drawing #1: project creation + 3 days (DUE)
            # Drawing #2 & #3: No due date yet (UPCOMING)
            if sequence_num == 1:
                due_date = base_date + timedelta(days=3)
            else:
                due_date = None
            
            drawing = ProjectDrawing(
                project_id=project.id,
                category=project_type,
                name=drawing_name,
                status=DrawingStatus.PLANNED,
                due_date=due_date,
                is_issued=False,
                revision_count=0,
                sequence_number=sequence_num,
                is_active=True if sequence_num == 1 else False,
                assigned_to=project.team_leader_id or project.lead_architect_id,
                priority="high" if sequence_num == 1 else "medium"
            )
            drawing_dict = drawing.model_dump()
            
            # Convert datetimes to ISO strings
            for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                if drawing_dict.get(field):
                    drawing_dict[field] = drawing_dict[field].isoformat() if isinstance(drawing_dict[field], datetime) else drawing_dict[field]
            
            await db.project_drawings.insert_one(drawing_dict)
            logger.info(f"Created drawing #{sequence_num}: {drawing_name} for project {project.id}")
    
    # Send project creation notifications
    try:
        from notification_triggers_v2 import notify_project_creation
        await notify_project_creation(project.id)
    except Exception as e:
        logger.error(f"Error sending project creation notification: {str(e)}")
    
    return project


@router.get("/")
async def get_projects(current_user: User = Depends(get_current_user)):
    """Get all projects"""
    projects = await db.projects.find({"deleted_at": None}, {"_id": 0}).to_list(1000)
    return projects


@router.get("/{project_id}")
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get project by ID"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: NewProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update project"""
    update_data = project_data.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Convert datetime fields
    for field in ['start_date', 'end_date']:
        if field in update_data and update_data[field]:
            if isinstance(update_data[field], str):
                update_data[field] = datetime.fromisoformat(update_data[field]).isoformat()
    
    result = await db.projects.update_one(
        {"id": project_id, "deleted_at": None},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project updated successfully"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_owner)
):
    """Soft delete project - OTP verification temporarily suspended (owner only)"""
    # Soft delete project
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/co-clients")
async def add_co_client(
    project_id: str,
    co_client_data: CoClientCreate,
    current_user: User = Depends(get_current_user)
):
    """Add co-client to project"""
    # Check if project exists
    project = await db.projects.find_one({"id": project_id, "deleted_at": None})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    co_client = CoClient(
        id=str(uuid4()),
        project_id=project_id,
        name=co_client_data.name,
        email=co_client_data.email,
        phone=co_client_data.phone,
        role=co_client_data.role,
        permissions=co_client_data.permissions,
        created_at=datetime.now(timezone.utc),
        created_by_id=current_user.id
    )
    
    co_client_dict = co_client.model_dump()
    co_client_dict['created_at'] = co_client_dict['created_at'].isoformat()
    
    await db.co_clients.insert_one(co_client_dict)
    
    return co_client


@router.get("/{project_id}/co-clients")
async def get_co_clients(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all co-clients for a project"""
    co_clients = await db.co_clients.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return co_clients


@router.delete("/{project_id}/co-clients/{co_client_id}")
async def remove_co_client(
    project_id: str,
    co_client_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove co-client from project"""
    result = await db.co_clients.delete_one({"id": co_client_id, "project_id": project_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Co-client not found")
    
    return {"message": "Co-client removed successfully"}
