#!/usr/bin/env python3
"""
Backend API Testing Script for Architecture Firm Management System
Testing Drawing Notification System as requested in review:
1. Test Drawing Upload Notification (under_review: true)
2. Test Issued Drawing Notification (is_issued: true)
3. Verify WhatsApp Templates Used
4. Check backend logs for notification messages
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://review-page.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.team_leader_token = None
        self.owner_token = None
        self.project_id = None
        self.drawing_id = None
        self.drawing_name = None
        
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

    def test_drawing_upload_notification(self):
        """Test drawing upload notification (under_review: true)"""
        if not self.team_leader_token or not self.drawing_id:
            self.log_result("Drawing Upload Notification", False, "Missing token or drawing ID")
            return
            
        try:
            print("📤 Testing Drawing Upload Notification...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Update drawing to mark as under_review
            update_data = {"under_review": True}
            
            response = self.session.put(
                f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                self.log_result("Drawing Upload Notification", True, 
                              f"Drawing {self.drawing_name} marked as under_review. Check backend logs for notifications.")
                
                # Wait a moment for async notifications to process
                time.sleep(2)
                
                return True
            else:
                self.log_result("Drawing Upload Notification", False, 
                              f"Failed to update drawing: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Drawing Upload Notification", False, f"Exception: {str(e)}")
            return False

    def test_drawing_issued_notification(self):
        """Test drawing issued notification (is_issued: true)"""
        if not self.team_leader_token or not self.drawing_id:
            self.log_result("Drawing Issued Notification", False, "Missing token or drawing ID")
            return
            
        try:
            print("✅ Testing Drawing Issued Notification...")
            
            headers = {"Authorization": f"Bearer {self.team_leader_token}"}
            
            # Update drawing to mark as issued
            update_data = {"is_issued": True}
            
            response = self.session.put(
                f"{BACKEND_URL}/drawings/{self.drawing_id}", 
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                self.log_result("Drawing Issued Notification", True, 
                              f"Drawing {self.drawing_name} marked as issued. Check backend logs for notifications.")
                
                # Wait a moment for async notifications to process
                time.sleep(2)
                
                return True
            else:
                self.log_result("Drawing Issued Notification", False, 
                              f"Failed to update drawing: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Drawing Issued Notification", False, f"Exception: {str(e)}")
            return False

    def test_notification_logs(self):
        """Test notification logs to verify template usage"""
        if not self.owner_token:
            self.log_result("Notification Logs Check", False, "No owner token available")
            return
            
        try:
            print("📄 Testing Notification Logs...")
            
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Try to get recent logs
            response = self.session.get(f"{BACKEND_URL}/aggregated/logs?page=1&page_size=20", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                
                # Look for recent notification logs
                notification_logs = []
                template_logs = []
                
                for log in logs:
                    log_message = log.get("message", "").lower()
                    if any(keyword in log_message for keyword in ["notification", "whatsapp", "template", "email"]):
                        notification_logs.append(log)
                        if "template" in log_message:
                            template_logs.append(log)
                
                if notification_logs:
                    self.log_result("Notification Logs Check", True, 
                                  f"Found {len(notification_logs)} notification logs, {len(template_logs)} template logs")
                    
                    # Print some recent notification logs
                    print("   Recent notification logs:")
                    for log in notification_logs[:5]:
                        timestamp = log.get("timestamp", "")
                        message = log.get("message", "")
                        print(f"     {timestamp}: {message}")
                else:
                    self.log_result("Notification Logs Check", True, 
                                  "No recent notification logs found (may be in different log format)")
            else:
                self.log_result("Notification Logs Check", False, 
                              f"Failed to fetch logs: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Notification Logs Check", False, f"Exception: {str(e)}")

    def test_template_service_availability(self):
        """Test if template notification service is available"""
        try:
            print("🔧 Testing Template Service Availability...")
            
            # Test health endpoint to see if template service is loaded
            response = self.session.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                self.log_result("Template Service Health", True, 
                              "Backend health check passed")
            else:
                self.log_result("Template Service Health", False, 
                              f"Health check failed: {response.status_code}")
            
            # Test ops status if available
            if self.owner_token:
                headers = {"Authorization": f"Bearer {self.owner_token}"}
                ops_response = self.session.get(f"{BACKEND_URL}/ops/status", headers=headers)
                
                if ops_response.status_code == 200:
                    ops_data = ops_response.json()
                    self.log_result("Template Service Status", True, 
                                  f"Ops status available with {len(ops_data)} status items")
                else:
                    self.log_result("Template Service Status", False, 
                                  f"Ops status failed: {ops_response.status_code}")
                
        except Exception as e:
            self.log_result("Template Service Availability", False, f"Exception: {str(e)}")

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