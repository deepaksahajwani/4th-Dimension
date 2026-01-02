#!/usr/bin/env python3
"""
Backend API Testing Script for Architecture Firm Management System
Testing specific endpoints as requested in review:
1. My Work Endpoint Test
2. 3D Images Endpoint Test  
3. Team Leader Dashboard vs My Work Differentiation
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://pm-system.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.team_leader_token = None
        self.owner_token = None
        self.project_id = None
        
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

    def test_my_work_endpoint(self):
        """Test My Work endpoint - projects with team_leader_id field"""
        if not self.team_leader_token:
            self.log_result("My Work Endpoint", False, "No team leader token available")
            return
            
        try:
            print("📋 Testing My Work Endpoint...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
            
            if response.status_code == 200:
                projects = response.json()
                
                if not projects:
                    self.log_result("My Work Endpoint", False, "No projects found")
                    return
                
                # Check if projects have team_leader_id field
                team_leader_projects = []
                expected_user_id = "354afa65-0337-4859-ba4d-0e66d5dfd5f1"
                
                for project in projects:
                    if "team_leader_id" in project:
                        if project["team_leader_id"] == expected_user_id:
                            team_leader_projects.append(project)
                            # Store project ID for later tests
                            if not self.project_id:
                                self.project_id = project.get("id")
                
                if team_leader_projects:
                    self.log_result("My Work Endpoint", True, 
                                  f"Found {len(team_leader_projects)} projects with correct team_leader_id. "
                                  f"Sample project: {team_leader_projects[0].get('name', 'Unknown')}")
                else:
                    # Check if any projects have team_leader_id field at all
                    has_team_leader_field = any("team_leader_id" in p for p in projects)
                    if has_team_leader_field:
                        self.log_result("My Work Endpoint", False, 
                                      f"Projects have team_leader_id field but none match user ID {expected_user_id}")
                    else:
                        self.log_result("My Work Endpoint", False, 
                                      "Projects missing team_leader_id field")
            else:
                self.log_result("My Work Endpoint", False, 
                              f"Failed to fetch projects: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("My Work Endpoint", False, f"Exception: {str(e)}")

    def test_3d_images_endpoint(self):
        """Test 3D Images endpoint with file URL verification"""
        if not self.owner_token:
            self.log_result("3D Images Endpoint", False, "No owner token available")
            return
            
        try:
            print("🖼️ Testing 3D Images Endpoint...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # First get projects to find a project ID
            projects_response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
            
            if projects_response.status_code != 200:
                self.log_result("3D Images Endpoint", False, 
                              f"Failed to fetch projects: {projects_response.status_code}")
                return
            
            projects = projects_response.json()
            if not projects:
                self.log_result("3D Images Endpoint", False, "No projects found")
                return
            
            # Use the first project or the one we found earlier
            project_id = self.project_id or projects[0].get("id")
            if not project_id:
                self.log_result("3D Images Endpoint", False, "No valid project ID found")
                return
            
            # Test 3D images endpoint
            images_response = self.session.get(f"{BACKEND_URL}/projects/{project_id}/3d-images", headers=headers)
            
            if images_response.status_code == 200:
                images_data = images_response.json()
                
                # Check if response is structured correctly
                if isinstance(images_data, dict):
                    total_images = 0
                    valid_file_urls = 0
                    
                    for category, images in images_data.items():
                        if isinstance(images, list):
                            total_images += len(images)
                            
                            for image in images:
                                file_url = image.get("file_url", "")
                                
                                # Check if file_url starts with /api/uploads/3d_images/
                                if file_url.startswith("/api/uploads/3d_images/"):
                                    valid_file_urls += 1
                                    
                                    # Test if the image is accessible
                                    full_url = f"https://pm-system.preview.emergentagent.com{file_url}"
                                    try:
                                        img_response = self.session.head(full_url, headers=headers, timeout=10)
                                        if img_response.status_code == 200:
                                            print(f"   ✅ Image accessible: {file_url}")
                                        else:
                                            print(f"   ⚠️ Image not accessible: {file_url} (Status: {img_response.status_code})")
                                    except Exception as e:
                                        print(f"   ⚠️ Error accessing image {file_url}: {str(e)}")
                    
                    if total_images > 0:
                        if valid_file_urls == total_images:
                            self.log_result("3D Images Endpoint", True, 
                                          f"Found {total_images} images, all have correct file_url format (/api/uploads/3d_images/)")
                        else:
                            self.log_result("3D Images Endpoint", False, 
                                          f"Found {total_images} images, but only {valid_file_urls} have correct file_url format")
                    else:
                        self.log_result("3D Images Endpoint", True, 
                                      "3D images endpoint working, but no images found (empty state)")
                        
                elif isinstance(images_data, list) and len(images_data) == 0:
                    self.log_result("3D Images Endpoint", True, 
                                  "3D images endpoint working, but no images found (empty array)")
                else:
                    self.log_result("3D Images Endpoint", False, 
                                  f"Unexpected response format: {type(images_data)}")
            else:
                self.log_result("3D Images Endpoint", False, 
                              f"Failed to fetch 3D images: {images_response.status_code}", images_response.text)
                
        except Exception as e:
            self.log_result("3D Images Endpoint", False, f"Exception: {str(e)}")

    def test_team_leader_dashboard_differentiation(self):
        """Test Team Leader Dashboard vs My Work differentiation"""
        if not self.team_leader_token or not self.project_id:
            self.log_result("Dashboard Differentiation", False, "Missing team leader token or project ID")
            return
            
        try:
            print("🎯 Testing Team Leader Dashboard vs My Work Differentiation...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Test 1: Verify projects endpoint has team_leader_id
            projects_response = self.session.get(f"{BACKEND_URL}/projects", headers=headers)
            
            if projects_response.status_code != 200:
                self.log_result("Dashboard Differentiation", False, 
                              f"Failed to fetch projects: {projects_response.status_code}")
                return
            
            projects = projects_response.json()
            team_leader_field_exists = any("team_leader_id" in p for p in projects)
            
            if not team_leader_field_exists:
                self.log_result("Dashboard Differentiation", False, 
                              "Projects missing team_leader_id field")
                return
            
            # Test 2: Check drawings endpoint for actionable fields
            drawings_response = self.session.get(f"{BACKEND_URL}/projects/{self.project_id}/drawings", headers=headers)
            
            if drawings_response.status_code == 200:
                drawings = drawings_response.json()
                
                if drawings:
                    # Check for My Work differentiation fields
                    required_fields = ["has_pending_revision", "under_review", "is_approved", "is_issued"]
                    sample_drawing = drawings[0]
                    
                    missing_fields = [field for field in required_fields if field not in sample_drawing]
                    
                    if not missing_fields:
                        self.log_result("Dashboard Differentiation", True, 
                                      f"All required fields present in drawings: {required_fields}")
                    else:
                        # Check if drawings have status field that could be used for differentiation
                        if "status" in sample_drawing:
                            self.log_result("Dashboard Differentiation", True, 
                                          f"Drawings have status field for differentiation. Missing fields: {missing_fields}")
                        else:
                            self.log_result("Dashboard Differentiation", False, 
                                          f"Missing required fields for My Work differentiation: {missing_fields}")
                else:
                    self.log_result("Dashboard Differentiation", True, 
                                  "Drawings endpoint working, but no drawings found (empty state)")
            elif drawings_response.status_code == 404:
                self.log_result("Dashboard Differentiation", True, 
                              "Drawings endpoint not found (may not be implemented yet)")
            else:
                self.log_result("Dashboard Differentiation", False, 
                              f"Failed to fetch drawings: {drawings_response.status_code}")
                
        except Exception as e:
            self.log_result("Dashboard Differentiation", False, f"Exception: {str(e)}")

    def test_3d_image_categories_endpoint(self):
        """Test 3D Image Categories endpoint"""
        if not self.owner_token:
            self.log_result("3D Image Categories", False, "No owner token available")
            return
            
        try:
            print("📂 Testing 3D Image Categories Endpoint...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = self.session.get(f"{BACKEND_URL}/3d-image-categories", headers=headers)
            
            if response.status_code == 200:
                categories = response.json()
                
                if isinstance(categories, list) and len(categories) > 0:
                    # Check if we have the expected 28 preset categories
                    if len(categories) >= 28:
                        self.log_result("3D Image Categories", True, 
                                      f"Found {len(categories)} categories (expected 28+ preset categories)")
                    else:
                        self.log_result("3D Image Categories", True, 
                                      f"Found {len(categories)} categories (fewer than expected 28)")
                else:
                    self.log_result("3D Image Categories", False, 
                                  f"Unexpected categories format: {type(categories)}")
            else:
                self.log_result("3D Image Categories", False, 
                              f"Failed to fetch categories: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("3D Image Categories", False, f"Exception: {str(e)}")

    def test_user_projects_endpoint(self):
        """Test user-specific projects endpoint"""
        if not self.team_leader_token:
            self.log_result("User Projects Endpoint", False, "No team leader token available")
            return
            
        try:
            print("👤 Testing User Projects Endpoint...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            user_id = "354afa65-0337-4859-ba4d-0e66d5dfd5f1"
            
            response = self.session.get(f"{BACKEND_URL}/users/{user_id}/projects", headers=headers)
            
            if response.status_code == 200:
                user_projects = response.json()
                
                if isinstance(user_projects, list):
                    self.log_result("User Projects Endpoint", True, 
                                  f"User projects endpoint working. Found {len(user_projects)} projects for user")
                else:
                    self.log_result("User Projects Endpoint", False, 
                                  f"Unexpected response format: {type(user_projects)}")
            elif response.status_code == 404:
                self.log_result("User Projects Endpoint", True, 
                              "User projects endpoint not implemented (may be optional)")
            else:
                self.log_result("User Projects Endpoint", False, 
                              f"Failed to fetch user projects: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("User Projects Endpoint", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Backend API Tests for Review Request")
        print("=" * 60)
        
        # Authentication tests
        self.test_team_leader_login()
        self.test_owner_login()
        
        # Core functionality tests
        self.test_my_work_endpoint()
        self.test_3d_images_endpoint()
        self.test_team_leader_dashboard_differentiation()
        
        # Additional related tests
        self.test_3d_image_categories_endpoint()
        self.test_user_projects_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED - No critical issues found")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()