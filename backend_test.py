#!/usr/bin/env python3
"""
Backend API Testing Script for Architecture Firm Management System
Testing Refactored Backend API Endpoints after modular router migration:

**Context:**
Major backend refactoring where ~860 lines were removed from server.py.
Routes migrated to modular routers:
1. Comments routes → /app/backend/routes/comments.py
2. External parties (contractors, vendors, consultants) → /app/backend/routes/external_parties.py

**Tests to perform:**
1. Authentication Tests (Owner & Team Leader)
2. Comments API Tests (Project & Drawing comments)
3. Contractors API Tests
4. Vendors API Tests  
5. Consultants API Tests
6. General Health Check
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

    def test_comments_api(self):
        """Test Comments API endpoints (from comments.py router)"""
        if not self.team_leader_token or not self.project_id:
            self.log_result("Comments API Test", False, "Missing token or project ID")
            return
            
        try:
            print("💬 Testing Comments API...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test 1: GET project comments
            response = self.session.get(f"{BACKEND_URL}/projects/{self.project_id}/comments", headers=headers)
            
            if response.status_code == 200:
                comments = response.json()
                self.log_result("GET Project Comments", True, f"Retrieved {len(comments)} project comments")
            else:
                self.log_result("GET Project Comments", False, f"Failed: {response.status_code} - {response.text}")
                return
            
            # Test 2: POST project comment
            comment_data = {
                "text": f"Test comment from backend test - {datetime.now().isoformat()}"
            }
            
            # Use form data for project comments
            response = self.session.post(
                f"{BACKEND_URL}/projects/{self.project_id}/comments", 
                headers=headers,
                data=comment_data
            )
            
            if response.status_code == 200:
                comment_response = response.json()
                self.test_comment_id = comment_response.get("comment", {}).get("id")
                self.log_result("POST Project Comment", True, "Successfully created project comment")
            else:
                self.log_result("POST Project Comment", False, f"Failed: {response.status_code} - {response.text}")
            
            # Test 3: GET drawing comments (if drawing exists)
            if self.drawing_id:
                response = self.session.get(f"{BACKEND_URL}/drawings/{self.drawing_id}/comments", headers=headers)
                
                if response.status_code == 200:
                    drawing_comments = response.json()
                    self.log_result("GET Drawing Comments", True, f"Retrieved {len(drawing_comments)} drawing comments")
                else:
                    self.log_result("GET Drawing Comments", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Comments API Test", False, f"Exception: {str(e)}")

    def test_contractors_api(self):
        """Test Contractors API endpoints (from external_parties.py router)"""
        if not self.team_leader_token:
            self.log_result("Contractors API Test", False, "Missing token")
            return
            
        try:
            print("🔨 Testing Contractors API...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test 1: GET contractors
            response = self.session.get(f"{BACKEND_URL}/contractors", headers=headers)
            
            if response.status_code == 200:
                contractors = response.json()
                self.log_result("GET Contractors", True, f"Retrieved {len(contractors)} contractors")
            else:
                self.log_result("GET Contractors", False, f"Failed: {response.status_code} - {response.text}")
            
            # Test 2: GET contractor types
            response = self.session.get(f"{BACKEND_URL}/contractor-types", headers=headers)
            
            if response.status_code == 200:
                contractor_types = response.json()
                self.log_result("GET Contractor Types", True, f"Retrieved {len(contractor_types)} contractor types")
            else:
                self.log_result("GET Contractor Types", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Contractors API Test", False, f"Exception: {str(e)}")

    def test_vendors_api(self):
        """Test Vendors API endpoints (from external_parties.py router)"""
        if not self.team_leader_token:
            self.log_result("Vendors API Test", False, "Missing token")
            return
            
        try:
            print("🏪 Testing Vendors API...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test 1: GET vendors
            response = self.session.get(f"{BACKEND_URL}/vendors", headers=headers)
            
            if response.status_code == 200:
                vendors = response.json()
                self.log_result("GET Vendors", True, f"Retrieved {len(vendors)} vendors")
            else:
                self.log_result("GET Vendors", False, f"Failed: {response.status_code} - {response.text}")
            
            # Test 2: GET vendor types
            response = self.session.get(f"{BACKEND_URL}/vendor-types", headers=headers)
            
            if response.status_code == 200:
                vendor_types = response.json()
                self.log_result("GET Vendor Types", True, f"Retrieved {len(vendor_types)} vendor types")
            else:
                self.log_result("GET Vendor Types", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Vendors API Test", False, f"Exception: {str(e)}")

    def test_consultants_api(self):
        """Test Consultants API endpoints (from external_parties.py router)"""
        if not self.team_leader_token:
            self.log_result("Consultants API Test", False, "Missing token")
            return
            
        try:
            print("👨‍💼 Testing Consultants API...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test 1: GET consultants
            response = self.session.get(f"{BACKEND_URL}/consultants", headers=headers)
            
            if response.status_code == 200:
                consultants = response.json()
                self.log_result("GET Consultants", True, f"Retrieved {len(consultants)} consultants")
            else:
                self.log_result("GET Consultants", False, f"Failed: {response.status_code} - {response.text}")
            
            # Test 2: GET consultant types
            response = self.session.get(f"{BACKEND_URL}/consultant-types", headers=headers)
            
            if response.status_code == 200:
                consultant_types = response.json()
                self.log_result("GET Consultant Types", True, f"Retrieved {len(consultant_types)} consultant types")
            else:
                self.log_result("GET Consultant Types", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Consultants API Test", False, f"Exception: {str(e)}")

    def run_drawing_notification_tests(self):
        """Run all drawing notification tests in sequence"""
        print("🚀 Starting Drawing Notification System Tests")
        print("=" * 60)
        
        # Authentication tests
        self.test_team_leader_login()
        self.test_owner_login()
        
        # Get test data
        self.get_project_and_drawing()
        
        # Template service tests
        self.test_template_service_availability()
        
        # Drawing notification tests
        if self.drawing_id:
            print(f"\n📋 Testing with Drawing: {self.drawing_name} (ID: {self.drawing_id})")
            print(f"📁 Project ID: {self.project_id}")
            print()
            
            # Test drawing upload notification
            upload_success = self.test_drawing_upload_notification()
            
            # Test drawing issued notification
            if upload_success:
                # Wait a bit between tests
                time.sleep(1)
                self.test_drawing_issued_notification()
        
        # Check logs
        self.test_notification_logs()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DRAWING NOTIFICATION TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED - Drawing notification system working correctly")
        
        print(f"\n📝 NEXT STEPS:")
        print(f"1. Check backend logs with: tail -50 /var/log/supervisor/backend.err.log | grep -i 'notification\\|whatsapp\\|template\\|email'")
        print(f"2. Look for 'WhatsApp template sent', 'Email sent', 'In-app notification created' messages")
        print(f"3. Verify templates are being used (not freeform messages)")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_drawing_notification_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)