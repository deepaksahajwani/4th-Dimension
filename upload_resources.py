#!/usr/bin/env python3
"""
Script to upload resource documents to the 4th Dimension portal.
This script uploads files to existing resource entries by matching titles.
"""

import requests
import os
import sys

# Configuration
API_URL = os.environ.get('API_URL', 'https://architect-notify.preview.emergentagent.com')

# Map of file to resource title
FILE_TITLE_MAP = {
    "01_welcome_to_4d.docx": "Welcome to 4th Dimension",
    "02_employee_handbook.docx": "Employee Handbook",
    "03_it_setup_guide.docx": "IT Setup Guide",
    "04_drawing_standards.docx": "Drawing Standards Manual",
    "05_cad_layer_standards.docx": "CAD Layer Standards",
    "06_brand_guidelines.docx": "Brand Guidelines",
    "07_project_proposal_template.docx": "Project Proposal Template",
    "08_site_visit_report.docx": "Site Visit Report Template",
    "09_meeting_minutes.docx": "Meeting Minutes Template",
    "10_leave_policy.docx": "Leave Policy",
    "11_wfh_policy.docx": "Work From Home Policy",
    "12_site_safety_guidelines.docx": "Site Safety Guidelines",
    "13_portal_user_guide.docx": "Portal User Guide",
    "14_autocad_quick_reference.docx": "AutoCAD Quick Reference",
}

def main():
    # Get auth token
    login_resp = requests.post(
        f"{API_URL}/api/auth/login",
        json={"email": "deepaksahajwani@gmail.com", "password": "Deepak@2025"}
    )
    
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        sys.exit(1)
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Logged in successfully")
    
    # Get existing resources
    existing_resp = requests.get(f"{API_URL}/api/resources", headers=headers)
    if existing_resp.status_code != 200:
        print(f"Failed to get resources: {existing_resp.text}")
        sys.exit(1)
    
    existing = existing_resp.json()
    title_to_id = {r['title']: r['id'] for r in existing}
    print(f"📋 Found {len(existing)} existing resources")
    
    uploaded_count = 0
    not_found_count = 0
    
    for filename, title in FILE_TITLE_MAP.items():
        filepath = f"/app/{filename}"
        
        # Check if resource exists
        if title not in title_to_id:
            print(f"⚠️  No resource entry found for '{title}'")
            not_found_count += 1
            continue
        
        resource_id = title_to_id[title]
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        # Upload the file
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            upload_resp = requests.post(
                f"{API_URL}/api/resources/{resource_id}/upload",
                headers=headers,
                files=files
            )
        
        if upload_resp.status_code == 200:
            print(f"📤 Uploaded '{filename}' → '{title}'")
            uploaded_count += 1
        else:
            print(f"❌ Failed to upload '{filename}': {upload_resp.text}")
    
    print(f"\n{'='*50}")
    print(f"✅ Upload complete!")
    print(f"   📤 Uploaded: {uploaded_count}")
    print(f"   ⚠️  Not found: {not_found_count}")

if __name__ == "__main__":
    main()
