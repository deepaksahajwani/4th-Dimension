#!/usr/bin/env python3
"""
Test Magic Link Function Directly
This script tests the get_magic_link_for_drawing function directly
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/app/backend')

async def test_magic_link_function():
    """Test the magic link generation function directly"""
    try:
        from notification_triggers_v2 import get_magic_link_for_drawing
        
        # Test data from review request
        recipient_id = '54121be0-79b5-4db0-a08f-3a23a6ee935b'  # owner
        project_id = 'ed5e1e98-73e0-423f-af81-b04a5fd3f896'   # Aagam Heritage Bungalow
        drawing_id = 'ae595239-5c3b-4f23-a6c7-6ef5640af07e'
        
        print(f"Testing get_magic_link_for_drawing with:")
        print(f"  recipient_id: {recipient_id}")
        print(f"  project_id: {project_id}")
        print(f"  drawing_id: {drawing_id}")
        print()
        
        # Call the function
        magic_link = await get_magic_link_for_drawing(
            recipient_id=recipient_id,
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        print(f"Generated magic link: {magic_link}")
        print()
        
        # Check the format
        expected_new_format = f"/projects/{project_id}/drawing/{drawing_id}"
        old_format = f"?drawing={drawing_id}"
        
        if expected_new_format in magic_link:
            print("✅ PASS: Magic link uses NEW format (/projects/{projectId}/drawing/{drawingId})")
            
            # Check if it's a magic link or direct link
            if "/magic/" in magic_link:
                token = magic_link.split("/magic/")[-1]
                print(f"✅ Magic token generated: {token[:16]}...")
                
                # Test token storage
                await test_token_storage(token, project_id)
            else:
                print("✅ Direct link generated (fallback)")
                
        elif old_format in magic_link:
            print("❌ FAIL: Magic link uses OLD format (?drawing=)")
        else:
            print(f"❌ FAIL: Magic link format unexpected: {magic_link}")
            
    except Exception as e:
        print(f"❌ FAIL: Exception testing magic link function: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_token_storage(token, expected_project_id):
    """Test that the token is stored correctly in database"""
    try:
        from utils.database import get_database
        
        db = get_database()
        
        # Find the token in database
        token_doc = await db.magic_tokens.find_one({"token": token}, {"_id": 0})
        
        if token_doc:
            dest_type = token_doc.get("destination_type")
            extra_params = token_doc.get("extra_params", {})
            
            print(f"✅ Token found in database:")
            print(f"   destination_type: {dest_type}")
            print(f"   extra_params: {extra_params}")
            
            if dest_type == "drawing_review":
                print("✅ PASS: destination_type is 'drawing_review'")
            else:
                print(f"❌ FAIL: destination_type is '{dest_type}' (expected: 'drawing_review')")
            
            if "project_id" in extra_params and extra_params["project_id"] == expected_project_id:
                print("✅ PASS: project_id in extra_params matches expected")
            else:
                print(f"❌ FAIL: project_id in extra_params: {extra_params.get('project_id')} (expected: {expected_project_id})")
        else:
            print("❌ FAIL: Token not found in database")
            
    except Exception as e:
        print(f"❌ FAIL: Exception testing token storage: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_magic_link_function())