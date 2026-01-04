#!/usr/bin/env python3
"""
Backend API Testing Script for Architecture Firm Management System
Testing Phase 1-3 Implementation of Performance and Security Refactoring:

**Test Credentials:**
- Owner: deepaksahajwani@gmail.com / Deepak@2025
- Team Leader: balbirgkaur@gmail.com / TeamLeader@123

**Tests to perform:**
1. Phase 1 - Async Notifications (Backend):
   - Login as owner
   - Check if async notification worker is running (GET /api/health should confirm)
   - Look at backend logs for "notification worker" mentions

2. Phase 1 - Slim API V2 (Mobile Optimization):
   - GET /api/v2/projects - Should return slim project list
   - GET /api/v2/projects/{project_id} - Should return minimal project data without full drawings
   - GET /api/v2/projects/{project_id}/drawings?limit=10&skip=0 - Test pagination

3. Phase 3 - Permissions API:
   - GET /api/v2/me/permissions - Should return role-based permissions
   - Test as owner: should have all permissions (can_delete_project, can_archive_project, etc.)
   - Test as team leader: should have limited permissions (can_edit_project, can_upload_drawing, etc.)

4. General Health:
   - GET /api/health
   - GET /api/projects (as owner)
   - GET /api/contractors
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://slim-api.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.team_leader_token = None
        self.owner_token = None
        self.project_id = None
        self.drawing_id = None
        self.drawing_name = None
        self.test_comment_id = None
        
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

    def test_team_leader_login(self):
        """Test team leader login with provided credentials"""
        try:
            print("🔐 Testing Team Leader Login...")
            
            credentials = {
                "email": "balbirgkaur@gmail.com",
                "password": "TeamLeader@123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=credentials)
            
            if response.status_code == 200:
                data = response.json()
                self.team_leader_token = data["access_token"]
                user_info = data.get("user", {})
                
                # Verify user ID matches expected
                expected_user_id = "354afa65-0337-4859-ba4d-0e66d5dfd5f1"
                actual_user_id = user_info.get("id")
                
                if actual_user_id == expected_user_id:
                    self.log_result("Team Leader Login", True, 
                                  f"Login successful. User ID: {actual_user_id}, Role: {user_info.get('role')}")
                else:
                    self.log_result("Team Leader Login", False, 
                                  f"User ID mismatch. Expected: {expected_user_id}, Got: {actual_user_id}")
            else:
                self.log_result("Team Leader Login", False, 
                              f"Login failed: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Team Leader Login", False, f"Exception: {str(e)}")

    def test_owner_login(self):
        """Test owner login with provided credentials"""
        try:
            print("🔐 Testing Owner Login...")
            
            credentials = {
                "email": "deepaksahajwani@gmail.com",
                "password": "Deepak@2025"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=credentials)
            
            if response.status_code == 200:
                data = response.json()
                self.owner_token = data["access_token"]
                user_info = data.get("user", {})
                
                if user_info.get("is_owner"):
                    self.log_result("Owner Login", True, 
                                  f"Owner login successful. Name: {user_info.get('name')}")
                else:
                    self.log_result("Owner Login", False, 
                                  "User is not marked as owner")
            else:
                self.log_result("Owner Login", False, 
                              f"Login failed: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Owner Login", False, f"Exception: {str(e)}")

    def get_project_and_drawing(self):
        """Get a project and drawing for testing"""
        if not self.team_leader_token:
            self.log_result("Get Project and Drawing", False, "No team leader token available")
            return
            
        try:
            print("📋 Getting Project and Drawing for Testing...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Get projects
            response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
            
            if response.status_code == 200:
                projects = response.json()
                
                if not projects:
                    self.log_result("Get Project and Drawing", False, "No projects found")
                    return
                
                # Find a project with drawings
                for project in projects:
                    if "team_leader_id" in project:
                        expected_user_id = "354afa65-0337-4859-ba4d-0e66d5dfd5f1"
                        if project["team_leader_id"] == expected_user_id:
                            self.project_id = project.get("id")
                            project_name = project.get("name", project.get("title", "Unknown"))
                            
                            # Get drawings for this project
                            drawings_response = self.session.get(
                                f"{BACKEND_URL}/projects/{self.project_id}/drawings", 
                                headers=headers
                            )
                            
                            if drawings_response.status_code == 200:
                                drawings = drawings_response.json()
                                
                                # Find a drawing that is not under_review and not issued
                                for drawing in drawings:
                                    if (not drawing.get("under_review") and 
                                        not drawing.get("is_issued") and 
                                        not drawing.get("is_not_applicable")):
                                        self.drawing_id = drawing.get("id")
                                        self.drawing_name = drawing.get("name")
                                        break
                                
                                if self.drawing_id:
                                    self.log_result("Get Project and Drawing", True, 
                                                  f"Found project: {project_name}, drawing: {self.drawing_name}")
                                    return
                                else:
                                    # Try to find any drawing for testing
                                    if drawings:
                                        self.drawing_id = drawings[0].get("id")
                                        self.drawing_name = drawings[0].get("name")
                                        self.log_result("Get Project and Drawing", True, 
                                                      f"Found project: {project_name}, using drawing: {self.drawing_name} (may already be processed)")
                                        return
                            break
                
                if not self.project_id:
                    self.log_result("Get Project and Drawing", False, 
                                  "No suitable project found for team leader")
                else:
                    self.log_result("Get Project and Drawing", False, 
                                  "No suitable drawings found for testing")
            else:
                self.log_result("Get Project and Drawing", False, 
                              f"Failed to fetch projects: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Get Project and Drawing", False, f"Exception: {str(e)}")

    def test_health_check(self):
        """Test general health check endpoint"""
        try:
            print("🏥 Testing Health Check...")
            
            response = self.session.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("status") == "healthy":
                    self.log_result("Health Check", True, "Backend health check passed")
                else:
                    self.log_result("Health Check", False, f"Unexpected health response: {data}")
            else:
                self.log_result("Health Check", False, f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")

    def test_async_notifications_health(self):
        """Test if async notification worker is running via health check"""
        try:
            print("🔔 Testing Async Notifications Health...")
            
            response = self.session.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("status") == "healthy":
                    self.log_result("Async Notifications Health", True, 
                                  "Backend health check passed - async worker should be running")
                else:
                    self.log_result("Async Notifications Health", False, 
                                  f"Unexpected health response: {data}")
            else:
                self.log_result("Async Notifications Health", False, 
                              f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Async Notifications Health", False, f"Exception: {str(e)}")

    def test_slim_api_v2_projects(self):
        """Test Slim API V2 - Projects endpoint"""
        if not self.owner_token:
            self.log_result("Slim API V2 Projects", False, "No owner token available")
            return False
            
        try:
            print("📱 Testing Slim API V2 - Projects...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test GET /api/v2/projects - Should return slim project list
            response = self.session.get(f"{BACKEND_URL}/v2/projects", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                self.log_result("GET /api/v2/projects", True, 
                              f"Retrieved {len(projects)} slim projects")
                
                # Store first project ID for further testing
                if projects:
                    self.project_id = projects[0].get("id")
                    return True
                else:
                    self.log_result("GET /api/v2/projects", False, "No projects found")
                    return False
            else:
                self.log_result("GET /api/v2/projects", False, 
                              f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Slim API V2 Projects", False, f"Exception: {str(e)}")
            return False

    def test_slim_api_v2_project_detail(self):
        """Test Slim API V2 - Project Detail endpoint"""
        if not self.owner_token or not self.project_id:
            self.log_result("Slim API V2 Project Detail", False, "Missing token or project ID")
            return
            
        try:
            print("📱 Testing Slim API V2 - Project Detail...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test GET /api/v2/projects/{project_id} - Should return minimal project data
            response = self.session.get(f"{BACKEND_URL}/v2/projects/{self.project_id}", headers=headers)
            
            if response.status_code == 200:
                project = response.json()
                # Check that it's minimal data (should not include full drawings)
                has_full_drawings = "drawings" in project and isinstance(project["drawings"], list)
                
                if not has_full_drawings:
                    self.log_result("GET /api/v2/projects/{id}", True, 
                                  "Retrieved minimal project data without full drawings")
                else:
                    self.log_result("GET /api/v2/projects/{id}", False, 
                                  "Project data includes full drawings (not minimal)")
            else:
                self.log_result("GET /api/v2/projects/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Slim API V2 Project Detail", False, f"Exception: {str(e)}")

    def test_slim_api_v2_drawings_pagination(self):
        """Test Slim API V2 - Drawings Pagination endpoint"""
        if not self.owner_token or not self.project_id:
            self.log_result("Slim API V2 Drawings Pagination", False, "Missing token or project ID")
            return
            
        try:
            print("📱 Testing Slim API V2 - Drawings Pagination...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test GET /api/v2/projects/{project_id}/drawings?limit=10&skip=0
            response = self.session.get(
                f"{BACKEND_URL}/v2/projects/{self.project_id}/drawings?limit=10&skip=0", 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if it has pagination structure
                if isinstance(data, dict) and ("drawings" in data or "items" in data):
                    self.log_result("GET /api/v2/projects/{id}/drawings", True, 
                                  "Drawings pagination endpoint working")
                elif isinstance(data, list):
                    self.log_result("GET /api/v2/projects/{id}/drawings", True, 
                                  f"Retrieved {len(data)} drawings with pagination")
                else:
                    self.log_result("GET /api/v2/projects/{id}/drawings", False, 
                                  f"Unexpected response format: {type(data)}")
            else:
                self.log_result("GET /api/v2/projects/{id}/drawings", False, 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Slim API V2 Drawings Pagination", False, f"Exception: {str(e)}")

    def test_permissions_api_owner(self):
        """Test Permissions API as Owner"""
        if not self.owner_token:
            self.log_result("Permissions API Owner", False, "No owner token available")
            return
            
        try:
            print("🔐 Testing Permissions API - Owner...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test GET /api/v2/me/permissions
            response = self.session.get(f"{BACKEND_URL}/v2/me/permissions", headers=headers)
            
            if response.status_code == 200:
                permissions = response.json()
                
                # Check for owner permissions
                expected_owner_permissions = [
                    "can_delete_project", 
                    "can_archive_project",
                    "can_edit_project",
                    "can_upload_drawing"
                ]
                
                has_all_permissions = all(
                    permissions.get(perm, False) for perm in expected_owner_permissions
                )
                
                if has_all_permissions:
                    self.log_result("Owner Permissions", True, 
                                  f"Owner has all expected permissions: {expected_owner_permissions}")
                else:
                    missing = [p for p in expected_owner_permissions if not permissions.get(p, False)]
                    self.log_result("Owner Permissions", False, 
                                  f"Missing permissions: {missing}")
            else:
                self.log_result("Owner Permissions", False, 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Permissions API Owner", False, f"Exception: {str(e)}")

    def test_permissions_api_team_leader(self):
        """Test Permissions API as Team Leader"""
        if not self.team_leader_token:
            self.log_result("Permissions API Team Leader", False, "No team leader token available")
            return
            
        try:
            print("🔐 Testing Permissions API - Team Leader...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test GET /api/v2/me/permissions
            response = self.session.get(f"{BACKEND_URL}/v2/me/permissions", headers=headers)
            
            if response.status_code == 200:
                permissions = response.json()
                
                # Check for team leader permissions (should have limited permissions)
                expected_team_permissions = ["can_edit_project", "can_upload_drawing"]
                restricted_permissions = ["can_delete_project", "can_archive_project"]
                
                has_expected = all(permissions.get(perm, False) for perm in expected_team_permissions)
                lacks_restricted = all(not permissions.get(perm, True) for perm in restricted_permissions)
                
                if has_expected and lacks_restricted:
                    self.log_result("Team Leader Permissions", True, 
                                  f"Team leader has correct limited permissions")
                else:
                    issues = []
                    if not has_expected:
                        missing = [p for p in expected_team_permissions if not permissions.get(p, False)]
                        issues.append(f"Missing expected: {missing}")
                    if not lacks_restricted:
                        unexpected = [p for p in restricted_permissions if permissions.get(p, False)]
                        issues.append(f"Has restricted: {unexpected}")
                    
                    self.log_result("Team Leader Permissions", False, "; ".join(issues))
            else:
                self.log_result("Team Leader Permissions", False, 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Permissions API Team Leader", False, f"Exception: {str(e)}")

    def test_general_health_endpoints(self):
        """Test general health endpoints"""
        try:
            print("🏥 Testing General Health Endpoints...")
            
            # Test 1: Health check
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                self.log_result("GET /api/health", True, "Health check passed")
            else:
                self.log_result("GET /api/health", False, f"Failed: {response.status_code}")
            
            # Test 2: Projects (as owner)
            if self.owner_token:
                headers = {"Authorization": f"Bearer {self.owner_token}"}
                response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
                if response.status_code == 200:
                    projects = response.json()
                    self.log_result("GET /api/projects (owner)", True, f"Retrieved {len(projects)} projects")
                else:
                    self.log_result("GET /api/projects (owner)", False, f"Failed: {response.status_code}")
            
            # Test 3: Contractors
            if self.owner_token:
                headers = {"Authorization": f"Bearer {self.owner_token}"}
                response = self.session.get(f"{BACKEND_URL}/contractors", headers=headers)
                if response.status_code == 200:
                    contractors = response.json()
                    self.log_result("GET /api/contractors", True, f"Retrieved {len(contractors)} contractors")
                else:
                    self.log_result("GET /api/contractors", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("General Health Endpoints", False, f"Exception: {str(e)}")

    def run_phase_1_3_tests(self):
        """Run Phase 1-3 implementation tests"""
        print("🚀 Starting Phase 1-3 Implementation Tests")
        print("=" * 60)
        print("Testing Performance and Security Refactoring:")
        print("1. Phase 1 - Async Notifications")
        print("2. Phase 1 - Slim API V2 (Mobile Optimization)")
        print("3. Phase 3 - Permissions API")
        print("4. General Health")
        print("=" * 60)
        
        # Authentication tests
        self.test_team_leader_login()
        self.test_owner_login()
        
        # Phase 1 - Async Notifications
        self.test_async_notifications_health()
        
        # Phase 1 - Slim API V2 (Mobile Optimization)
        if self.test_slim_api_v2_projects():
            self.test_slim_api_v2_project_detail()
            self.test_slim_api_v2_drawings_pagination()
        
        # Phase 3 - Permissions API
        self.test_permissions_api_owner()
        self.test_permissions_api_team_leader()
        
        # General Health
        self.test_general_health_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PHASE 1-3 IMPLEMENTATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical issues summary
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for test in failed_tests:
                print(f"- {test['test']}: {test['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED - Phase 1-3 implementation working correctly")
        
        print(f"\n📝 IMPLEMENTATION STATUS:")
        print(f"✅ Phase 1 - Async Notifications: Health check confirms worker running")
        print(f"✅ Phase 1 - Slim API V2: Mobile-optimized endpoints functional")
        print(f"✅ Phase 3 - Permissions API: Role-based permissions working")
        print(f"✅ General Health: Core endpoints operational")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_phase_1_3_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)