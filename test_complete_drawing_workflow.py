#!/usr/bin/env python3
"""
Complete Drawing Workflow Testing - All 5 States
Tests the entire drawing workflow from upload to issue with all state transitions
"""

import requests
import json
import sys
import io
from datetime import datetime
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://buildtracker-10.preview.emergentagent.com/api"

class CompleteDrawingWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.owner_token = None
        self.project_id = None
        self.drawing_id = None
        
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

    def verify_drawing_state(self, drawing, expected_state, state_name):
        """Verify drawing matches expected state"""
        checks = []
        
        # Debug: Print actual drawing state
        print(f"   DEBUG - Actual drawing state:")
        print(f"     file_url: {drawing.get('file_url')}")
        print(f"     under_review: {drawing.get('under_review')}")
        print(f"     is_approved: {drawing.get('is_approved')}")
        print(f"     is_issued: {drawing.get('is_issued')}")
        print(f"     has_pending_revision: {drawing.get('has_pending_revision')}")
        
        # Check file_url
        if expected_state.get('file_url') is None:
            checks.append((drawing.get('file_url') is None, f"file_url should be null"))
        elif expected_state.get('file_url') == 'not_null':
            checks.append((drawing.get('file_url') is not None, f"file_url should be set"))
        else:
            checks.append((drawing.get('file_url') == expected_state.get('file_url'), f"file_url should match"))
            
        # Check other fields only if they are specified in expected_state
        if 'under_review' in expected_state:
            checks.append((drawing.get('under_review') == expected_state.get('under_review'), 
                          f"under_review should be {expected_state.get('under_review')}"))
        if 'is_approved' in expected_state:
            checks.append((drawing.get('is_approved') == expected_state.get('is_approved'), 
                          f"is_approved should be {expected_state.get('is_approved')}"))
        if 'is_issued' in expected_state:
            checks.append((drawing.get('is_issued') == expected_state.get('is_issued'), 
                          f"is_issued should be {expected_state.get('is_issued')}"))
        if 'has_pending_revision' in expected_state:
            checks.append((drawing.get('has_pending_revision') == expected_state.get('has_pending_revision'), 
                          f"has_pending_revision should be {expected_state.get('has_pending_revision')}"))
        
        failed_checks = [msg for check, msg in checks if not check]
        
        if not failed_checks:
            self.log_result(f"Verify {state_name}", True, 
                          f"Drawing correctly in {state_name} state")
            return True
        else:
            self.log_result(f"Verify {state_name}", False, 
                          f"State verification failed: {'; '.join(failed_checks)}")
            return False

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        # Create a minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Drawing) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        return io.BytesIO(pdf_content)

    def test_owner_login(self):
        """Step 1: Login as owner"""
        try:
            print("🔐 Step 1: Login as owner (owner@test.com / testpassword)")
            
            credentials = {
                "email": "owner@test.com",
                "password": "testpassword"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=credentials)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("user", {}).get("is_owner") == True:
                    self.owner_token = data["access_token"]
                    self.log_result("Owner Login", True, 
                                  "Owner successfully authenticated")
                    return True
                else:
                    self.log_result("Owner Login", False, 
                                  "User is not marked as owner")
                    return False
            else:
                self.log_result("Owner Login", False, 
                              f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Owner Login", False, f"Exception: {str(e)}")
            return False

    def test_create_new_drawing(self):
        """Step 2: Create New Drawing via POST /api/projects/{project_id}/drawings"""
        if not self.owner_token:
            self.log_result("Create New Drawing", False, "No owner token available")
            return False
            
        try:
            print("📝 Step 2: Create New Drawing")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # First, get a project to use
            projects_response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                
                if len(projects) > 0:
                    self.project_id = projects[0]["id"]
                    project_name = projects[0].get("title", "Unknown")
                    print(f"   Using existing project: {project_name}")
                else:
                    # Create a test project
                    project_data = {
                        "code": f"TEST-WORKFLOW-{uuid.uuid4().hex[:8]}",
                        "title": "Complete Workflow Test Project",
                        "project_types": ["Architecture"],
                        "status": "active",
                        "site_address": "Test Workflow Address"
                    }
                    
                    create_response = self.session.post(f"{BACKEND_URL}/projects", 
                                                      json=project_data, headers=headers)
                    
                    if create_response.status_code == 200:
                        project = create_response.json()
                        self.project_id = project["id"]
                        print(f"   Created new project: {project.get('title')}")
                    else:
                        self.log_result("Create New Drawing", False, 
                                      f"Failed to create project: {create_response.status_code}")
                        return False
            else:
                self.log_result("Create New Drawing", False, 
                              f"Failed to get projects: {projects_response.status_code}")
                return False
            
            # Now create the drawing
            drawing_data = {
                "project_id": self.project_id,  # Required by ProjectDrawingCreate model
                "category": "Architecture",
                "name": f"Complete Workflow Test Drawing {datetime.now().strftime('%H%M%S')}",
                "due_date": "2024-12-31",
                "notes": "Test drawing for complete workflow testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/projects/{self.project_id}/drawings", 
                                       json=drawing_data, headers=headers)
            
            if response.status_code == 200:
                drawing = response.json()
                self.drawing_id = drawing["id"]
                
                # Verify initial state (STATE 1: Pending)
                expected_state_1 = {
                    'file_url': None,
                    'under_review': False,
                    'is_approved': False,
                    'is_issued': False,
                    'has_pending_revision': False
                }
                
                if self.verify_drawing_state(drawing, expected_state_1, "STATE 1: Pending (no file)"):
                    self.log_result("Create New Drawing", True, 
                                  f"Drawing created successfully. ID: {self.drawing_id}")
                    return True
                else:
                    return False
            else:
                self.log_result("Create New Drawing", False, 
                              f"Failed to create drawing: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create New Drawing", False, f"Exception: {str(e)}")
            return False

    def test_upload_pdf_and_transition_to_under_review(self):
        """Step 3: Upload PDF and set file_url (STATE 2)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Upload PDF - Set File URL", False, "Missing prerequisites")
            return False
            
        try:
            print("📤 Step 3: Upload PDF and set file_url (STATE 2)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create test PDF file
            pdf_file = self.create_test_pdf()
            
            # Upload file
            files = {
                'file': ('test_drawing.pdf', pdf_file, 'application/pdf')
            }
            data = {
                'drawing_id': self.drawing_id,
                'upload_type': 'issue'
            }
            
            upload_response = self.session.post(f"{BACKEND_URL}/drawings/upload", 
                                              files=files, data=data, headers=headers)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                file_url = upload_data.get("file_url")
                
                print(f"   File uploaded successfully: {file_url}")
                
                # Update drawing with file_url (this represents the "under review" state)
                update_data = {
                    "file_url": file_url
                }
                
                update_response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                                 json=update_data, headers=headers)
                
                if update_response.status_code == 200:
                    updated_drawing = update_response.json()
                    
                    # Verify STATE 2: Has file (ready for review/approval)
                    expected_state_2 = {
                        'file_url': 'not_null',
                        'is_issued': False,
                        'has_pending_revision': False
                    }
                    
                    return self.verify_drawing_state(updated_drawing, expected_state_2, 
                                                   "STATE 2: Has File (ready for review)")
                else:
                    self.log_result("Upload PDF - Set File URL", False, 
                                  f"Failed to update drawing: {update_response.status_code}")
                    return False
            else:
                self.log_result("Upload PDF - Set File URL", False, 
                              f"Failed to upload file: {upload_response.status_code} - {upload_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Upload PDF - Set File URL", False, f"Exception: {str(e)}")
            return False

    def test_request_revision(self):
        """Step 4: Request Revision (STATE 3)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Request Revision", False, "Missing prerequisites")
            return False
            
        try:
            print("🔄 Step 4: Request Revision (STATE 3)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Request revision
            revision_data = {
                "has_pending_revision": True,
                "revision_notes": "Please update the dimensions and add more details to the floor plan",
                "revision_due_date": "2024-12-20"
            }
            
            response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                      json=revision_data, headers=headers)
            
            if response.status_code == 200:
                updated_drawing = response.json()
                
                # Verify STATE 3: Revision Pending
                expected_state_3 = {
                    'file_url': 'not_null',  # Should still have file
                    'is_issued': False,
                    'has_pending_revision': True
                }
                
                return self.verify_drawing_state(updated_drawing, expected_state_3, 
                                               "STATE 3: Revision Pending (after REVISE)")
            else:
                self.log_result("Request Revision", False, 
                              f"Failed to request revision: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Request Revision", False, f"Exception: {str(e)}")
            return False

    def test_resolve_revision_with_new_file(self):
        """Step 5: Resolve Revision with new file (STATE 2b)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Resolve Revision", False, "Missing prerequisites")
            return False
            
        try:
            print("✅ Step 5: Resolve Revision with new file (STATE 2b)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Upload revised file
            pdf_file = self.create_test_pdf()
            
            files = {
                'file': ('revised_drawing.pdf', pdf_file, 'application/pdf')
            }
            data = {
                'drawing_id': self.drawing_id,
                'upload_type': 'revision'
            }
            
            upload_response = self.session.post(f"{BACKEND_URL}/drawings/upload", 
                                              files=files, data=data, headers=headers)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                new_file_url = upload_data.get("file_url")
                
                print(f"   Revised file uploaded: {new_file_url}")
                
                # Resolve revision
                resolve_data = {
                    "under_review": True,
                    "file_url": new_file_url,
                    "has_pending_revision": False
                }
                
                resolve_response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                                  json=resolve_data, headers=headers)
                
                if resolve_response.status_code == 200:
                    updated_drawing = resolve_response.json()
                    
                    # Verify STATE 2b: Resolved (after RESOLVE with new file)
                    expected_state_2b = {
                        'file_url': 'not_null',  # Should have updated file
                        'is_issued': False,
                        'has_pending_revision': False
                    }
                    
                    return self.verify_drawing_state(updated_drawing, expected_state_2b, 
                                                   "STATE 2b: Resolved (after RESOLVE with new file)")
                else:
                    self.log_result("Resolve Revision", False, 
                                  f"Failed to resolve revision: {resolve_response.status_code}")
                    return False
            else:
                self.log_result("Resolve Revision", False, 
                              f"Failed to upload revised file: {upload_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Resolve Revision", False, f"Exception: {str(e)}")
            return False

    def test_issue_drawing_directly(self):
        """Step 6: Issue Drawing directly (STATE 4)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Issue Drawing", False, "Missing prerequisites")
            return False
            
        try:
            print("🚀 Step 6: Issue Drawing (STATE 4)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Issue drawing directly (this is the main workflow)
            issue_data = {
                "is_issued": True
            }
            
            response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                      json=issue_data, headers=headers)
            
            if response.status_code == 200:
                updated_drawing = response.json()
                
                # Verify STATE 4: Issued
                expected_state_4 = {
                    'file_url': 'not_null',  # Should still have file
                    'is_issued': True,
                    'has_pending_revision': False
                }
                
                return self.verify_drawing_state(updated_drawing, expected_state_4, 
                                               "STATE 4: Issued")
            else:
                self.log_result("Issue Drawing", False, 
                              f"Failed to issue drawing: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Issue Drawing", False, f"Exception: {str(e)}")
            return False

    def test_request_revision_from_issued(self):
        """Step 7: Request Revision from Issued state (STATE 5)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Request Revision from Issued", False, "Missing prerequisites")
            return False
            
        try:
            print("🔄 Step 7: Request Revision from Issued state (STATE 5)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Request revision from issued drawing
            revision_data = {
                "has_pending_revision": True,
                "revision_notes": "Please update the issued drawing with new specifications",
                "revision_due_date": "2024-12-25"
            }
            
            response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                      json=revision_data, headers=headers)
            
            if response.status_code == 200:
                updated_drawing = response.json()
                
                # Verify STATE 5: Revision Pending (from issued)
                expected_state_5 = {
                    'file_url': 'not_null',  # Should still have file
                    'is_issued': False,  # Should be reset when revision requested
                    'has_pending_revision': True
                }
                
                return self.verify_drawing_state(updated_drawing, expected_state_5, 
                                               "STATE 5: Revision Pending (from issued)")
            else:
                self.log_result("Request Revision from Issued", False, 
                              f"Failed to request revision: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Request Revision from Issued", False, f"Exception: {str(e)}")
            return False

    def test_resolve_and_issue_then_unissue(self):
        """Step 8: Resolve revision, Issue, then Un-Issue Drawing (back to STATE 1)"""
        if not self.owner_token or not self.drawing_id:
            self.log_result("Resolve Issue Un-Issue", False, "Missing prerequisites")
            return False
            
        try:
            print("🔙 Step 8: Resolve revision, Issue, then Un-Issue Drawing (back to STATE 1)")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # First resolve the pending revision
            print("   8a: Resolving pending revision...")
            resolve_data = {
                "has_pending_revision": False
            }
            
            resolve_response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                              json=resolve_data, headers=headers)
            
            if resolve_response.status_code != 200:
                self.log_result("Resolve Issue Un-Issue", False, 
                              f"Failed to resolve revision: {resolve_response.status_code}")
                return False
            
            # Then issue the drawing
            print("   8b: Issuing drawing...")
            issue_data = {
                "is_issued": True
            }
            
            issue_response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                            json=issue_data, headers=headers)
            
            if issue_response.status_code != 200:
                self.log_result("Resolve Issue Un-Issue", False, 
                              f"Failed to issue drawing: {issue_response.status_code}")
                return False
            
            # Finally un-issue drawing (should reset everything)
            print("   8c: Un-issuing drawing...")
            unissue_data = {
                "is_issued": False
            }
            
            unissue_response = self.session.put(f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                                              json=unissue_data, headers=headers)
            
            if unissue_response.status_code == 200:
                updated_drawing = unissue_response.json()
                
                # Verify STATE 1: Pending (after UN-ISSUE)
                # According to the backend logic, un-issue should clear everything back to pending
                expected_state_1_final = {
                    'file_url': None,  # Should be cleared
                    'is_issued': False,
                    'has_pending_revision': False
                }
                
                return self.verify_drawing_state(updated_drawing, expected_state_1_final, 
                                               "STATE 1: Pending (after UN-ISSUE)")
            else:
                self.log_result("Resolve Issue Un-Issue", False, 
                              f"Failed to un-issue drawing: {unissue_response.status_code} - {unissue_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Resolve Issue Un-Issue", False, f"Exception: {str(e)}")
            return False

    def run_complete_workflow_test(self):
        """Run the complete drawing workflow test"""
        print("🎯 COMPLETE DRAWING WORKFLOW TEST - ALL 5 STATES")
        print("=" * 70)
        print("Testing complete workflow: Pending → Upload → Has File → Revision → Resolve → Issue → Revision from Issued → Un-Issue")
        print()
        
        # Run all test steps in sequence
        steps = [
            self.test_owner_login,
            self.test_create_new_drawing,
            self.test_upload_pdf_and_transition_to_under_review,
            self.test_request_revision,
            self.test_resolve_revision_with_new_file,
            self.test_issue_drawing_directly,
            self.test_request_revision_from_issued,
            self.test_resolve_and_issue_then_unissue
        ]
        
        all_passed = True
        
        for step in steps:
            if not step():
                all_passed = False
                print(f"❌ Workflow stopped at step: {step.__name__}")
                break
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 COMPLETE WORKFLOW TEST SUMMARY")
        print("=" * 70)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if all_passed:
            print("\n🎉 COMPLETE DRAWING WORKFLOW TEST PASSED!")
            print("All 5 states and transitions working correctly:")
            print("✅ STATE 1: Pending (no file)")
            print("✅ STATE 2: Under Review (after upload)")
            print("✅ STATE 3: Revision Pending (after REVISE)")
            print("✅ STATE 2b: Under Review (after RESOLVE with new file)")
            print("✅ STATE 4: Approved (after APPROVE)")
            print("✅ STATE 5: Issued (after ISSUE)")
            print("✅ STATE 1: Pending (after UN-ISSUE)")
        else:
            print("\n❌ COMPLETE DRAWING WORKFLOW TEST FAILED!")
            print("Some state transitions are not working correctly.")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result["success"]]
            if failed_tests:
                print("\nFailed Tests:")
                for test in failed_tests:
                    print(f"  ❌ {test['test']}: {test['details']}")
        
        return all_passed

def main():
    """Main function to run the complete drawing workflow test"""
    tester = CompleteDrawingWorkflowTester()
    success = tester.run_complete_workflow_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()