from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models_projects import (
    Client as NewClient, ClientCreate as NewClientCreate, ClientUpdate,
    BrandCategoryMaster, BrandCategoryMasterCreate, BrandCategoryMasterUpdate,
    ContactTypeMaster, ContactTypeMasterCreate, ContactTypeMasterUpdate
)

router = APIRouter(tags=["clients"])

# Dependencies
def get_current_user(): pass
def require_owner(): pass
def get_db(): pass

# ==================== CLIENT ROUTES ====================

@router.post("/clients", response_model=NewClient)
async def create_client(
    client_data: NewClientCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    client = NewClient(
        name=client_data.name,
        contact_person=client_data.contact_person,
        phone=client_data.phone,
        email=client_data.email,
        address=client_data.address,
        notes=client_data.notes,
        archived=False,
        created_by_id=current_user.id,
        owner_team_id=None
    )
    
    client_dict = client.model_dump()
    client_dict['created_at'] = client_dict['created_at'].isoformat()
    client_dict['updated_at'] = client_dict['updated_at'].isoformat()
    
    await db.clients.insert_one(client_dict)
    return client

@router.get("/clients")
async def get_clients(
    include_archived: bool = False,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    query = {"deleted_at": None}
    if not include_archived:
        query["archived"] = {"$ne": True}
    
    clients = await db.clients.find(query, {"_id": 0}).to_list(1000)
    
    for client in clients:
        if isinstance(client.get('created_at'), str):
            client['created_at'] = datetime.fromisoformat(client['created_at'])
        if isinstance(client.get('updated_at'), str):
            client['updated_at'] = datetime.fromisoformat(client['updated_at'])
        
        project_count = await db.projects.count_documents({"client_id": client["id"], "deleted_at": None})
        client['total_projects'] = project_count
    
    return clients

@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    client = await db.clients.find_one({"id": client_id, "deleted_at": None}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if isinstance(client.get('created_at'), str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    if isinstance(client.get('updated_at'), str):
        client['updated_at'] = datetime.fromisoformat(client['updated_at'])
    
    projects = await db.projects.find({"client_id": client_id, "deleted_at": None}, {"_id": 0}).to_list(100)
    client['projects'] = projects
    
    return client

@router.put("/clients/{client_id}")
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "name": client_data.name,
            "contact_person": client_data.contact_person,
            "phone": client_data.phone,
            "email": client_data.email,
            "address": client_data.address,
            "notes": client_data.notes,
            "archived": client_data.archived,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Client updated successfully"}

@router.put("/clients/{client_id}/archive")
async def archive_client(
    client_id: str,
    archived: bool = True,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "archived": archived,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    action = "archived" if archived else "unarchived"
    return {"message": f"Client {action} successfully"}

@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await db.projects.update_many(
        {"client_id": client_id},
        {"$set": {"client_id": None}}
    )
    
    return {"message": "Client deleted and projects unlinked"}

# ==================== BRAND CATEGORY ROUTES ====================

@router.get("/brand-categories")
async def get_brand_categories(current_user = Depends(get_current_user), db = Depends(get_db)):
    categories = await db.brand_categories.find({}, {"_id": 0}).to_list(1000)
    return categories

@router.post("/brand-categories", response_model=BrandCategoryMaster)
async def create_brand_category(
    category_data: BrandCategoryMasterCreate, 
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    category = BrandCategoryMaster(
        category_name=category_data.category_name,
        suggested_brands=category_data.suggested_brands
    )
    
    category_dict = category.model_dump()
    category_dict['created_at'] = category_dict['created_at'].isoformat()
    category_dict['updated_at'] = category_dict['updated_at'].isoformat()
    
    await db.brand_categories.insert_one(category_dict)
    return category

@router.put("/brand-categories/{category_id}")
async def update_brand_category(
    category_id: str,
    category_data: BrandCategoryMasterUpdate,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    update_data = {k: v for k, v in category_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.brand_categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    return {"message": "Brand category updated successfully"}

@router.delete("/brand-categories/{category_id}")
async def delete_brand_category(
    category_id: str,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    await db.brand_categories.delete_one({"id": category_id})
    return {"message": "Brand category deleted successfully"}

# ==================== CONTACT TYPE ROUTES ====================

@router.get("/contact-types")
async def get_contact_types(current_user = Depends(get_current_user), db = Depends(get_db)):
    types = await db.contact_types.find({}, {"_id": 0}).to_list(1000)
    return types

@router.post("/contact-types", response_model=ContactTypeMaster)
async def create_contact_type(
    type_data: ContactTypeMasterCreate, 
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    contact_type = ContactTypeMaster(
        type_name=type_data.type_name
    )
    
    type_dict = contact_type.model_dump()
    type_dict['created_at'] = type_dict['created_at'].isoformat()
    type_dict['updated_at'] = type_dict['updated_at'].isoformat()
    
    await db.contact_types.insert_one(type_dict)
    return contact_type

@router.put("/contact-types/{type_id}")
async def update_contact_type(
    type_id: str,
    type_data: ContactTypeMasterUpdate,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    update_data = {k: v for k, v in type_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.contact_types.update_one(
        {"id": type_id},
        {"$set": update_data}
    )
    return {"message": "Contact type updated successfully"}

@router.delete("/contact-types/{type_id}")
async def delete_contact_type(
    type_id: str,
    current_user = Depends(require_owner),
    db = Depends(get_db)
):
    await db.contact_types.delete_one({"id": type_id})
    return {"message": "Contact type deleted successfully"}
