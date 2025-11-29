#!/usr/bin/env python3
"""
Test script specifically for in-app notification system
"""

import sys
import os
sys.path.append('/app')

from backend_test import BackendTester

if __name__ == "__main__":
    tester = BackendTester()
    
    print("🔔 Running In-App Notification System Test")
    print("=" * 60)
    
    # Run the notification test
    tester.test_in_app_notification_system()
    
    # Show results
    notification_tests = [result for result in tester.test_results if "Notification System" in result["test"]]
    passed = sum(1 for result in notification_tests if result["success"])
    total = len(notification_tests)
    
    print("\n" + "=" * 60)
    print("📊 NOTIFICATION SYSTEM TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
    
    if total - passed > 0:
        print("\n❌ FAILED TESTS:")
        for result in notification_tests:
            if not result["success"]:
                print(f"  - {result['test']}: {result['details']}")
    
    sys.exit(0 if passed == total else 1)