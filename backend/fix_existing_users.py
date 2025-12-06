"""
One-time script to create client/contractor/consultant records for existing registered users
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from uuid import uuid4

async def fix_existing_users():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['architecture_firm']
    
    # Find all users who are clients/contractors/consultants
    users = await db.users.find({
        "role": {"$in": ["client", "contractor", "consultant"]},
        "approval_status": {"$in": ["approved", "pending"]}
    }, {"_id": 0}).to_list(1000)
    
    print(f"Found {len(users)} client/contractor/consultant users")
    
    for user in users:
        user_id = user['id']
        role = user['role']
        name = user['name']
        email = user['email']
        phone = user.get('mobile', '')
        
        if role == 'client':
            # Check if client record exists
            existing = await db.clients.find_one({"user_id": user_id})
            if not existing:
                client_record = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "contact_person": name,
                    "email": email,
                    "phone": phone,
                    "address": f"{user.get('address_line_1', '')}, {user.get('city', '')}, {user.get('state', '')}".strip(', '),
                    "created_at": datetime.now(timezone.utc),
                    "created_by": user_id,
                    "notes": "Auto-created from existing user account",
                    "archived": False
                }
                await db.clients.insert_one(client_record)
                print(f"✅ Created client record for {name}")
            else:
                print(f"⏭️  Client record already exists for {name}")
                
        elif role == 'contractor':
            existing = await db.contractors.find_one({"user_id": user_id})
            if not existing:
                contractor_record = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": f"{user.get('address_line_1', '')}, {user.get('city', '')}, {user.get('state', '')}".strip(', '),
                    "contractor_type": "Other",
                    "created_at": datetime.now(timezone.utc),
                    "created_by": user_id,
                    "notes": "Auto-created from existing user account"
                }
                await db.contractors.insert_one(contractor_record)
                print(f"✅ Created contractor record for {name}")
            else:
                print(f"⏭️  Contractor record already exists for {name}")
                
        elif role == 'consultant':
            existing = await db.consultants.find_one({"user_id": user_id})
            if not existing:
                consultant_record = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": f"{user.get('address_line_1', '')}, {user.get('city', '')}, {user.get('state', '')}".strip(', '),
                    "type": "Other",
                    "created_at": datetime.now(timezone.utc),
                    "created_by": user_id,
                    "notes": "Auto-created from existing user account"
                }
                await db.consultants.insert_one(consultant_record)
                print(f"✅ Created consultant record for {name}")
            else:
                print(f"⏭️  Consultant record already exists for {name}")
    
    print("\n✅ Migration complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_existing_users())
