#!/usr/bin/env python3
"""
Simple test for ad-hoc task creation endpoint
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://archplanr.preview.emergentagent.com/api"

def test_adhoc_task():
    # Step 1: Login as owner
    print("Step 1: Logging in as owner...")
    login_data = {
        "email": "deepaksahajwani@gmail.com",
        "password": "testpassword"
    }
    
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    login_result = login_response.json()
    token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful")
    
    # Step 2: Get team member ID
    print("Step 2: Getting team member...")
    users_response = requests.get(f"{BACKEND_URL}/users", headers=headers)
    
    if users_response.status_code != 200:
        print(f"❌ Failed to get users: {users_response.status_code}")
        return
    
    users = users_response.json()
    team_member = None
    
    for user in users:
        if user.get("email") == "testvoice@example.com":
            team_member = user
            break
    
    if not team_member:
        print("❌ Team member testvoice@example.com not found")
        return
    
    print(f"✅ Found team member: {team_member['name']} ({team_member['id']})")
    
    # Step 3: Create ad-hoc task
    print("Step 3: Creating ad-hoc task...")
    task_data = {
        "title": "Quick Task Test",
        "description": "Please review the elevation drawings and provide feedback by EOD tomorrow.",
        "assigned_to_id": team_member["id"],
        "due_date_time": "2025-11-30T17:00:00Z",
        "priority": "HIGH",
        "category": "OTHER",
        "project_id": None,
        "status": "open"
    }
    
    print(f"Task data: {json.dumps(task_data, indent=2)}")
    
    create_response = requests.post(f"{BACKEND_URL}/tasks/ad-hoc", json=task_data, headers=headers)
    
    print(f"Response status: {create_response.status_code}")
    print(f"Response headers: {dict(create_response.headers)}")
    
    if create_response.status_code == 200:
        try:
            result = create_response.json()
            print(f"✅ Task created successfully!")
            print(f"Task ID: {result.get('id')}")
            print(f"Title: {result.get('title')}")
            print(f"Is Ad-hoc: {result.get('is_ad_hoc')}")
            print(f"Assigned to: {result.get('assigned_to_name')}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {create_response.text}")
    else:
        print(f"❌ Task creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")

if __name__ == "__main__":
    test_adhoc_task()