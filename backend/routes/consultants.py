from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models_projects import Consultant, ConsultantCreate, ChecklistPreset, DrawingType

router = APIRouter(prefix="/consultants", tags=["consultants"])

# Dependencies will be injected
def get_current_user(): pass
def get_db(): pass

@router.post("", response_model=Consultant)
async def create_consultant(consultant_data: ConsultantCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    consultant = Consultant(**consultant_data.model_dump())
    consultant_dict = consultant.model_dump()
    consultant_dict['created_at'] = consultant_dict['created_at'].isoformat()
    consultant_dict['updated_at'] = consultant_dict['updated_at'].isoformat()
    await db.consultants.insert_one(consultant_dict)
    return consultant

@router.get("", response_model=List[Consultant])
async def get_consultants(current_user = Depends(get_current_user), db = Depends(get_db)):
    consultants = await db.consultants.find({"deleted_at": None}, {"_id": 0}).to_list(1000)
    for c in consultants:
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
    return consultants

@router.put("/{consultant_id}", response_model=Consultant)
async def update_consultant(
    consultant_id: str,
    consultant_data: ConsultantCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
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

@router.delete("/{consultant_id}")
async def delete_consultant(
    consultant_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    await db.consultants.update_one(
        {"id": consultant_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Consultant deleted successfully"}
