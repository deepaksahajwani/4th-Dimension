"""
Seed sample clients and link to existing projects
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from datetime import datetime, timezone
import uuid

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'architecture_firm')

async def seed_clients():
    client_conn = AsyncIOMotorClient(mongo_url)
    db = client_conn[db_name]
    
    print("🌱 Seeding sample clients...")
    
    # Delete old demo client if exists
    await db.clients.delete_many({"name": "Demo Client Pvt Ltd"})
    
    # Create 3 sample clients
    clients = [
        {
            "id": str(uuid.uuid4()),
            "name": "Sharma Constructions Pvt Ltd",
            "contact_person": "Mr. Rajesh Sharma",
            "phone": "+919876543210",
            "email": "rajesh@sharma.com",
            "address": "Plot 12, Sector 15, Vashi, Navi Mumbai - 400703",
            "notes": "Residential and commercial builder. Prefer modern architecture.",
            "created_by_id": None,
            "owner_team_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Patel Lifestyle Homes",
            "contact_person": "Mrs. Priya Patel",
            "phone": "+919123456789",
            "email": "priya@patellifestyle.com",
            "address": "203, Maker Chambers, Nariman Point, Mumbai - 400021",
            "notes": "Luxury home developers. Looking for interior design services.",
            "created_by_id": None,
            "owner_team_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Desai Enterprises",
            "contact_person": "Mr. Anil Desai",
            "phone": "+919988776655",
            "email": "anil@desai.co.in",
            "address": "Bungalow 45, Juhu Scheme, Mumbai - 400049",
            "notes": "Individual client. Own bungalow renovation project.",
            "created_by_id": None,
            "owner_team_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
    ]
    
    await db.clients.insert_many(clients)
    print(f"✅ Created {len(clients)} sample clients")
    
    # Link to existing projects
    ar_project = await db.projects.find_one({"code": "AR-001"})
    in_project = await db.projects.find_one({"code": "IN-001"})
    
    if ar_project:
        await db.projects.update_one(
            {"code": "AR-001"},
            {"$set": {"client_id": clients[0]["id"]}}
        )
        print(f"✅ Linked AR-001 to {clients[0]['name']}")
    
    if in_project:
        await db.projects.update_one(
            {"code": "IN-001"},
            {"$set": {"client_id": clients[1]["id"]}}
        )
        print(f"✅ Linked IN-001 to {clients[1]['name']}")
    
    print("✨ Client seeding complete!")
    print("\n📊 Clients created:")
    for c in clients:
        print(f"   - {c['name']} ({c['contact_person']})")
    
    client_conn.close()

if __name__ == "__main__":
    asyncio.run(seed_clients())
