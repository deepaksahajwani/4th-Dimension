#!/usr/bin/env python3
"""
Drawing Resolve Revision Functionality Test
Tests the specific issue reported: clicking "Resolve" button does nothing
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://project-nexus-39.preview.emergentagent.com/api"

class DrawingRevisionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.owner_token = None
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def test_drawing_resolve_revision_end_to_end(self):
        """Test the complete drawing resolve revision functionality end-to-end"""
        print(f"\n🎯 Testing Drawing Resolve Revision Functionality End-to-End")
        print("=" * 70)
        
        # Step 1: Login as owner (owner@test.com / testpassword)
        try:
            print("Step 1: Login as owner (owner@test.com / testpassword)...")
            owner_credentials = {
                "email": "owner@test.com",
                "password": "testpassword"
            }
            
            login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=owner_credentials)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                
                if login_data.get("user", {}).get("is_owner") == True:
                    self.owner_token = login_data["access_token"]
                    self.log_result("Step 1 - Owner Login", True, 
                                  "Owner successfully authenticated")
                else:
                    self.log_result("Step 1 - Owner Login", False, 
                                  "User is not marked as owner")
                    return False
            else:
                self.log_result("Step 1 - Owner Login", False, 
                              f"Owner login failed: {login_response.status_code} - {login_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 1 - Owner Login", False, f"Exception: {str(e)}")
            return False

        owner_headers = {"Authorization": f"Bearer {self.owner_token}"}
        
        # Step 2: Get a project with drawings
        try:
            print("Step 2: Get a project with drawings...")
            projects_response = self.session.get(f"{BACKEND_URL}/projects", headers=owner_headers)
            
            if projects_response.status_code == 200:
                projects_data = projects_response.json()
                
                if len(projects_data) > 0:
                    # Look for a project with drawings
                    project_with_drawings = None
                    for project in projects_data:
                        drawings_response = self.session.get(f"{BACKEND_URL}/projects/{project['id']}/drawings", 
                                                           headers=owner_headers)
                        if drawings_response.status_code == 200:
                            drawings = drawings_response.json()
                            if len(drawings) > 0:
                                project_with_drawings = project
                                self.test_drawings = drawings
                                break
                    
                    if project_with_drawings:
                        self.test_project = project_with_drawings
                        self.log_result("Step 2 - Get Project with Drawings", True, 
                                      f"Found project '{self.test_project.get('title')}' with {len(self.test_drawings)} drawings")
                    else:
                        self.log_result("Step 2 - Get Project with Drawings", False, 
                                      "No projects with drawings found")
                        return False
                else:
                    self.log_result("Step 2 - Get Project with Drawings", False, 
                                  "No projects found")
                    return False
            else:
                self.log_result("Step 2 - Get Project with Drawings", False, 
                              f"Failed to get projects: {projects_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step 2 - Get Project with Drawings", False, f"Exception: {str(e)}")
            return False

        # Step 3: Find a drawing that has been issued (or issue one)
        try:
            print("Step 3: Find a drawing that has been issued...")
            
            # Look for an issued drawing first
            issued_drawing = None
            for drawing in self.test_drawings:
                if drawing.get('is_issued', False):
                    issued_drawing = drawing
                    break
            
            if not issued_drawing:
                # No issued drawing found, issue the first available drawing
                first_drawing = self.test_drawings[0]
                drawing_id = first_drawing['id']
                
                print(f"   No issued drawing found. Issuing drawing: {first_drawing.get('name')}")
                
                issue_payload = {
                    "is_issued": True
                }
                
                issue_response = self.session.put(f"{BACKEND_URL}/drawings/{drawing_id}", 
                                                json=issue_payload, headers=owner_headers)
                
                if issue_response.status_code == 200:
                    issued_drawing = issue_response.json()
                    self.log_result("Step 3 - Issue Drawing", True, 
                                  f"Successfully issued drawing: {issued_drawing.get('name')}")
                else:
                    self.log_result("Step 3 - Issue Drawing", False, 
                                  f"Failed to issue drawing: {issue_response.status_code} - {issue_response.text}")
                    return False
            else:
                self.log_result("Step 3 - Find Issued Drawing", True, 
                              f"Found issued drawing: {issued_drawing.get('name')}")
            
            self.test_drawing = issued_drawing
            
        except Exception as e:
            self.log_result("Step 3 - Find/Issue Drawing", False, f"Exception: {str(e)}")
            return False

        drawing_id = self.test_drawing['id']
        
        # Step 4: Create Revision
        try:
            print("Step 4: Create revision...")
            
            revision_payload = {
                "has_pending_revision": True,
                "revision_notes": "Test revision notes - Need to update room dimensions and add window details",
                "revision_due_date": "2025-11-15"
            }
            
            revision_response = self.session.put(f"{BACKEND_URL}/drawings/{drawing_id}", 
                                               json=revision_payload, headers=owner_headers)
            
            if revision_response.status_code == 200:
                revision_data = revision_response.json()
                
                # Verify response shows has_pending_revision = true
                if revision_data.get('has_pending_revision') == True:
                    # Verify is_issued is reset to false
                    if revision_data.get('is_issued') == False:
                        self.log_result("Step 4 - Create Revision", True, 
                                      f"Revision created successfully. has_pending_revision: {revision_data.get('has_pending_revision')}, is_issued: {revision_data.get('is_issued')}")
                    else:
                        self.log_result("Step 4 - Create Revision", False, 
                                      f"is_issued should be reset to false, but got: {revision_data.get('is_issued')}")
                        return False
                else:
                    self.log_result("Step 4 - Create Revision", False, 
                                  f"has_pending_revision should be true, but got: {revision_data.get('has_pending_revision')}")
                    return False
            else:
                self.log_result("Step 4 - Create Revision", False, 
                              f"Failed to create revision: {revision_response.status_code} - {revision_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 4 - Create Revision", False, f"Exception: {str(e)}")
            return False

        # Step 5: Resolve Revision (THE KEY TEST)
        try:
            print("Step 5: Resolve Revision (THE KEY TEST)...")
            
            # Get current revision count before resolving
            current_revision_count = revision_data.get('revision_count', 0)
            
            resolve_payload = {
                "has_pending_revision": False
            }
            
            resolve_response = self.session.put(f"{BACKEND_URL}/drawings/{drawing_id}", 
                                              json=resolve_payload, headers=owner_headers)
            
            if resolve_response.status_code == 200:
                resolved_data = resolve_response.json()
                
                # Check response for required fields
                checks = []
                
                # has_pending_revision = false
                if resolved_data.get('has_pending_revision') == False:
                    checks.append("✅ has_pending_revision = false")
                else:
                    checks.append(f"❌ has_pending_revision = {resolved_data.get('has_pending_revision')} (expected false)")
                
                # revision_count incremented
                new_revision_count = resolved_data.get('revision_count', 0)
                if new_revision_count > current_revision_count:
                    checks.append(f"✅ revision_count incremented from {current_revision_count} to {new_revision_count}")
                else:
                    checks.append(f"❌ revision_count not incremented: {current_revision_count} -> {new_revision_count}")
                
                # Check is_issued state
                is_issued_state = resolved_data.get('is_issued')
                checks.append(f"ℹ️  is_issued state: {is_issued_state}")
                
                # Check if response includes updated drawing data
                required_fields = ['id', 'name', 'has_pending_revision', 'revision_count', 'is_issued']
                missing_fields = [field for field in required_fields if field not in resolved_data]
                
                if not missing_fields:
                    checks.append("✅ Response includes all required drawing data")
                else:
                    checks.append(f"❌ Missing fields in response: {missing_fields}")
                
                # Determine overall success
                failed_checks = [check for check in checks if check.startswith("❌")]
                
                if not failed_checks:
                    self.log_result("Step 5 - Resolve Revision (KEY TEST)", True, 
                                  f"Revision resolved successfully. Checks: {'; '.join(checks)}")
                else:
                    self.log_result("Step 5 - Resolve Revision (KEY TEST)", False, 
                                  f"Revision resolution failed. Checks: {'; '.join(checks)}")
                    return False
                    
                self.resolved_drawing = resolved_data
                
            else:
                self.log_result("Step 5 - Resolve Revision (KEY TEST)", False, 
                              f"Failed to resolve revision: {resolve_response.status_code} - {resolve_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 5 - Resolve Revision (KEY TEST)", False, f"Exception: {str(e)}")
            return False

        # Step 6: Verify Data Persistence
        try:
            print("Step 6: Verify data persistence...")
            
            # GET the drawing again to verify it persisted
            get_drawing_response = self.session.get(f"{BACKEND_URL}/projects/{self.test_project['id']}/drawings", 
                                                  headers=owner_headers)
            
            if get_drawing_response.status_code == 200:
                drawings_list = get_drawing_response.json()
                
                # Find our test drawing
                persisted_drawing = None
                for drawing in drawings_list:
                    if drawing.get('id') == drawing_id:
                        persisted_drawing = drawing
                        break
                
                if persisted_drawing:
                    # Verify persistence
                    persistence_checks = []
                    
                    # Check revision_count is correct
                    if persisted_drawing.get('revision_count') == self.resolved_drawing.get('revision_count'):
                        persistence_checks.append(f"✅ revision_count persisted: {persisted_drawing.get('revision_count')}")
                    else:
                        persistence_checks.append(f"❌ revision_count not persisted: expected {self.resolved_drawing.get('revision_count')}, got {persisted_drawing.get('revision_count')}")
                    
                    # Check has_pending_revision is false
                    if persisted_drawing.get('has_pending_revision') == False:
                        persistence_checks.append("✅ has_pending_revision persisted as false")
                    else:
                        persistence_checks.append(f"❌ has_pending_revision not persisted: {persisted_drawing.get('has_pending_revision')}")
                    
                    # Check for revision history if available
                    if 'revision_history' in persisted_drawing:
                        revision_history = persisted_drawing.get('revision_history', [])
                        if revision_history:
                            persistence_checks.append(f"✅ revision_history available with {len(revision_history)} entries")
                        else:
                            persistence_checks.append("ℹ️  revision_history is empty")
                    else:
                        persistence_checks.append("ℹ️  revision_history field not present")
                    
                    # Determine overall persistence success
                    failed_persistence = [check for check in persistence_checks if check.startswith("❌")]
                    
                    if not failed_persistence:
                        self.log_result("Step 6 - Verify Data Persistence", True, 
                                      f"Data persistence verified. Checks: {'; '.join(persistence_checks)}")
                    else:
                        self.log_result("Step 6 - Verify Data Persistence", False, 
                                      f"Data persistence failed. Checks: {'; '.join(persistence_checks)}")
                        return False
                else:
                    self.log_result("Step 6 - Verify Data Persistence", False, 
                                  "Drawing not found in project drawings list")
                    return False
            else:
                self.log_result("Step 6 - Verify Data Persistence", False, 
                              f"Failed to get project drawings: {get_drawing_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step 6 - Verify Data Persistence", False, f"Exception: {str(e)}")
            return False

        # All steps passed
        print("\n🎉 ALL TESTS PASSED - Drawing Resolve Revision functionality is working correctly!")
        return True

    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Drawing Resolve Revision Tests")
        print("=" * 50)
        
        success = self.test_drawing_resolve_revision_end_to_end()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        if success:
            print("\n✅ CONCLUSION: Drawing resolve revision functionality is working correctly!")
            print("   The backend API properly handles revision resolution and data persistence.")
            print("   If the user reports the 'Resolve' button does nothing, it's likely a frontend issue.")
        else:
            print("\n❌ CONCLUSION: Issues found with drawing resolve revision functionality!")
            print("   Check the failed tests above for specific problems.")
        
        return success

if __name__ == "__main__":
    tester = DrawingRevisionTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)