"""
ArchFlow - Seed Demo Data
Creates demo projects, consultants, and team members
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from datetime import datetime, timezone, timedelta
import uuid

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'architecture_firm')

async def seed_demo_data():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Seeding Demo Data...")
    
    # 1. Create demo client
    demo_client = {
        "id": str(uuid.uuid4()),
        "name": "Demo Client Pvt Ltd",
        "contact_person": "Mr. Demo",
        "phone": "+919876543210",
        "email": "demo@client.com",
        "address": "123 Demo Street, Mumbai",
        "notes": "Demo client for testing",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.clients.insert_one(demo_client)
    print(f"✅ Created demo client: {demo_client['name']}")
    
    # 2. Create structural consultant
    consultant = {
        "id": str(uuid.uuid4()),
        "name": "ABC Structural Consultants",
        "type": "Structural",
        "phone": "+919123456789",
        "email": "structural@abc.com",
        "notes": "Specialized in RCC structures",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.consultants.insert_one(consultant)
    print(f"✅ Created consultant: {consultant['name']}")
    
    # 3. Get checklist presets
    arch_preset = await db.checklist_presets.find_one({"name": "Architecture – Standard"})
    int_preset = await db.checklist_presets.find_one({"name": "Interior – Standard"})
    
    if not arch_preset or not int_preset:
        print("❌ Presets not found. Run seed_drawing_library.py first")
        client.close()
        return
    
    # 4. Create demo Architecture project
    arch_project = {
        "id": str(uuid.uuid4()),
        "code": "AR-001",
        "title": "Residential Bungalow - Demo",
        "type": "Architecture",
        "status": "Layout_Dev",
        "client_id": demo_client["id"],
        "lead_architect_id": None,  # Will be assigned manually
        "project_manager_id": None,
        "start_date": datetime.now(timezone.utc).isoformat(),
        "expected_finish": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
        "site_address": "Plot 45, Sector 12, Navi Mumbai",
        "plot_dimensions": "30' x 60'",
        "notes": "3BHK + Terrace with modern elevation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.projects.insert_one(arch_project)
    print(f"✅ Created project: {arch_project['code']} - {arch_project['title']}")
    
    # 5. Generate first 5 drawings for AR-001, make one overdue
    checklist_items = await db.checklist_items.find(
        {"checklist_preset_id": arch_preset["id"]}
    ).sort("sequence", 1).limit(5).to_list(5)
    
    today = datetime.now(timezone.utc)
    drawings_created = []
    
    for idx, item in enumerate(checklist_items):
        drawing_type = await db.drawing_types.find_one({"id": item["drawing_type_id"]})
        
        if drawing_type:
            # Make first drawing overdue
            if idx == 0:
                due_date = today - timedelta(days=3)  # Overdue
                status = "InProgress"
            else:
                stagger = item["sequence"] // 10
                due_date = today + timedelta(days=drawing_type["default_due_offset_days"] + stagger)
                status = "Planned"
            
            drawing = {
                "id": str(uuid.uuid4()),
                "project_id": arch_project["id"],
                "drawing_type_id": drawing_type["id"],
                "title_override": None,
                "sequence": item["sequence"],
                "status": status,
                "assigned_to_id": None,
                "consultant_id": consultant["id"] if "Structural" in drawing_type.get("name", "") else None,
                "due_date": due_date.isoformat(),
                "file_latest": None,
                "version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.project_drawings.insert_one(drawing)
            drawings_created.append(drawing_type["name"])
    
    print(f"✅ Created {len(drawings_created)} drawings for AR-001")
    print(f"   - {', '.join(drawings_created)}")
    print(f"   - First drawing is OVERDUE to demonstrate reminders")
    
    # 6. Create demo Interior project
    int_project = {
        "id": str(uuid.uuid4()),
        "code": "IN-001",
        "title": "Apartment Interior - Demo",
        "type": "Interior",
        "status": "Concept",
        "client_id": demo_client["id"],
        "lead_architect_id": None,
        "project_manager_id": None,
        "start_date": datetime.now(timezone.utc).isoformat(),
        "expected_finish": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "site_address": "Flat 302, Tower A, Seawoods, Navi Mumbai",
        "plot_dimensions": "1200 sq ft carpet",
        "notes": "Contemporary style with modular kitchen",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.projects.insert_one(int_project)
    print(f"✅ Created project: {int_project['code']} - {int_project['title']}")
    
    # Generate first 3 drawings for IN-001
    int_items = await db.checklist_items.find(
        {"checklist_preset_id": int_preset["id"]}
    ).sort("sequence", 1).limit(3).to_list(3)
    
    int_drawings = []
    for item in int_items:
        drawing_type = await db.drawing_types.find_one({"id": item["drawing_type_id"]})
        if drawing_type:
            stagger = item["sequence"] // 10
            due_date = today + timedelta(days=drawing_type["default_due_offset_days"] + stagger)
            
            drawing = {
                "id": str(uuid.uuid4()),
                "project_id": int_project["id"],
                "drawing_type_id": drawing_type["id"],
                "title_override": None,
                "sequence": item["sequence"],
                "status": "Planned",
                "assigned_to_id": None,
                "consultant_id": None,
                "due_date": due_date.isoformat(),
                "file_latest": None,
                "version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.project_drawings.insert_one(drawing)
            int_drawings.append(drawing_type["name"])
    
    print(f"✅ Created {len(int_drawings)} drawings for IN-001")
    print(f"   - {', '.join(int_drawings)}")
    
    print("✨ Demo data seeded successfully!")
    print("\n📊 Summary:")
    print(f"   - 1 Client")
    print(f"   - 1 Consultant (Structural)")
    print(f"   - 2 Projects (AR-001, IN-001)")
    print(f"   - {len(drawings_created) + len(int_drawings)} Project Drawings")
    print(f"   - 1 Overdue drawing (for reminder demo)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
