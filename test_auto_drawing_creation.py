#!/usr/bin/env python3
"""
Test Auto-Drawing Creation Fix
Tests that drawings are auto-created with correct categories matching project_types
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Get backend URL from frontend .env
BACKEND_URL = "https://pmapp-stability.preview.emergentagent.com/api"

class AutoDrawingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
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

    def test_auto_drawing_creation_fix(self):
        """Test auto-drawing creation fix - drawings should have categories matching project_types"""
        print(f"\n🎨 Testing Auto-Drawing Creation Fix")
        print("=" * 60)
        
        # Step 1: Login with owner credentials
        try:
            print("Step 1: Logging in as owner...")
            owner_credentials = {
                "email": "owner@test.com",
                "password": "testpassword"
            }
            
            login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=owner_credentials)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.auth_token = login_data["access_token"]
                self.log_result("Auto-Drawing Creation - Owner Login", True, 
                              "Successfully authenticated as owner")
            else:
                self.log_result("Auto-Drawing Creation - Owner Login", False, 
                              f"Login failed: {login_response.status_code} - {login_response.text}")
                return
                
        except Exception as e:
            self.log_result("Auto-Drawing Creation - Owner Login", False, f"Exception: {str(e)}")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Step 2: Get existing client for project creation
        try:
            print("Step 2: Getting existing client...")
            clients_response = self.session.get(f"{BACKEND_URL}/clients", headers=headers)
            
            if clients_response.status_code == 200:
                clients_data = clients_response.json()
                
                if len(clients_data) > 0:
                    self.test_client = clients_data[0]
                    self.log_result("Auto-Drawing Creation - Get Client", True, 
                                  f"Using client: {self.test_client.get('name', 'N/A')}")
                else:
                    # Create a test client if none exist
                    print("No clients found, creating test client...")
                    client_data = {
                        "name": "Test Client for Auto Drawing",
                        "contact_person": "Test Contact",
                        "email": "testclient@example.com",
                        "phone": "+919876543210",
                        "address": "Test Address",
                        "project_types": ["Architecture", "Interior"]
                    }
                    
                    create_client_response = self.session.post(f"{BACKEND_URL}/clients", 
                                                             json=client_data, headers=headers)
                    
                    if create_client_response.status_code == 200:
                        self.test_client = create_client_response.json()
                        self.log_result("Auto-Drawing Creation - Create Client", True, 
                                      f"Created client: {self.test_client.get('name')}")
                    else:
                        self.log_result("Auto-Drawing Creation - Create Client", False, 
                                      f"Failed to create client: {create_client_response.status_code}")
                        return
            else:
                self.log_result("Auto-Drawing Creation - Get Client", False, 
                              f"Failed to get clients: {clients_response.status_code}")
                return
                
        except Exception as e:
            self.log_result("Auto-Drawing Creation - Get Client", False, f"Exception: {str(e)}")
            return

        # Step 3: Create Architecture Project and Test Auto-Created Drawings
        try:
            print("Step 3: Creating Architecture project and testing auto-created drawings...")
            
            project_data = {
                "code": "ARCH-TEST-001",
                "title": "Architecture Drawing Test",
                "project_types": ["Architecture"],
                "client_id": self.test_client["id"],
                "start_date": "2024-12-01",
                "status": "Lead",
                "site_address": "Test Site Address",
                "notes": "Test project for auto-drawing creation"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/projects", 
                                              json=project_data, headers=headers)
            
            if create_response.status_code == 200:
                project = create_response.json()
                self.arch_project_id = project["id"]
                
                # Get drawings for this project
                drawings_response = self.session.get(f"{BACKEND_URL}/projects/{self.arch_project_id}/drawings", 
                                                   headers=headers)
                
                if drawings_response.status_code == 200:
                    drawings = drawings_response.json()
                    
                    print(f"Found {len(drawings)} drawings for Architecture project")
                    for i, drawing in enumerate(drawings):
                        print(f"  Drawing {i+1}: {drawing.get('name')} - Category: {drawing.get('category')} - Sequence: {drawing.get('sequence_number')} - Active: {drawing.get('is_active')}")
                    
                    # Verify exactly 3 drawings created
                    if len(drawings) == 3:
                        # Check all drawings have category "Architecture"
                        architecture_drawings = [d for d in drawings if d.get('category') == 'Architecture']
                        
                        if len(architecture_drawings) == 3:
                            # Check drawing names
                            expected_names = [
                                "Site Plan & Layout",
                                "Floor Plans & Sections", 
                                "Elevations & 3D Views"
                            ]
                            
                            actual_names = [d.get('name') for d in drawings]
                            names_match = all(name in actual_names for name in expected_names)
                            
                            # Check due dates (3, 7, 10 days from start date)
                            start_date = datetime.strptime("2024-12-01", "%Y-%m-%d")
                            expected_due_dates = [
                                (start_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                                (start_date + timedelta(days=7)).strftime("%Y-%m-%d"),
                                (start_date + timedelta(days=10)).strftime("%Y-%m-%d")
                            ]
                            
                            # Sort drawings by sequence number for comparison
                            sorted_drawings = sorted(drawings, key=lambda x: x.get('sequence_number', 0))
                            actual_due_dates = [d.get('due_date', '').split('T')[0] for d in sorted_drawings]
                            due_dates_match = actual_due_dates == expected_due_dates
                            
                            # Check active status (first drawing should be active)
                            first_drawing_active = sorted_drawings[0].get('is_active', False) == True
                            other_drawings_inactive = all(not d.get('is_active', True) for d in sorted_drawings[1:])
                            
                            # Check sequence numbers
                            sequence_numbers = [d.get('sequence_number') for d in sorted_drawings]
                            sequence_correct = sequence_numbers == [1, 2, 3]
                            
                            if names_match and due_dates_match and first_drawing_active and other_drawings_inactive and sequence_correct:
                                self.log_result("Auto-Drawing Creation - Architecture Project", True, 
                                              f"✅ All checks passed: 3 drawings with category 'Architecture', correct names, due dates, and sequence")
                            else:
                                issues = []
                                if not names_match:
                                    issues.append(f"Names mismatch - Expected: {expected_names}, Got: {actual_names}")
                                if not due_dates_match:
                                    issues.append(f"Due dates mismatch - Expected: {expected_due_dates}, Got: {actual_due_dates}")
                                if not first_drawing_active:
                                    issues.append("First drawing should be active")
                                if not other_drawings_inactive:
                                    issues.append("Other drawings should be inactive")
                                if not sequence_correct:
                                    issues.append(f"Sequence numbers incorrect - Expected: [1,2,3], Got: {sequence_numbers}")
                                
                                self.log_result("Auto-Drawing Creation - Architecture Project", False, 
                                              f"Issues found: {'; '.join(issues)}")
                        else:
                            self.log_result("Auto-Drawing Creation - Architecture Project", False, 
                                          f"Expected 3 drawings with category 'Architecture', got {len(architecture_drawings)}")
                    else:
                        self.log_result("Auto-Drawing Creation - Architecture Project", False, 
                                      f"Expected exactly 3 drawings, got {len(drawings)}")
                else:
                    self.log_result("Auto-Drawing Creation - Architecture Project", False, 
                                  f"Failed to get drawings: {drawings_response.status_code}")
            else:
                self.log_result("Auto-Drawing Creation - Architecture Project", False, 
                              f"Failed to create project: {create_response.status_code} - {create_response.text}")
                
        except Exception as e:
            self.log_result("Auto-Drawing Creation - Architecture Project", False, f"Exception: {str(e)}")

        # Step 4: Create Multi-Type Project and Test Auto-Created Drawings
        try:
            print("Step 4: Creating multi-type project and testing auto-created drawings...")
            
            multi_project_data = {
                "code": "MULTI-TEST-001",
                "title": "Multi-Type Drawing Test",
                "project_types": ["Architecture", "Interior"],
                "client_id": self.test_client["id"],
                "start_date": "2024-12-01",
                "status": "Lead",
                "site_address": "Test Site Address",
                "notes": "Test project for multi-type auto-drawing creation"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/projects", 
                                              json=multi_project_data, headers=headers)
            
            if create_response.status_code == 200:
                project = create_response.json()
                self.multi_project_id = project["id"]
                
                # Get drawings for this project
                drawings_response = self.session.get(f"{BACKEND_URL}/projects/{self.multi_project_id}/drawings", 
                                                   headers=headers)
                
                if drawings_response.status_code == 200:
                    drawings = drawings_response.json()
                    
                    print(f"Found {len(drawings)} drawings for Multi-Type project")
                    for i, drawing in enumerate(drawings):
                        print(f"  Drawing {i+1}: {drawing.get('name')} - Category: {drawing.get('category')} - Sequence: {drawing.get('sequence_number')}")
                    
                    # Verify exactly 6 drawings created (3 Architecture + 3 Interior)
                    if len(drawings) == 6:
                        # Check Architecture drawings
                        arch_drawings = [d for d in drawings if d.get('category') == 'Architecture']
                        interior_drawings = [d for d in drawings if d.get('category') == 'Interior']
                        
                        if len(arch_drawings) == 3 and len(interior_drawings) == 3:
                            # Check Architecture drawing names
                            expected_arch_names = [
                                "Site Plan & Layout",
                                "Floor Plans & Sections", 
                                "Elevations & 3D Views"
                            ]
                            
                            # Check Interior drawing names
                            expected_interior_names = [
                                "Space Planning & Layout",
                                "Furniture & Fixture Layout",
                                "Lighting & Electrical Plan"
                            ]
                            
                            arch_names = [d.get('name') for d in arch_drawings]
                            interior_names = [d.get('name') for d in interior_drawings]
                            
                            arch_names_match = all(name in arch_names for name in expected_arch_names)
                            interior_names_match = all(name in interior_names for name in expected_interior_names)
                            
                            # Check sequence numbers (should be 1-6)
                            sorted_drawings = sorted(drawings, key=lambda x: x.get('sequence_number', 0))
                            sequence_numbers = [d.get('sequence_number') for d in sorted_drawings]
                            sequence_correct = sequence_numbers == [1, 2, 3, 4, 5, 6]
                            
                            # Check only first drawing is active
                            first_drawing_active = sorted_drawings[0].get('is_active', False) == True
                            other_drawings_inactive = all(not d.get('is_active', True) for d in sorted_drawings[1:])
                            
                            if arch_names_match and interior_names_match and sequence_correct and first_drawing_active and other_drawings_inactive:
                                self.log_result("Auto-Drawing Creation - Multi-Type Project", True, 
                                              f"✅ All checks passed: 6 drawings (3 Architecture + 3 Interior) with correct categories, names, and sequence")
                            else:
                                issues = []
                                if not arch_names_match:
                                    issues.append(f"Architecture names mismatch - Expected: {expected_arch_names}, Got: {arch_names}")
                                if not interior_names_match:
                                    issues.append(f"Interior names mismatch - Expected: {expected_interior_names}, Got: {interior_names}")
                                if not sequence_correct:
                                    issues.append(f"Sequence numbers incorrect - Expected: [1,2,3,4,5,6], Got: {sequence_numbers}")
                                if not first_drawing_active:
                                    issues.append("First drawing should be active")
                                if not other_drawings_inactive:
                                    issues.append("Other drawings should be inactive")
                                
                                self.log_result("Auto-Drawing Creation - Multi-Type Project", False, 
                                              f"Issues found: {'; '.join(issues)}")
                        else:
                            self.log_result("Auto-Drawing Creation - Multi-Type Project", False, 
                                          f"Expected 3 Architecture + 3 Interior drawings, got {len(arch_drawings)} + {len(interior_drawings)}")
                    else:
                        self.log_result("Auto-Drawing Creation - Multi-Type Project", False, 
                                      f"Expected exactly 6 drawings, got {len(drawings)}")
                else:
                    self.log_result("Auto-Drawing Creation - Multi-Type Project", False, 
                                  f"Failed to get drawings: {drawings_response.status_code}")
            else:
                self.log_result("Auto-Drawing Creation - Multi-Type Project", False, 
                              f"Failed to create project: {create_response.status_code} - {create_response.text}")
                
        except Exception as e:
            self.log_result("Auto-Drawing Creation - Multi-Type Project", False, f"Exception: {str(e)}")

        print("✅ Auto-Drawing Creation fix testing completed")

    def run_test(self):
        """Run the auto-drawing creation test"""
        print(f"🚀 Starting Auto-Drawing Creation Fix Test")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        self.test_auto_drawing_creation_fix()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = AutoDrawingTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)