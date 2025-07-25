#!/usr/bin/env python3
"""
Test script for the refresh endpoint
"""

import requests
import json

def test_refresh_endpoint():
    """Test the refresh endpoint"""
    
    # Test URL
    base_url = "http://localhost:8000"
    survey_id = 3200079
    
    # Test the refresh endpoint
    url = f"{base_url}/api/surveybot/surveys/{survey_id}/refresh"
    
    print(f"Testing refresh endpoint: {url}")
    print(f"Method: POST")
    
    try:
        response = requests.post(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Refresh endpoint working correctly!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Refresh endpoint failed!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the API is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_other_endpoints():
    """Test other endpoints to ensure they work"""
    
    base_url = "http://localhost:8000"
    survey_id = 3200079
    
    endpoints = [
        ("GET", f"{base_url}/", "Root endpoint"),
        ("GET", f"{base_url}/health", "Health check"),
        ("GET", f"{base_url}/api/surveybot/surveys/{survey_id}/data", "Survey data"),
        ("GET", f"{base_url}/api/surveybot/surveys/{survey_id}/questions", "Survey questions"),
        ("GET", f"{base_url}/api/surveybot/surveys/{survey_id}/summary", "Survey summary"),
    ]
    
    print("\n" + "="*50)
    print("Testing other endpoints:")
    print("="*50)
    
    for method, url, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url)
                
            print(f"{description}: {response.status_code}")
            
        except Exception as e:
            print(f"{description}: Error - {e}")

if __name__ == "__main__":
    print("Testing ONOW Survey Bot API endpoints...")
    test_refresh_endpoint()
    test_other_endpoints()