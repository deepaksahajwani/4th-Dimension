#!/usr/bin/env python3
"""
Comprehensive Magic Link Test
Tests the complete magic link flow including URL resolution
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/app/backend')

async def test_complete_magic_link_flow():
    """Test the complete magic link flow"""
    try:
        from notification_triggers_v2 import get_magic_link_for_drawing
        from services.magic_link_service import validate_magic_token, build_destination_url
        
        # Test data from review request
        recipient_id = '54121be0-79b5-4db0-a08f-3a23a6ee935b'  # owner
        project_id = 'ed5e1e98-73e0-423f-af81-b04a5fd3f896'   # Aagam Heritage Bungalow
        drawing_id = 'ae595239-5c3b-4f23-a6c7-6ef5640af07e'
        
        print("🔗 TESTING COMPLETE MAGIC LINK FLOW")
        print("=" * 50)
        print(f"recipient_id: {recipient_id}")
        print(f"project_id: {project_id}")
        print(f"drawing_id: {drawing_id}")
        print()
        
        # Step 1: Generate magic link
        print("Step 1: Generating magic link...")
        magic_link = await get_magic_link_for_drawing(
            recipient_id=recipient_id,
            project_id=project_id,
            drawing_id=drawing_id
        )
        
        print(f"Generated: {magic_link}")
        
        if "/magic/" in magic_link:
            token = magic_link.split("/magic/")[-1]
            print(f"Token: {token[:16]}...")
            print()
            
            # Step 2: Validate token
            print("Step 2: Validating token...")
            token_data = await validate_magic_token(token)
            
            if token_data:
                print("✅ Token is valid")
                print(f"   destination_type: {token_data.get('destination_type')}")
                print(f"   destination_id: {token_data.get('destination_id')}")
                print(f"   extra_params: {token_data.get('extra_params')}")
                print()
                
                # Step 3: Build destination URL
                print("Step 3: Building destination URL...")
                destination_url = build_destination_url(token_data)
                print(f"Destination URL: {destination_url}")
                print()
                
                # Step 4: Verify format
                print("Step 4: Verifying URL format...")
                expected_new_format = f"/projects/{project_id}/drawing/{drawing_id}"
                old_format = f"?drawing={drawing_id}"
                
                if destination_url == expected_new_format:
                    print("✅ PASS: Magic link resolves to NEW format")
                    print(f"   Expected: {expected_new_format}")
                    print(f"   Actual:   {destination_url}")
                elif old_format in destination_url:
                    print("❌ FAIL: Magic link resolves to OLD format")
                    print(f"   Expected: {expected_new_format}")
                    print(f"   Actual:   {destination_url}")
                else:
                    print("❌ FAIL: Magic link resolves to unexpected format")
                    print(f"   Expected: {expected_new_format}")
                    print(f"   Actual:   {destination_url}")
                
                # Step 5: Verify token storage
                print()
                print("Step 5: Verifying token storage...")
                await verify_token_storage(token_data, project_id)
                
            else:
                print("❌ FAIL: Token validation failed")
        else:
            print("❌ FAIL: No magic token in link")
            
    except Exception as e:
        print(f"❌ FAIL: Exception in magic link flow: {str(e)}")
        import traceback
        traceback.print_exc()

async def verify_token_storage(token_data, expected_project_id):
    """Verify token storage details"""
    try:
        dest_type = token_data.get("destination_type")
        extra_params = token_data.get("extra_params", {})
        
        # Check destination_type
        if dest_type == "drawing_review":
            print("✅ PASS: destination_type is 'drawing_review'")
        else:
            print(f"❌ FAIL: destination_type is '{dest_type}' (expected: 'drawing_review')")
        
        # Check extra_params contains project_id
        if "project_id" in extra_params:
            actual_project_id = extra_params["project_id"]
            if actual_project_id == expected_project_id:
                print("✅ PASS: project_id in extra_params matches expected")
            else:
                print(f"❌ FAIL: project_id mismatch - expected: {expected_project_id}, actual: {actual_project_id}")
        else:
            print("❌ FAIL: project_id not found in extra_params")
            
    except Exception as e:
        print(f"❌ FAIL: Exception verifying token storage: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_complete_magic_link_flow())