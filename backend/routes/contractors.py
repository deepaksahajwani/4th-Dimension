from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models_projects import Contractor, ContractorCreate, ContractorType, Vendor, VendorCreate, VendorUpdate, VendorType

router = APIRouter(tags=["contractors"])

# Dependencies
def get_current_user(): pass
def require_owner(): pass
def get_db(): pass

# CONTRACTORS
@router.post("/contractors")
async def create_contractor(
    contractor_data: ContractorCreate,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    contractor = Contractor(**contractor_data.model_dump())
    contractor_dict = contractor.model_dump()
    
    for field in ['created_at', 'updated_at']:
        if contractor_dict.get(field):
            contractor_dict[field] = contractor_dict[field].isoformat()
    
    await db.contractors.insert_one(contractor_dict)
    return contractor

@router.get("/contractors")
async def get_contractors(current_user = Depends(get_current_user), db = Depends(get_db)):
    contractors = await db.contractors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    return contractors

@router.get("/contractors/{contractor_id}")
async def get_contractor(
    contractor_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
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
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    update_dict = contractor_data.model_dump()
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.contractors.update_one(
        {"id": contractor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return await get_contractor(contractor_id, current_user, db)

@router.delete("/contractors/{contractor_id}")
async def delete_contractor(
    contractor_id: str,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    result = await db.contractors.update_one(
        {"id": contractor_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return {"message": "Contractor deleted successfully"}

@router.get("/contractor-types")
async def get_contractor_types():
    return [{"value": t.value, "label": t.value} for t in ContractorType]

# VENDORS
@router.post("/vendors")
async def create_vendor(
    vendor_data: VendorCreate,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    vendor = Vendor(**vendor_data.model_dump())
    vendor_dict = vendor.model_dump()
    
    for field in ['created_at', 'updated_at']:
        if vendor_dict.get(field):
            vendor_dict[field] = vendor_dict[field].isoformat()
    
    await db.vendors.insert_one(vendor_dict)
    return vendor

@router.get("/vendors")
async def get_vendors(current_user = Depends(get_current_user), db = Depends(get_db)):
    vendors = await db.vendors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    return vendors

@router.get("/vendors/{vendor_id}")
async def get_vendor(
    vendor_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
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
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    update_dict = {k: v for k, v in vendor_data.model_dump().items() if v is not None}
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.vendors.update_one(
        {"id": vendor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return await get_vendor(vendor_id, current_user, db)

@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    result = await db.vendors.update_one(
        {"id": vendor_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return {"message": "Vendor deleted successfully"}

@router.get("/vendor-types")
async def get_vendor_types():
    return [{"value": t.value, "label": t.value} for t in VendorType]
