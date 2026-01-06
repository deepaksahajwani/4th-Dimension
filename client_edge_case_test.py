#!/usr/bin/env python3
"""
Additional edge case tests for Client API project_types field
"""

import requests
import json
import uuid

BACKEND_URL = "https://mobile-first-14.preview.emergentagent.com/api"

def test_edge_cases():
    """Test edge cases for project_types field"""
    session = requests.Session()
    
    # Create test user
    test_email = f"edgetest_{uuid.uuid4().hex[:8]}@example.com"
    user_register = {
        "email": test_email,
        "password": "EdgeTest123!",
        "name": "Edge Test User"
    }
    
    register_response = session.post(f"{BACKEND_URL}/auth/register", json=user_register)
    if register_response.status_code != 200:
        print("❌ Failed to create test user")
        return False
    
    auth_token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Complete profile if needed
    register_data = register_response.json()
    if register_data.get("requires_profile_completion"):
        profile_data = {
            "full_name": "Edge Test User",
            "address_line_1": "123 Test Street",
            "address_line_2": "Test Area", 
            "city": "Test City",
            "state": "Test State",
            "pin_code": "123456",
            "email": test_email,
            "mobile": "+919876543210",
            "date_of_birth": "1990-01-15",
            "date_of_joining": "2024-01-01",
            "gender": "male",
            "marital_status": "single",
            "role": "architect"
        }
        
        profile_response = session.post(f"{BACKEND_URL}/profile/complete", 
                                       json=profile_data, headers=headers)
        if profile_response.status_code != 200:
            print("❌ Failed to complete profile")
            return False
    
    print("✅ Test user setup complete")
    
    # Test cases
    test_cases = [
        {
            "name": "Duplicate project_types",
            "project_types": ["Architecture", "Architecture", "Interior"],
            "expected_success": True,
            "description": "Should handle duplicate values"
        },
        {
            "name": "Case sensitivity",
            "project_types": ["architecture", "INTERIOR", "Landscape"],
            "expected_success": True,
            "description": "Should handle different cases"
        },
        {
            "name": "Invalid project_type",
            "project_types": ["Architecture", "InvalidType", "Interior"],
            "expected_success": True,
            "description": "Should accept any string values (no validation enforced)"
        },
        {
            "name": "Very long project_type name",
            "project_types": ["Architecture", "A" * 1000],
            "expected_success": True,
            "description": "Should handle very long strings"
        },
        {
            "name": "Special characters",
            "project_types": ["Architecture & Design", "Interior-Design", "Landscape/Planning"],
            "expected_success": True,
            "description": "Should handle special characters"
        },
        {
            "name": "Unicode characters",
            "project_types": ["建築", "インテリア", "Архитектура"],
            "expected_success": True,
            "description": "Should handle unicode characters"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases):
        try:
            client_data = {
                "name": f"Edge Test Client {i+1} - {case['name']}",
                "project_types": case["project_types"],
                "contact_person": "Edge Tester",
                "email": f"edge{i+1}@test.com"
            }
            
            response = session.post(f"{BACKEND_URL}/clients", json=client_data, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                actual_types = response_data.get("project_types", [])
                
                print(f"✅ {case['name']}: SUCCESS")
                print(f"   Input: {case['project_types']}")
                print(f"   Output: {actual_types}")
                print(f"   Description: {case['description']}")
                results.append(True)
            else:
                print(f"❌ {case['name']}: FAILED")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {case['name']}: EXCEPTION - {str(e)}")
            results.append(False)
        
        print()
    
    # Test project_types field in different API operations
    print("Testing project_types in different operations...")
    
    # Create a client for update/get tests
    base_client = {
        "name": "Base Test Client",
        "project_types": ["Architecture", "Interior"],
        "contact_person": "Base Tester",
        "email": "base@test.com"
    }
    
    create_response = session.post(f"{BACKEND_URL}/clients", json=base_client, headers=headers)
    if create_response.status_code == 200:
        client_id = create_response.json()["id"]
        
        # Test GET individual client
        get_response = session.get(f"{BACKEND_URL}/clients/{client_id}", headers=headers)
        if get_response.status_code == 200:
            client_data = get_response.json()
            if client_data.get("project_types") == ["Architecture", "Interior"]:
                print("✅ GET individual client: project_types preserved")
                results.append(True)
            else:
                print(f"❌ GET individual client: project_types mismatch - {client_data.get('project_types')}")
                results.append(False)
        else:
            print(f"❌ GET individual client failed: {get_response.status_code}")
            results.append(False)
        
        # Test PUT update
        update_data = {
            "name": "Updated Base Client",
            "project_types": ["Landscape", "Planning", "Architecture"],
            "contact_person": "Updated Tester",
            "phone": "+919876543210",
            "email": "updated@test.com",
            "address": "Updated Address",
            "notes": "Updated notes",
            "archived": False
        }
        
        update_response = session.put(f"{BACKEND_URL}/clients/{client_id}", json=update_data, headers=headers)
        if update_response.status_code == 200:
            # Verify update
            verify_response = session.get(f"{BACKEND_URL}/clients/{client_id}", headers=headers)
            if verify_response.status_code == 200:
                updated_client = verify_response.json()
                expected_types = ["Landscape", "Planning", "Architecture"]
                if updated_client.get("project_types") == expected_types:
                    print("✅ PUT update client: project_types updated correctly")
                    results.append(True)
                else:
                    print(f"❌ PUT update client: project_types mismatch - Expected: {expected_types}, Got: {updated_client.get('project_types')}")
                    results.append(False)
            else:
                print(f"❌ PUT update verification failed: {verify_response.status_code}")
                results.append(False)
        else:
            print(f"❌ PUT update failed: {update_response.status_code} - {update_response.text}")
            results.append(False)
        
        # Test GET all clients
        list_response = session.get(f"{BACKEND_URL}/clients", headers=headers)
        if list_response.status_code == 200:
            clients = list_response.json()
            found_client = None
            for client in clients:
                if client.get("id") == client_id:
                    found_client = client
                    break
            
            if found_client and "project_types" in found_client:
                print("✅ GET all clients: project_types field present")
                results.append(True)
            else:
                print("❌ GET all clients: project_types field missing")
                results.append(False)
        else:
            print(f"❌ GET all clients failed: {list_response.status_code}")
            results.append(False)
    else:
        print(f"❌ Failed to create base client: {create_response.status_code}")
        results.extend([False, False, False])
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 EDGE CASE TEST SUMMARY")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    return passed == total

if __name__ == "__main__":
    success = test_edge_cases()
    exit(0 if success else 1)