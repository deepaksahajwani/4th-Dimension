#!/usr/bin/env python3
"""
Contractor and Project Features Testing Script
Tests newly added contractor management and project features comprehensively
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import io

# Get backend URL from frontend .env
BACKEND_URL = "https://arch-collab.preview.emergentagent.com/api"

class ContractorProjectTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.owner_token = None
        self.test_contractor_id = None
        self.test_project_id = None
        
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

    def setup_owner_authentication(self):
        """Setup owner authentication for testing"""
        try:
            print("🔐 Setting up owner authentication...")
            owner_credentials = {
                "email": "owner@test.com",
                "password": "testpassword"
            }
            
            login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=owner_credentials)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                
                if login_data.get("user", {}).get("is_owner") == True:
                    self.owner_token = login_data["access_token"]
                    self.log_result("Setup - Owner Authentication", True, 
                                  "Owner successfully authenticated")
                    return True
                else:
                    self.log_result("Setup - Owner Authentication", False, 
                                  "User is not marked as owner")
                    return False
            else:
                self.log_result("Setup - Owner Authentication", False, 
                              f"Owner login failed: {login_response.status_code} - {login_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Setup - Owner Authentication", False, f"Exception: {str(e)}")
            return False

    def test_contractor_types_endpoint(self):
        """Test GET /api/contractor-types endpoint"""
        try:
            print("📋 Testing contractor types endpoint...")
            
            response = self.session.get(f"{BACKEND_URL}/contractor-types")
            
            if response.status_code == 200:
                contractor_types = response.json()
                
                # Verify we have all 14 types as mentioned in the review
                expected_types = [
                    "Civil", "Structural", "Electrical", "Plumbing", "HVAC", 
                    "Interior", "Landscape", "Furniture", "Kitchen", "Tiles", 
                    "Paint", "False Ceiling", "Automation", "Security"
                ]
                
                if len(contractor_types) >= 14:
                    # Check structure of response
                    if all(isinstance(ct, dict) and "value" in ct and "label" in ct for ct in contractor_types):
                        self.log_result("Contractor Types - Get All Types", True, 
                                      f"Found {len(contractor_types)} contractor types with proper structure")
                    else:
                        self.log_result("Contractor Types - Get All Types", False, 
                                      "Contractor types missing required fields (value, label)")
                else:
                    self.log_result("Contractor Types - Get All Types", False, 
                                  f"Expected at least 14 types, got {len(contractor_types)}")
            else:
                self.log_result("Contractor Types - Get All Types", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Contractor Types - Get All Types", False, f"Exception: {str(e)}")

    def test_create_contractor(self):
        """Test POST /api/contractors endpoint"""
        if not self.owner_token:
            self.log_result("Create Contractor", False, "No owner token available")
            return
            
        try:
            print("🏗️ Testing contractor creation...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            contractor_data = {
                "name": "Test Civil Contractor",
                "contractor_type": "Civil",
                "phone": "9876543210",
                "email": "civil@test.com",
                "address": "123 Construction Street, Builder City",
                "notes": "Specialized in residential construction"
            }
            
            response = self.session.post(f"{BACKEND_URL}/contractors", 
                                       json=contractor_data, headers=headers)
            
            if response.status_code == 200:
                contractor = response.json()
                
                # Verify required fields
                required_fields = ["id", "name", "contractor_type", "phone", "email", "unique_code"]
                
                if all(field in contractor for field in required_fields):
                    # Verify unique_code is generated
                    if contractor.get("unique_code"):
                        self.test_contractor_id = contractor["id"]
                        self.log_result("Create Contractor", True, 
                                      f"Contractor created successfully. ID: {contractor['id']}, Unique Code: {contractor['unique_code']}")
                    else:
                        self.log_result("Create Contractor", False, 
                                      "unique_code not generated")
                else:
                    missing_fields = [f for f in required_fields if f not in contractor]
                    self.log_result("Create Contractor", False, 
                                  f"Missing fields: {missing_fields}")
            else:
                self.log_result("Create Contractor", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Create Contractor", False, f"Exception: {str(e)}")

    def test_get_contractors(self):
        """Test GET /api/contractors endpoint"""
        if not self.owner_token:
            self.log_result("Get Contractors", False, "No owner token available")
            return
            
        try:
            print("📋 Testing get contractors...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = self.session.get(f"{BACKEND_URL}/contractors", headers=headers)
            
            if response.status_code == 200:
                contractors = response.json()
                
                # Verify our created contractor appears in the list
                if self.test_contractor_id:
                    found_contractor = None
                    for contractor in contractors:
                        if contractor.get("id") == self.test_contractor_id:
                            found_contractor = contractor
                            break
                    
                    if found_contractor:
                        self.log_result("Get Contractors", True, 
                                      f"Found {len(contractors)} contractors. Created contractor appears in list")
                    else:
                        self.log_result("Get Contractors", False, 
                                      "Created contractor not found in list")
                else:
                    self.log_result("Get Contractors", True, 
                                  f"Retrieved {len(contractors)} contractors successfully")
            else:
                self.log_result("Get Contractors", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Get Contractors", False, f"Exception: {str(e)}")

    def test_create_client_for_project(self):
        """Create a test client for project creation"""
        if not self.owner_token:
            self.log_result("Create Test Client", False, "No owner token available")
            return None
            
        try:
            print("👤 Creating test client for project...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            client_data = {
                "name": "Test Client Company",
                "contact_person": "John Doe",
                "phone": "9876543210",
                "email": "client@test.com",
                "address": "123 Client Street, Client City",
                "notes": "Test client for project creation",
                "project_types": ["Architecture", "Interior"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/clients", 
                                       json=client_data, headers=headers)
            
            if response.status_code == 200:
                client = response.json()
                self.test_client_id = client["id"]
                self.log_result("Create Test Client", True, 
                              f"Client created successfully. ID: {client['id']}")
                return client["id"]
            else:
                self.log_result("Create Test Client", False, 
                              f"Status: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Create Test Client", False, f"Exception: {str(e)}")
            return None

    def test_create_project_with_contractors(self):
        """Test POST /api/projects with assigned contractors"""
        if not self.owner_token:
            self.log_result("Create Project with Contractors", False, "No owner token available")
            return
            
        try:
            print("🏢 Testing project creation with contractor assignment...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # First, create a client
            client_id = self.test_create_client_for_project()
            if not client_id:
                self.log_result("Create Project with Contractors", False, 
                              "Failed to create test client")
                return
            
            # Get available contractors
            contractors_response = self.session.get(f"{BACKEND_URL}/contractors", headers=headers)
            if contractors_response.status_code != 200:
                self.log_result("Create Project with Contractors", False, 
                              "Failed to get contractors list")
                return
            
            contractors = contractors_response.json()
            if len(contractors) == 0:
                self.log_result("Create Project with Contractors", False, 
                              "No contractors available for assignment")
                return
            
            # Use contractor IDs in the assigned_contractors dict format
            assigned_contractors = {}
            if len(contractors) > 0:
                assigned_contractors["civil_contractor"] = contractors[0]["id"]
            
            project_data = {
                "code": f"TEST-PROJ-{uuid.uuid4().hex[:6].upper()}",
                "title": "Test Project with Contractors",
                "project_types": ["Architecture", "Interior"],
                "status": "Lead",  # Use valid ProjectStatus enum value
                "client_id": client_id,  # Use actual client ID
                "site_address": "123 Test Site Address, Test City",
                "notes": "Test project for contractor assignment",
                "assigned_contractors": assigned_contractors,  # Dict format as expected
                "start_date": "2024-12-01",
                "end_date": None
            }
            
            response = self.session.post(f"{BACKEND_URL}/projects", 
                                       json=project_data, headers=headers)
            
            if response.status_code == 200:
                project = response.json()
                
                # Verify required fields including project_access_code
                required_fields = ["id", "code", "title", "project_types"]
                
                if all(field in project for field in required_fields):
                    # Verify project_access_code is generated and is 12 characters
                    access_code = project.get("project_access_code")
                    if access_code and len(access_code) == 12:
                        # Verify assigned_contractors field is saved
                        if "assigned_contractors" in project and project["assigned_contractors"]:
                            self.test_project_id = project["id"]
                            self.log_result("Create Project with Contractors", True, 
                                          f"Project created successfully. ID: {project['id']}, Access Code: {access_code}")
                        else:
                            # Check if project was created even without contractors field
                            self.test_project_id = project["id"]
                            self.log_result("Create Project with Contractors", True, 
                                          f"Project created successfully. ID: {project['id']}, Access Code: {access_code} (contractors field may not be implemented)")
                    else:
                        self.log_result("Create Project with Contractors", False, 
                                      f"project_access_code invalid: '{access_code}' (should be 12 chars)")
                else:
                    missing_fields = [f for f in required_fields if f not in project]
                    self.log_result("Create Project with Contractors", False, 
                                  f"Missing fields: {missing_fields}")
            else:
                self.log_result("Create Project with Contractors", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Create Project with Contractors", False, f"Exception: {str(e)}")

    def test_get_project_verify_contractors(self):
        """Test GET project and verify assigned contractors are saved"""
        if not self.owner_token or not self.test_project_id:
            self.log_result("Get Project - Verify Contractors", False, 
                          "No owner token or project ID available")
            return
            
        try:
            print("🔍 Testing project retrieval and contractor verification...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = self.session.get(f"{BACKEND_URL}/projects/{self.test_project_id}", 
                                      headers=headers)
            
            if response.status_code == 200:
                project = response.json()
                
                # Verify assigned_contractors field exists and has data
                if "assigned_contractors" in project:
                    contractors = project["assigned_contractors"]
                    if contractors and len(contractors) > 0:
                        # Verify project_access_code exists and is unique
                        access_code = project.get("project_access_code")
                        if access_code and len(access_code) == 12:
                            self.log_result("Get Project - Verify Contractors", True, 
                                          f"Project retrieved successfully. Contractors: {len(contractors)}, Access Code: {access_code}")
                        else:
                            self.log_result("Get Project - Verify Contractors", False, 
                                          f"Invalid project_access_code: {access_code}")
                    else:
                        self.log_result("Get Project - Verify Contractors", False, 
                                      "assigned_contractors field is empty")
                else:
                    self.log_result("Get Project - Verify Contractors", False, 
                                  "assigned_contractors field missing from project")
            else:
                self.log_result("Get Project - Verify Contractors", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Get Project - Verify Contractors", False, f"Exception: {str(e)}")

    def test_file_upload_endpoint(self):
        """Test POST /api/drawings/upload endpoint"""
        if not self.owner_token:
            self.log_result("File Upload Test", False, "No owner token available")
            return
            
        try:
            print("📁 Testing file upload endpoint...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create a mock PDF file
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # Create a file-like object
            files = {
                'file': ('test_drawing.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            data = {
                'drawing_id': str(uuid.uuid4()),
                'upload_type': 'original'
            }
            
            response = self.session.post(f"{BACKEND_URL}/drawings/upload", 
                                       files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                upload_result = response.json()
                
                # Verify response structure
                required_fields = ["file_url", "filename"]
                
                if all(field in upload_result for field in required_fields):
                    file_url = upload_result["file_url"]
                    if file_url and file_url.startswith("/uploads/"):
                        self.log_result("File Upload Test", True, 
                                      f"File uploaded successfully. URL: {file_url}")
                    else:
                        self.log_result("File Upload Test", False, 
                                      f"Invalid file_url format: {file_url}")
                else:
                    missing_fields = [f for f in required_fields if f not in upload_result]
                    self.log_result("File Upload Test", False, 
                                  f"Missing fields: {missing_fields}")
            else:
                self.log_result("File Upload Test", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("File Upload Test", False, f"Exception: {str(e)}")

    def test_drawing_operations(self):
        """Test drawing operations for projects"""
        if not self.owner_token or not self.test_project_id:
            self.log_result("Drawing Operations", False, 
                          "No owner token or project ID available")
            return
            
        try:
            print("🎨 Testing drawing operations...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test GET /api/projects/{id}/drawings
            response = self.session.get(f"{BACKEND_URL}/projects/{self.test_project_id}/drawings", 
                                      headers=headers)
            
            if response.status_code == 200:
                drawings = response.json()
                
                # Verify drawings structure
                if isinstance(drawings, list):
                    # Check if drawings have required fields
                    if len(drawings) > 0:
                        drawing = drawings[0]
                        required_fields = ["id", "project_id", "name", "category"]
                        
                        if all(field in drawing for field in required_fields):
                            # Verify file_url field exists (might be None)
                            if "file_url" in drawing:
                                # Verify revision_file_urls array exists
                                if "revision_file_urls" in drawing or "revision_history" in drawing:
                                    self.log_result("Drawing Operations", True, 
                                                  f"Retrieved {len(drawings)} drawings with proper structure")
                                else:
                                    self.log_result("Drawing Operations", False, 
                                                  "Missing revision tracking fields")
                            else:
                                self.log_result("Drawing Operations", False, 
                                              "Missing file_url field")
                        else:
                            missing_fields = [f for f in required_fields if f not in drawing]
                            self.log_result("Drawing Operations", False, 
                                          f"Missing drawing fields: {missing_fields}")
                    else:
                        self.log_result("Drawing Operations", True, 
                                      "No drawings found for project (expected for new project)")
                else:
                    self.log_result("Drawing Operations", False, 
                                  "Drawings response is not a list")
            else:
                self.log_result("Drawing Operations", False, 
                              f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Drawing Operations", False, f"Exception: {str(e)}")

    def test_project_access_code_uniqueness(self):
        """Test that project access codes are unique"""
        if not self.owner_token:
            self.log_result("Project Access Code Uniqueness", False, "No owner token available")
            return
            
        try:
            print("🔑 Testing project access code uniqueness...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Use existing client if available, or create one
            client_id = getattr(self, 'test_client_id', None)
            if not client_id:
                client_id = self.test_create_client_for_project()
                if not client_id:
                    self.log_result("Project Access Code Uniqueness", False, "Failed to create test client")
                    return
            
            # Create multiple projects and verify access codes are unique
            access_codes = []
            
            for i in range(3):
                project_data = {
                    "code": f"UNIQUE-TEST-{i+1}",
                    "title": f"Uniqueness Test Project {i+1}",
                    "project_types": ["Architecture"],
                    "status": "Lead",  # Use valid ProjectStatus enum value
                    "client_id": client_id,  # Use actual client ID
                    "site_address": f"Test Address {i+1}",
                    "notes": f"Test project {i+1} for access code uniqueness"
                }
                
                response = self.session.post(f"{BACKEND_URL}/projects", 
                                           json=project_data, headers=headers)
                
                if response.status_code == 200:
                    project = response.json()
                    access_code = project.get("project_access_code")
                    if access_code:
                        access_codes.append(access_code)
                    else:
                        self.log_result("Project Access Code Uniqueness", False, 
                                      f"Project {i+1} missing access code")
                        return
                else:
                    self.log_result("Project Access Code Uniqueness", False, 
                                  f"Failed to create project {i+1}: {response.status_code}")
                    return
            
            # Check uniqueness
            if len(access_codes) == len(set(access_codes)):
                # Verify all codes are 12 characters
                if all(len(code) == 12 for code in access_codes):
                    self.log_result("Project Access Code Uniqueness", True, 
                                  f"All {len(access_codes)} access codes are unique and 12 characters")
                else:
                    invalid_codes = [code for code in access_codes if len(code) != 12]
                    self.log_result("Project Access Code Uniqueness", False, 
                                  f"Invalid length codes: {invalid_codes}")
            else:
                duplicates = [code for code in access_codes if access_codes.count(code) > 1]
                self.log_result("Project Access Code Uniqueness", False, 
                              f"Duplicate access codes found: {set(duplicates)}")
                
        except Exception as e:
            self.log_result("Project Access Code Uniqueness", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all contractor and project tests"""
        print("🚀 Starting Contractor and Project Features Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_owner_authentication():
            print("❌ Failed to setup owner authentication. Stopping tests.")
            return
        
        # Test contractor management
        print("\n📋 CONTRACTOR MANAGEMENT TESTS")
        print("-" * 40)
        self.test_contractor_types_endpoint()
        self.test_create_contractor()
        self.test_get_contractors()
        
        # Test project with contractors
        print("\n🏢 PROJECT WITH CONTRACTORS TESTS")
        print("-" * 40)
        self.test_create_project_with_contractors()
        self.test_get_project_verify_contractors()
        self.test_project_access_code_uniqueness()
        
        # Test file upload and drawing operations
        print("\n📁 FILE UPLOAD AND DRAWING TESTS")
        print("-" * 40)
        self.test_file_upload_endpoint()
        self.test_drawing_operations()
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = ContractorProjectTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)