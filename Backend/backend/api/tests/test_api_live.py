#!/usr/bin/env python
"""
Test live API endpoints
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

# Test with admin credentials
login_data = {
    "username": "admin",
    "password": "Admin@123"
}

print("=== Testing Live Emergency Access API ===\n")

# Login
print("[1] Logging in...")
response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    token = data.get('access')
    print(f"[OK] Got token: {token[:50]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # Test my requests
    print("\n[2] Testing my requests...")
    response = requests.get(f"{API_BASE}/emergency-access/requests/my/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        requests_data = response.json()
        print(f"[OK] Got {len(requests_data)} requests")
        for req in requests_data:
            print(f"  - {req.get('role')}: {req.get('status')}")
    else:
        print(f"[ERROR] {response.text[:200]}")

    # Test pending requests
    print("\n[3] Testing pending requests...")
    response = requests.get(f"{API_BASE}/emergency-access/requests/pending/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        pending_data = response.json()
        print(f"[OK] Got {len(pending_data)} pending requests")
        for req in pending_data:
            print(f"  - {req.get('user')}: {req.get('role')}")
    else:
        print(f"[ERROR] {response.text[:200]}")

else:
    print(f"[ERROR] Login failed: {response.text}")

print("\n=== API TEST COMPLETE ===")
