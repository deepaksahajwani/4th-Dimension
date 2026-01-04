"""
External Parties Router - Contractors, Vendors, Consultants
Refactored from server.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import logging

from models_projects import (
    Contractor, ContractorCreate, ContractorType,
    Vendor, VendorCreate, VendorUpdate, VendorType,
    Consultant, ConsultantCreate, ConsultantType
)
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(tags=["External Parties"])

# Database and auth dependencies will be injected
db = None
get_current_user = None
require_owner = None
User = None


def init_router(database, current_user_dep, owner_dep, user_model):
    """Initialize router with dependencies from main app"""
    global db, get_current_user, require_owner, User
    db = database
    get_current_user = current_user_dep
    require_owner = owner_dep
    User = user_model


# ==================== CONTRACTOR ROUTES ====================

@router.post("/contractors")
async def create_contractor(
    contractor_data: ContractorCreate,
    current_user = Depends(lambda: get_current_user)
):
    """Create a new contractor (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    contractor = Contractor(**contractor_data.model_dump())
    contractor_dict = contractor.model_dump()
    
    # Convert datetimes to ISO strings
    for field in ['created_at', 'updated_at']:
        if contractor_dict.get(field):
            contractor_dict[field] = contractor_dict[field].isoformat()
    
    await db.contractors.insert_one(contractor_dict)
    return contractor


@router.get("/contractors")
async def get_contractors(current_user = Depends(lambda: get_current_user)):
    """
    Get contractors based on user role:
    - Owner/Team Members: See all approved contractors
    - Clients: See ONLY contractors assigned to their projects
    - Contractors: See only themselves
    """
    
    # If client, filter to only contractors on their projects
    if current_user.role == "client":
        client = await db.clients.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if client:
            client_projects = await db.projects.find(
                {"client_id": client["id"], "deleted_at": None},
                {"_id": 0, "assigned_contractors": 1}
            ).to_list(100)
        else:
            client_projects = await db.projects.find(
                {"client_id": current_user.id, "deleted_at": None},
                {"_id": 0, "assigned_contractors": 1}
            ).to_list(100)
        
        contractor_ids = set()
        for project in client_projects:
            assigned = project.get('assigned_contractors', {})
            if isinstance(assigned, dict):
                contractor_ids.update(assigned.values())
        
        if not contractor_ids:
            return []
        
        contractors = await db.contractors.find(
            {"id": {"$in": list(contractor_ids)}, "deleted_at": None},
            {"_id": 0}
        ).to_list(100)
        
        return contractors
    
    # If contractor, only return self
    if current_user.role == "contractor":
        contractor = await db.contractors.find_one(
            {"email": current_user.email, "deleted_at": None},
            {"_id": 0}
        )
        return [contractor] if contractor else []
    
    # Owner and team members see all
    contractors = await db.contractors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    
    # Filter out contractors whose user accounts are not approved
    approved_contractors = []
    for contractor in contractors:
        if contractor.get('user_id'):
            user = await db.users.find_one(
                {"id": contractor['user_id']}, 
                {"_id": 0, "approval_status": 1}
            )
            if user and user.get('approval_status') == 'approved':
                approved_contractors.append(contractor)
        else:
            approved_contractors.append(contractor)
    
    return approved_contractors


@router.get("/contractors/{contractor_id}")
async def get_contractor(
    contractor_id: str,
    current_user = Depends(lambda: get_current_user)
):
    """Get a specific contractor"""
    contractor = await db.contractors.find_one(
        {"id": contractor_id, "deleted_at": None},
        {"_id": 0}
    )
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor


@router.put("/contractors/{contractor_id}")
async def update_contractor(
    contractor_id: str,
    contractor_data: ContractorCreate,
    current_user = Depends(lambda: get_current_user)
):
    """Update a contractor (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    update_dict = contractor_data.model_dump()
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.contractors.update_one(
        {"id": contractor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return await get_contractor(contractor_id, current_user)


@router.delete("/contractors/{contractor_id}")
async def delete_contractor(
    contractor_id: str,
    current_user = Depends(lambda: get_current_user)
):
    """HARD DELETE a contractor (Owner only) - Only if no active projects exist"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # Check for active projects
    active_projects = await db.projects.find({
        "contractors": contractor_id,
        "$or": [
            {"archived": False},
            {"archived": {"$exists": False}}
        ]
    }, {"_id": 0, "name": 1}).to_list(10)
    
    if active_projects:
        project_names = ", ".join([p.get('name', 'Unnamed') for p in active_projects])
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete contractor. Active projects exist: {project_names}."
        )
    
    contractor_email = contractor.get('email')
    contractor_phone = contractor.get('phone')
    contractor_user_id = contractor.get('user_id')
    
    # HARD DELETE from contractors collection
    await db.contractors.delete_one({"id": contractor_id})
    logger.info(f"Hard deleted contractor: {contractor.get('name')}")
    
    # Delete associated user account
    if contractor_user_id:
        await db.users.delete_one({"id": contractor_user_id})
        logger.info(f"Hard deleted user account for contractor: {contractor.get('name')}")
    
    # Clean up related records
    if contractor_email:
        await db.pending_registrations.delete_many({"email": contractor_email})
        await db.invitations.delete_many({"email": contractor_email})
        await db.team_verifications.delete_many({"email": contractor_email})
    
    if contractor_phone:
        phone_digits = ''.join(filter(str.isdigit, contractor_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Contractor permanently deleted."}


@router.get("/contractor-types")
async def get_contractor_types():
    """Get list of predefined contractor types"""
    return [{"value": t.value, "label": t.value} for t in ContractorType]


# ==================== VENDOR ROUTES ====================

@router.post("/vendors")
async def create_vendor(
    vendor_data: VendorCreate,
    current_user = Depends(lambda: get_current_user)
):
    """Create a new vendor (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    vendor = Vendor(**vendor_data.model_dump())
    vendor_dict = vendor.model_dump()
    
    for field in ['created_at', 'updated_at']:
        if vendor_dict.get(field):
            vendor_dict[field] = vendor_dict[field].isoformat()
    
    await db.vendors.insert_one(vendor_dict)
    return vendor


@router.get("/vendors")
async def get_vendors(current_user = Depends(lambda: get_current_user)):
    """Get all vendors"""
    vendors = await db.vendors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    return vendors


@router.get("/vendors/{vendor_id}")
async def get_vendor(
    vendor_id: str,
    current_user = Depends(lambda: get_current_user)
):
    """Get a specific vendor"""
    vendor = await db.vendors.find_one(
        {"id": vendor_id, "deleted_at": None},
        {"_id": 0}
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.put("/vendors/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    vendor_data: VendorUpdate,
    current_user = Depends(lambda: get_current_user)
):
    """Update a vendor (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    update_dict = {k: v for k, v in vendor_data.model_dump().items() if v is not None}
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.vendors.update_one(
        {"id": vendor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return await get_vendor(vendor_id, current_user)


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    current_user = Depends(lambda: get_current_user)
):
    """Soft delete a vendor (Owner only)"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    
    result = await db.vendors.update_one(
        {"id": vendor_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return {"message": "Vendor deleted successfully"}


@router.get("/vendor-types")
async def get_vendor_types():
    """Get list of predefined vendor types"""
    return [{"value": t.value, "label": t.value} for t in VendorType]


# ==================== CONSULTANT ROUTES ====================

@router.get("/consultant-types")
async def get_consultant_types():
    """Get list of predefined consultant types"""
    return [{"value": t.value, "label": t.value} for t in ConsultantType]


@router.post("/consultants", response_model=Consultant)
async def create_consultant(
    consultant_data: ConsultantCreate,
    current_user = Depends(lambda: get_current_user)
):
    """Create a new consultant"""
    consultant = Consultant(**consultant_data.model_dump())
    consultant_dict = consultant.model_dump()
    consultant_dict['created_at'] = consultant_dict['created_at'].isoformat()
    consultant_dict['updated_at'] = consultant_dict['updated_at'].isoformat()
    await db.consultants.insert_one(consultant_dict)
    return consultant


@router.get("/consultants", response_model=List[Consultant])
async def get_consultants(current_user = Depends(lambda: get_current_user)):
    """Get all consultants (filtered by approval status)"""
    consultants = await db.consultants.find({"deleted_at": None}, {"_id": 0}).to_list(1000)
    
    approved_consultants = []
    for c in consultants:
        if c.get('user_id'):
            user = await db.users.find_one(
                {"id": c['user_id']}, 
                {"_id": 0, "approval_status": 1}
            )
            if not (user and user.get('approval_status') == 'approved'):
                continue
        
        # Process dates
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
        if isinstance(c.get('updated_at'), str):
            c['updated_at'] = datetime.fromisoformat(c['updated_at'])
        
        # Auto-fix legacy "Structural" type to "Structure"
        if c.get('type') == 'Structural':
            c['type'] = 'Structure'
            await db.consultants.update_one(
                {"id": c['id']},
                {"$set": {"type": "Structure"}}
            )
        
        approved_consultants.append(c)
    
    return approved_consultants


@router.put("/consultants/{consultant_id}", response_model=Consultant)
async def update_consultant(
    consultant_id: str,
    consultant_data: ConsultantCreate,
    current_user = Depends(lambda: get_current_user)
):
    """Update consultant"""
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    update_dict = consultant_data.model_dump()
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.consultants.update_one(
        {"id": consultant_id},
        {"$set": update_dict}
    )
    
    updated = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated


@router.delete("/consultants/{consultant_id}")
async def delete_consultant(
    consultant_id: str,
    current_user = Depends(lambda: get_current_user)
):
    """HARD DELETE consultant - Only if no active projects exist"""
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    # Check for active projects
    active_projects = await db.projects.find({
        "consultants": consultant_id,
        "$or": [
            {"archived": False},
            {"archived": {"$exists": False}}
        ]
    }, {"_id": 0, "name": 1}).to_list(10)
    
    if active_projects:
        project_names = ", ".join([p.get('name', 'Unnamed') for p in active_projects])
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete consultant. Active projects exist: {project_names}."
        )
    
    consultant_email = existing.get('email')
    consultant_phone = existing.get('phone')
    consultant_user_id = existing.get('user_id')
    
    # HARD DELETE
    await db.consultants.delete_one({"id": consultant_id})
    logger.info(f"Hard deleted consultant: {existing.get('name')}")
    
    if consultant_user_id:
        await db.users.delete_one({"id": consultant_user_id})
        logger.info(f"Hard deleted user account for consultant")
    
    # Cleanup
    if consultant_email:
        await db.pending_registrations.delete_many({"email": consultant_email})
        await db.invitations.delete_many({"email": consultant_email})
        await db.team_verifications.delete_many({"email": consultant_email})
    
    if consultant_phone:
        phone_digits = ''.join(filter(str.isdigit, consultant_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Consultant permanently deleted."}
