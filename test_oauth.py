#!/usr/bin/env python3
"""
Simple test script to verify OAuth setup and API endpoints.
Run this after setting up your .env file with Google OAuth credentials.
"""

import os
import requests
import sys
from urllib.parse import urlparse

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8888/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the application. Is it running?")
        return False

def test_login_page():
    """Test the login page loads"""
    try:
        response = requests.get("http://localhost:8888/login")
        if response.status_code == 200 and "Continue with Google" in response.text:
            print("✅ Login page loads with Google OAuth button")
            return True
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to login page")
        return False

def test_oauth_config():
    """Test OAuth configuration"""
    try:
        response = requests.get("http://localhost:8888/auth/google")
        
        # Should redirect to Google (or return error if not configured)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'accounts.google.com' in location:
                print("✅ OAuth redirect to Google working")
                return True
            else:
                print(f"❌ OAuth redirect not to Google: {location}")
                return False
        elif response.status_code == 500:
            try:
                error_data = response.json()
                if "not configured" in error_data.get("error", ""):
                    print("⚠️  Google OAuth not configured (missing GOOGLE_CLIENT_ID/SECRET)")
                    return False
                else:
                    print(f"❌ OAuth setup error: {error_data}")
                    return False
            except:
                print(f"❌ OAuth setup failed: {response.status_code}")
                return False
        else:
            print(f"❌ Unexpected OAuth response: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot test OAuth endpoint")
        return False

def check_environment():
    """Check if environment file exists and has required variables"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("⚠️  .env file not found. Create one with your Google OAuth credentials.")
        return False
    
    required_vars = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET", 
        "JWT_SECRET_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or placeholder values in .env: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Environment file looks good")
        return True

def main():
    """Run all tests"""
    print("🧪 Testing Budget App OAuth Setup\n")
    
    tests = [
        ("Environment Configuration", check_environment),
        ("Health Endpoint", test_health_endpoint),
        ("Login Page", test_login_page),
        ("OAuth Configuration", test_oauth_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your OAuth setup is ready.")
        print("\nNext steps:")
        print("1. Visit http://localhost:8888/login")
        print("2. Click 'Continue with Google'")
        print("3. Complete the OAuth flow")
        print("4. Access your dashboard and API")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 