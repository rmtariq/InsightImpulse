#!/usr/bin/env python3
"""
Test Threads Session ID validity
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

THREADS_SESSION_ID = os.getenv('THREADS_SESSION_ID')

print("🔐 Testing Threads Session ID...")
print(f"Session ID: {THREADS_SESSION_ID[:30]}...{THREADS_SESSION_ID[-20:]}")
print()

# Test 1: Check if session ID format is correct
if not THREADS_SESSION_ID or len(THREADS_SESSION_ID) < 50:
    print("❌ Session ID too short or missing!")
    print(f"   Length: {len(THREADS_SESSION_ID) if THREADS_SESSION_ID else 0}")
    exit(1)

print("✅ Session ID length looks good")
print(f"   Length: {len(THREADS_SESSION_ID)}")
print()

# Test 2: Try to make a simple request to Threads
print("🌐 Testing connection to Threads...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Cookie': f'sessionid={THREADS_SESSION_ID}'
}

try:
    response = requests.get('https://www.threads.net/', headers=headers, timeout=10)
    print(f"✅ Response status: {response.status_code}")
    
    # Check if we're logged in
    if 'login' in response.url.lower():
        print("❌ Session INVALID - Redirected to login page!")
        print(f"   URL: {response.url}")
    elif response.status_code == 200:
        print("✅ Session appears VALID - No redirect to login")
        
        # Check for user data in response
        if 'ds_user_id' in response.text or 'instagram' in response.text:
            print("✅ User data found in response")
        else:
            print("⚠️ No user data found - session might be partially valid")
    else:
        print(f"⚠️ Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("📋 DIAGNOSIS:")
print()

if THREADS_SESSION_ID and len(THREADS_SESSION_ID) > 50:
    print("✅ Session ID format: OK")
else:
    print("❌ Session ID format: INVALID")
    print()
    print("🔧 HOW TO FIX:")
    print("1. Go to https://www.threads.net and log in")
    print("2. Press F12 → Application → Cookies → threads.net")
    print("3. Find 'sessionid' cookie")
    print("4. Copy ENTIRE value (might be very long!)")
    print("5. Update .env file with: THREADS_SESSION_ID=<full_value>")
    exit(1)

print()
print("🎯 NEXT STEPS:")
print("If session is valid, try running:")
print("   python fetch_threads_replies_from_csv.py")
print()
print("If still failing, the actor might have other requirements!")
