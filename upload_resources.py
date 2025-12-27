#!/usr/bin/env python3
"""
Script to upload resource documents to the 4th Dimension portal.
This script creates resource entries and uploads the corresponding DOCX files.
"""

import requests
import os
import sys

# Configuration
API_URL = os.environ.get('API_URL', 'https://architect-notify.preview.emergentagent.com')

# Map of file to resource details
RESOURCES = [
    {
        "filename": "01_welcome_to_4d.docx",
        "title": "Welcome to 4th Dimension",
        "description": "Introduction to our firm, culture, and values",
        "category": "onboarding",
        "type": "document",
        "featured": True,
        "order": 1,
        "tags": ["welcome", "introduction", "culture"]
    },
    {
        "filename": "02_employee_handbook.docx",
        "title": "Employee Handbook",
        "description": "Complete guide to company policies, benefits, and procedures",
        "category": "onboarding",
        "type": "document",
        "featured": True,
        "order": 2,
        "tags": ["policies", "handbook", "employee"]
    },
    {
        "filename": "03_it_setup_guide.docx",
        "title": "IT Setup Guide",
        "description": "How to set up your workstation, email, and software",
        "category": "onboarding",
        "type": "document",
        "order": 3,
        "tags": ["IT", "setup", "software", "workstation"]
    },
    {
        "filename": "04_drawing_standards.docx",
        "title": "Drawing Standards Manual",
        "description": "Standard conventions for architectural drawings",
        "category": "standards",
        "type": "document",
        "featured": True,
        "order": 1,
        "tags": ["drawings", "standards", "architecture"]
    },
    {
        "filename": "05_cad_layer_standards.docx",
        "title": "CAD Layer Standards",
        "description": "AutoCAD layer naming conventions and colors",
        "category": "standards",
        "type": "document",
        "order": 2,
        "tags": ["CAD", "AutoCAD", "layers", "standards"]
    },
    {
        "filename": "06_brand_guidelines.docx",
        "title": "Brand Guidelines",
        "description": "Logo usage, colors, fonts, and presentation standards",
        "category": "standards",
        "type": "document",
        "order": 3,
        "tags": ["brand", "logo", "colors", "fonts"]
    },
    {
        "filename": "07_project_proposal_template.docx",
        "title": "Project Proposal Template",
        "description": "Standard template for client proposals",
        "category": "templates",
        "type": "document",
        "order": 1,
        "tags": ["template", "proposal", "client"]
    },
    {
        "filename": "08_site_visit_report.docx",
        "title": "Site Visit Report Template",
        "description": "Template for documenting site visits",
        "category": "templates",
        "type": "document",
        "order": 2,
        "tags": ["template", "site visit", "report"]
    },
    {
        "filename": "09_meeting_minutes.docx",
        "title": "Meeting Minutes Template",
        "description": "Standard format for meeting documentation",
        "category": "templates",
        "type": "document",
        "order": 3,
        "tags": ["template", "meeting", "minutes"]
    },
    {
        "filename": "10_leave_policy.docx",
        "title": "Leave Policy",
        "description": "Guidelines for leave applications and approvals",
        "category": "policies",
        "type": "document",
        "order": 1,
        "tags": ["leave", "policy", "HR"]
    },
    {
        "filename": "11_wfh_policy.docx",
        "title": "Work From Home Policy",
        "description": "Remote work guidelines and expectations",
        "category": "policies",
        "type": "document",
        "order": 2,
        "tags": ["WFH", "remote", "policy"]
    },
    {
        "filename": "12_site_safety_guidelines.docx",
        "title": "Site Safety Guidelines",
        "description": "Safety protocols for site visits",
        "category": "policies",
        "type": "document",
        "order": 3,
        "tags": ["safety", "site", "protocols"]
    },
    {
        "filename": "13_portal_user_guide.docx",
        "title": "Portal User Guide",
        "description": "How to use the 4th Dimension project portal",
        "category": "tutorials",
        "type": "document",
        "featured": True,
        "order": 1,
        "tags": ["portal", "guide", "tutorial"]
    },
    {
        "filename": "14_autocad_quick_reference.docx",
        "title": "AutoCAD Quick Reference",
        "description": "Keyboard shortcuts and common commands for AutoCAD",
        "category": "tools",
        "type": "document",
        "order": 1,
        "tags": ["AutoCAD", "shortcuts", "commands", "reference"]
    }
]

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
    
    # First, check existing resources
    existing_resp = requests.get(f"{API_URL}/api/resources", headers=headers)
    if existing_resp.status_code == 200:
        existing = existing_resp.json()
        existing_titles = {r['title'] for r in existing}
        print(f"📋 Found {len(existing)} existing resources")
    else:
        existing_titles = set()
    
    uploaded_count = 0
    skipped_count = 0
    
    for resource in RESOURCES:
        title = resource["title"]
        filename = resource["filename"]
        filepath = f"/app/{filename}"
        
        # Check if already exists
        if title in existing_titles:
            print(f"⏭️  Skipping '{title}' - already exists")
            skipped_count += 1
            continue
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        # Create resource entry
        resource_data = {
            "title": title,
            "description": resource["description"],
            "category": resource["category"],
            "type": resource["type"],
            "featured": resource.get("featured", False),
            "order": resource["order"],
            "tags": resource.get("tags", []),
            "visible_to": ["all"]
        }
        
        create_resp = requests.post(
            f"{API_URL}/api/resources",
            headers=headers,
            json=resource_data
        )
        
        if create_resp.status_code not in [200, 201]:
            print(f"❌ Failed to create resource '{title}': {create_resp.text}")
            continue
        
        resource_id = create_resp.json()["id"]
        print(f"📝 Created resource '{title}' (ID: {resource_id})")
        
        # Upload the file
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            upload_resp = requests.post(
                f"{API_URL}/api/resources/{resource_id}/upload",
                headers=headers,
                files=files
            )
        
        if upload_resp.status_code == 200:
            print(f"📤 Uploaded file '{filename}'")
            uploaded_count += 1
        else:
            print(f"❌ Failed to upload file '{filename}': {upload_resp.text}")
    
    print(f"\n{'='*50}")
    print(f"✅ Upload complete!")
    print(f"   📤 Uploaded: {uploaded_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")

if __name__ == "__main__":
    main()
