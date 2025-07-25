#!/usr/bin/env python3

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root():
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_survey_questions():
    try:
        response = requests.get(f"{BASE_URL}/api/surveybot/surveys/3200079/questions")
        if response.status_code == 200:
            data = response.json()
            questions = data.get('questions', [])
            print(f"✅ Survey questions: Found {len(questions)} questions")
            return True
        else:
            print(f"❌ Survey questions failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Survey questions error: {e}")
        return False

def test_query():
    try:
        payload = {
            "query": "Show me the total number of responses",
            "survey_id": 3200079
        }
        response = requests.post(f"{BASE_URL}/api/surveybot/query", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Query endpoint: Success")
                return True
            else:
                print(f"❌ Query endpoint: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Query endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Query endpoint error: {e}")
        return False

def main():
    print("🧪 Testing ONOW Survey Bot API...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Survey Questions", test_survey_questions),
        ("Query Endpoint", test_query)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 