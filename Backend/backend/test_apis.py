import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

print("=" * 60)
print("TESTING FUSION SYSTEM ADMINISTRATOR - API ENDPOINTS")
print("=" * 60)

# Test 1: Health check
print("\n[Test 1] Health Check")
try:
    response = requests.get(f"{BASE_URL}/auth/login/")
    print(f"✓ Login endpoint accessible - Status: {response.status_code}")
except Exception as e:
    print(f"✗ Failed to reach server: {e}")

# Test 2: Login with admin credentials
print("\n[Test 2] Admin Login")
login_data = {
    "username": "admin",
    "password": "Admin@123"
}
try:
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✓ Login successful!")
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        print(f"  Access Token received: {bool(access_token)}")
        print(f"  Refresh Token received: {bool(refresh_token)}")
    else:
        print(f"✗ Login failed: {response.text}")
        access_token = None
except Exception as e:
    print(f"✗ Login error: {e}")
    access_token = None

# Test 3: Token Refresh
print("\n[Test 3] Token Refresh")
if access_token:
    try:
        refresh_response = requests.post(f"{BASE_URL}/auth/token/refresh/", json={
            "refresh": refresh_token
        })
        print(f"Status Code: {refresh_response.status_code}")
        if refresh_response.status_code == 200:
            print("✓ Token refresh successful!")
        else:
            print(f"✗ Token refresh failed: {refresh_response.text}")
    except Exception as e:
        print(f"✗ Token refresh error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 4: Get Current User
print("\n[Test 4] Get Current User")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print("✓ Current user retrieved!")
            print(f"  Username: {user_data.get('username')}")
            print(f"  Email: {user_data.get('email')}")
        else:
            print(f"✗ Failed to get current user: {response.text}")
    except Exception as e:
        print(f"✗ Get current user error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 5: Get All Users
print("\n[Test 5] Get All Users (List)")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/users/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Users list retrieved!")
            print(f"  Total count: {data.get('count', 0)}")
            print(f"  Results in page: {len(data.get('results', []))}")
        else:
            print(f"✗ Failed to get users: {response.text}")
    except Exception as e:
        print(f"✗ Get users error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 6: Get Departments
print("\n[Test 6] Get Departments")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/departments/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Departments retrieved!")
            print(f"  Number of departments: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"✗ Failed to get departments: {response.text}")
    except Exception as e:
        print(f"✗ Get departments error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 7: Get Roles
print("\n[Test 7] Get Roles")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/view-roles/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Roles retrieved!")
            print(f"  Number of roles: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"✗ Failed to get roles: {response.text}")
    except Exception as e:
        print(f"✗ Get roles error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 8: Get Audit Logs
print("\n[Test 8] Get Audit Logs")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/audit-logs/", headers=headers, params={"page": 1, "page_size": 10})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Audit logs retrieved!")
            print(f"  Total logs: {data.get('count', 0)}")
            print(f"  Logs in page: {len(data.get('results', []))}")
        else:
            print(f"✗ Failed to get audit logs: {response.text}")
    except Exception as e:
        print(f"✗ Get audit logs error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 9: Get Programmes
print("\n[Test 9] Get Programmes")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/programmes/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Programmes retrieved!")
            print(f"  Number of programmes: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"✗ Failed to get programmes: {response.text}")
    except Exception as e:
        print(f"✗ Get programmes error: {e}")
else:
    print("⊗ Skipped (no access token)")

# Test 10: Get Batches
print("\n[Test 10] Get Batches")
if access_token:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/batches/", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Batches retrieved!")
            print(f"  Number of batches: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"✗ Failed to get batches: {response.text}")
    except Exception as e:
        print(f"✗ Get batches error: {e}")
else:
    print("⊗ Skipped (no access token)")

print("\n" + "=" * 60)
print("API TESTING COMPLETE")
print("=" * 60)
