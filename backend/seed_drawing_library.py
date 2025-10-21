"""
ArchFlow - Seed Data for Drawing Library and Presets
Run this to initialize default drawing categories, types, and checklist presets
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from datetime import datetime, timezone
import uuid

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'architecture_firm')

async def seed_drawing_library():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Seeding Drawing Library...")
    
    # 1. Create Drawing Categories
    categories = [
        {"id": str(uuid.uuid4()), "name": "Structural", "description": "Structural drawings and details"},
        {"id": str(uuid.uuid4()), "name": "Architectural", "description": "Architectural plans and elevations"},
        {"id": str(uuid.uuid4()), "name": "Plumbing", "description": "Plumbing layouts and details"},
        {"id": str(uuid.uuid4()), "name": "Electrical", "description": "Electrical layouts and schedules"},
        {"id": str(uuid.uuid4()), "name": "HVAC", "description": "HVAC layouts and details"},
        {"id": str(uuid.uuid4()), "name": "Furniture", "description": "Furniture layouts and details"},
        {"id": str(uuid.uuid4()), "name": "Ceiling", "description": "Ceiling and RCP layouts"},
        {"id": str(uuid.uuid4()), "name": "Kitchen", "description": "Kitchen working drawings"},
        {"id": str(uuid.uuid4()), "name": "Landscape", "description": "Landscape plans"},
        {"id": str(uuid.uuid4()), "name": "Other", "description": "Other miscellaneous drawings"},
    ]
    
    await db.drawing_categories.delete_many({})
    await db.drawing_categories.insert_many(categories)
    print(f"✅ Created {len(categories)} drawing categories")
    
    # Create category lookup
    cat_lookup = {cat["name"]: cat["id"] for cat in categories}
    
    # 2. Architecture Drawing Types
    architecture_types = [
        {"name": "Column Layout", "category": "Structural", "seq": 10, "offset": 7},
        {"name": "Footing Detail", "category": "Structural", "seq": 20, "offset": 7},
        {"name": "GA Plan / Final Layout", "category": "Architectural", "seq": 30, "offset": 7},
        {"name": "Sections", "category": "Architectural", "seq": 40, "offset": 7},
        {"name": "Elevations", "category": "Architectural", "seq": 50, "offset": 7},
        {"name": "3D Views", "category": "Architectural", "seq": 60, "offset": 7},
        {"name": "Slab Reinforcement", "category": "Structural", "seq": 70, "offset": 7},
        {"name": "Beam Layout", "category": "Structural", "seq": 80, "offset": 7},
        {"name": "Stair Detail", "category": "Architectural", "seq": 90, "offset": 7},
        {"name": "Door-Window Schedule", "category": "Architectural", "seq": 100, "offset": 7},
    ]
    
    # 3. Interior Drawing Types
    interior_types = [
        {"name": "Site Measurement Record", "category": "Architectural", "seq": 10, "offset": 7},
        {"name": "Furniture Layout", "category": "Architectural", "seq": 20, "offset": 7},
        {"name": "RCP / Ceiling Layout", "category": "Ceiling", "seq": 30, "offset": 7},
        {"name": "Electrical Layout", "category": "Electrical", "seq": 40, "offset": 7},
        {"name": "Plumbing Layout", "category": "Plumbing", "seq": 50, "offset": 7},
        {"name": "Kitchen Working Set", "category": "Kitchen", "seq": 60, "offset": 7},
        {"name": "Wardrobe Details", "category": "Furniture", "seq": 70, "offset": 7},
        {"name": "Toilet Details", "category": "Plumbing", "seq": 80, "offset": 7},
        {"name": "3D Views", "category": "Architectural", "seq": 90, "offset": 7},
        {"name": "Final Working Set", "category": "Architectural", "seq": 100, "offset": 7},
    ]
    
    # Insert drawing types
    drawing_types = []
    arch_type_ids = []
    int_type_ids = []
    
    for dt in architecture_types:
        dt_id = str(uuid.uuid4())
        drawing_types.append({
            "id": dt_id,
            "category_id": cat_lookup[dt["category"]],
            "name": dt["name"],
            "default_sequence": dt["seq"],
            "default_due_offset_days": dt["offset"],
            "auto_template_file": None,
            "auto_send": False,
            "project_type": "Architecture"
        })
        arch_type_ids.append({"id": dt_id, "seq": dt["seq"]})
    
    for dt in interior_types:
        dt_id = str(uuid.uuid4())
        drawing_types.append({
            "id": dt_id,
            "category_id": cat_lookup[dt["category"]],
            "name": dt["name"],
            "default_sequence": dt["seq"],
            "default_due_offset_days": dt["offset"],
            "auto_template_file": None,
            "auto_send": False,
            "project_type": "Interior"
        })
        int_type_ids.append({"id": dt_id, "seq": dt["seq"]})
    
    await db.drawing_types.delete_many({})
    await db.drawing_types.insert_many(drawing_types)
    print(f"✅ Created {len(drawing_types)} drawing types")
    
    # 4. Create Checklist Presets
    presets = [
        {
            "id": str(uuid.uuid4()),
            "name": "Architecture – Standard",
            "project_type": "Architecture",
            "description": "Standard checklist for architectural projects",
            "type_ids": arch_type_ids
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Interior – Standard",
            "project_type": "Interior",
            "description": "Standard checklist for interior design projects",
            "type_ids": int_type_ids
        }
    ]
    
    await db.checklist_presets.delete_many({})
    await db.checklist_presets.insert_many(presets)
    print(f"✅ Created {len(presets)} checklist presets")
    
    # 5. Create Checklist Items (link presets to drawing types)
    checklist_items = []
    for preset in presets:
        for type_info in preset["type_ids"]:
            checklist_items.append({
                "id": str(uuid.uuid4()),
                "checklist_preset_id": preset["id"],
                "drawing_type_id": type_info["id"],
                "sequence": type_info["seq"]
            })
    
    await db.checklist_items.delete_many({})
    await db.checklist_items.insert_many(checklist_items)
    print(f"✅ Created {len(checklist_items)} checklist items")
    
    print("✨ Drawing library seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_drawing_library())
