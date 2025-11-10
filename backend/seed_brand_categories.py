"""
Seed default brand categories for projects
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'archflow_db')

DEFAULT_BRAND_CATEGORIES = [
    {
        "category_name": "Faucets",
        "suggested_brands": ["Kohler", "Jaquar", "Grohe", "Hans Grohe", "Axor", "Other"]
    },
    {
        "category_name": "Plywood",
        "suggested_brands": ["Green", "Century", "Euro", "Kitply", "Other"]
    },
    {
        "category_name": "Tiles & Marble",
        "suggested_brands": ["Johnson", "Kajaria", "Somany", "RAK", "Nitco", "Other"]
    },
    {
        "category_name": "Sanitaryware",
        "suggested_brands": ["Kohler", "Jaquar", "Hindware", "Cera", "Parryware", "Other"]
    },
    {
        "category_name": "Lights/Lighting",
        "suggested_brands": ["Philips", "Havells", "Wipro", "Crompton", "Syska", "Other"]
    },
    {
        "category_name": "Paints/Colors",
        "suggested_brands": ["Asian Paints", "Berger", "Dulux", "Nerolac", "Nippon", "Other"]
    },
    {
        "category_name": "Hardware/Handles",
        "suggested_brands": ["Dorset", "Hettich", "Ebco", "Hafele", "Other"]
    },
    {
        "category_name": "Glass",
        "suggested_brands": ["Saint-Gobain", "AIS", "Modi", "Other"]
    },
    {
        "category_name": "Kitchen Appliances",
        "suggested_brands": ["Bosch", "Faber", "Elica", "Kutchina", "Glen", "Other"]
    },
    {
        "category_name": "False Ceiling Materials",
        "suggested_brands": ["Armstrong", "Gyproc", "Saint-Gobain", "USG Boral", "Other"]
    },
    {
        "category_name": "Flooring",
        "suggested_brands": ["Pergo", "Quick Step", "Armstrong", "Tarkett", "Other"]
    },
    {
        "category_name": "Furniture/Upholstery",
        "suggested_brands": ["Godrej", "Durian", "Urban Ladder", "Pepperfry", "Other"]
    },
    {
        "category_name": "Automation Systems",
        "suggested_brands": ["Schneider", "Legrand", "Philips Hue", "Google Home", "Amazon Alexa", "Other"]
    },
    {
        "category_name": "HVAC",
        "suggested_brands": ["Daikin", "Hitachi", "LG", "Blue Star", "Voltas", "Other"]
    },
    {
        "category_name": "Doors & Windows",
        "suggested_brands": ["Fenesta", "AIS", "UPVC", "Wood", "Aluminum", "Other"]
    },
    {
        "category_name": "Electrical Wiring",
        "suggested_brands": ["Polycab", "Havells", "Finolex", "KEI", "Other"]
    },
    {
        "category_name": "Switches & Sockets",
        "suggested_brands": ["Legrand", "Schneider", "Anchor", "Havells", "Other"]
    },
    {
        "category_name": "Waterproofing",
        "suggested_brands": ["Dr. Fixit", "Fosroc", "BASF", "Sika", "Other"]
    }
]

async def seed_brand_categories():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🎨 Seeding brand categories...")
    
    # Clear existing brand categories
    await db.brand_categories.delete_many({})
    
    # Insert default categories
    for category in DEFAULT_BRAND_CATEGORIES:
        brand_category = {
            "id": str(uuid.uuid4()),
            "category_name": category["category_name"],
            "suggested_brands": category["suggested_brands"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.brand_categories.insert_one(brand_category)
        print(f"✅ Created brand category: {category['category_name']}")
    
    print(f"✅ Seeded {len(DEFAULT_BRAND_CATEGORIES)} brand categories")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_brand_categories())
