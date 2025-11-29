#!/usr/bin/env python3
"""
Test database verification for ad-hoc tasks
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://archplanr.preview.emergentagent.com/api"

def test_database_verification():
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
        "title": "Database Verification Test",
        "description": "Please review the elevation drawings and provide feedback by EOD tomorrow.",
        "assigned_to_id": team_member["id"],
        "due_date_time": "2025-11-30T17:00:00Z",
        "priority": "HIGH",
        "category": "OTHER",
        "project_id": None,
        "status": "open"
    }
    
    create_response = requests.post(f"{BACKEND_URL}/tasks/ad-hoc", json=task_data, headers=headers)
    
    if create_response.status_code != 200:
        print(f"❌ Task creation failed: {create_response.status_code} - {create_response.text}")
        return
    
    created_task = create_response.json()
    task_id = created_task["id"]
    
    print(f"✅ Task created successfully!")
    print(f"Task ID: {task_id}")
    
    # Step 4: Verify task properties in response
    print("Step 4: Verifying task properties in response...")
    
    required_fields = ["id", "title", "assigned_to_id", "is_ad_hoc", "due_date_time", "priority", "week_assigned"]
    
    missing_fields = [field for field in required_fields if field not in created_task]
    
    if missing_fields:
        print(f"❌ Missing fields in response: {missing_fields}")
        return
    
    # Verify specific values
    checks = [
        (created_task.get("title") == "Database Verification Test", "title should be 'Database Verification Test'"),
        (created_task.get("is_ad_hoc") == True, "is_ad_hoc should be True"),
        (created_task.get("assigned_to_id") == team_member["id"], "assigned_to_id should match team member"),
        (created_task.get("priority") == "HIGH", "priority should be 'HIGH'"),
        (created_task.get("category") == "OTHER", "category should be 'OTHER'"),
        (created_task.get("status") == "open", "status should be 'open'"),
        (created_task.get("due_date_time") == "2025-11-30T17:00:00Z", "due_date_time should match"),
        ("week_assigned" in created_task, "week_assigned should be present")
    ]
    
    failed_checks = [msg for check, msg in checks if not check]
    
    if not failed_checks:
        print(f"✅ All task properties verified in response!")
        print(f"   is_ad_hoc: {created_task.get('is_ad_hoc')}")
        print(f"   week_assigned: {created_task.get('week_assigned')}")
        print(f"   assigned_to_name: {created_task.get('assigned_to_name')}")
    else:
        print(f"❌ Task validation failed: {'; '.join(failed_checks)}")
        return
    
    # Step 5: Verify task appears in dashboard with is_ad_hoc=True
    print("Step 5: Verifying task in dashboard...")
    dashboard_response = requests.get(f"{BACKEND_URL}/dashboard/weekly-progress/{team_member['id']}", headers=headers)
    
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard request failed: {dashboard_response.status_code}")
        return
    
    dashboard_data = dashboard_response.json()
    
    if "ad_hoc_tasks" not in dashboard_data:
        print(f"❌ ad_hoc_tasks section not found in dashboard")
        return
    
    ad_hoc_section = dashboard_data["ad_hoc_tasks"]
    tasks = ad_hoc_section.get('tasks', [])
    
    # Find our task
    our_task = None
    for task in tasks:
        if task.get('id') == task_id:
            our_task = task
            break
    
    if not our_task:
        print(f"❌ Task not found in dashboard")
        return
    
    # Verify dashboard task properties
    dashboard_checks = [
        (our_task.get("title") == "Database Verification Test", "title should match in dashboard"),
        (our_task.get("is_ad_hoc") == True, "is_ad_hoc should be True in dashboard"),
        (our_task.get("priority") == "HIGH", "priority should be HIGH in dashboard"),
        (our_task.get("status") == "open", "status should be open in dashboard"),
        ("urgency" in our_task, "urgency field should be present")
    ]
    
    failed_dashboard_checks = [msg for check, msg in dashboard_checks if not check]
    
    if not failed_dashboard_checks:
        print(f"✅ Task verified in dashboard!")
        print(f"   is_ad_hoc: {our_task.get('is_ad_hoc')}")
        print(f"   urgency: {our_task.get('urgency')}")
        print(f"   Total ad-hoc tasks: {ad_hoc_section.get('total')}")
    else:
        print(f"❌ Dashboard validation failed: {'; '.join(failed_dashboard_checks)}")
        return
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"✅ Task creation successful (200 OK)")
    print(f"✅ Response includes task ID and all task fields")
    print(f"✅ Task visible in weekly dashboard with urgency indicator")
    print(f"✅ Task has is_ad_hoc=True and week_assigned set")

if __name__ == "__main__":
    test_database_verification()