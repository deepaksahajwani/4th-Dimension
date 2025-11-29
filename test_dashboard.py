#!/usr/bin/env python3
"""
Test weekly dashboard endpoint for ad-hoc tasks
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://archplanr.preview.emergentagent.com/api"

def test_dashboard():
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
    
    # Step 3: Test weekly dashboard
    print("Step 3: Testing weekly dashboard...")
    dashboard_response = requests.get(f"{BACKEND_URL}/dashboard/weekly-progress/{team_member['id']}", headers=headers)
    
    print(f"Dashboard response status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code == 200:
        try:
            dashboard_data = dashboard_response.json()
            print(f"✅ Dashboard data retrieved successfully!")
            
            # Check for ad_hoc_tasks section
            if "ad_hoc_tasks" in dashboard_data:
                ad_hoc_section = dashboard_data["ad_hoc_tasks"]
                print(f"📋 Ad-hoc tasks section found:")
                print(f"   Total: {ad_hoc_section.get('total', 0)}")
                print(f"   Completed: {ad_hoc_section.get('completed', 0)}")
                print(f"   Progress: {ad_hoc_section.get('progress_percentage', 0)}%")
                
                tasks = ad_hoc_section.get('tasks', [])
                print(f"   Tasks count: {len(tasks)}")
                
                for i, task in enumerate(tasks):
                    print(f"   Task {i+1}:")
                    print(f"     ID: {task.get('id')}")
                    print(f"     Title: {task.get('title')}")
                    print(f"     Priority: {task.get('priority')}")
                    print(f"     Status: {task.get('status')}")
                    print(f"     Due: {task.get('due_date_time')}")
                    print(f"     Urgency: {task.get('urgency')}")
                    
                    if task.get('title') == 'Quick Task Test':
                        print(f"   ✅ Found our test task!")
                        
                        # Verify task properties
                        checks = [
                            (task.get('is_ad_hoc') == True, "is_ad_hoc should be True"),
                            (task.get('priority') == 'HIGH', "priority should be HIGH"),
                            (task.get('status') == 'open', "status should be open"),
                            ('urgency' in task, "urgency field should be present")
                        ]
                        
                        failed_checks = [msg for check, msg in checks if not check]
                        
                        if not failed_checks:
                            print(f"   ✅ All task properties verified!")
                        else:
                            print(f"   ❌ Task validation failed: {'; '.join(failed_checks)}")
                        
                        return True
                
                print(f"   ❌ Test task 'Quick Task Test' not found in dashboard")
                return False
            else:
                print(f"❌ ad_hoc_tasks section not found in dashboard")
                print(f"Available sections: {list(dashboard_data.keys())}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {dashboard_response.text}")
            return False
    else:
        print(f"❌ Dashboard request failed: {dashboard_response.status_code}")
        print(f"Response: {dashboard_response.text}")
        return False

if __name__ == "__main__":
    test_dashboard()