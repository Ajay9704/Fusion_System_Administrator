#!/usr/bin/env python
"""
Simple script to test JWT authentication
"""
import requests
import json

# Test credentials
test_username = "TESTADMIN"
test_password = "hello123"

# Login endpoint
login_url = "http://localhost:8000/api/auth/login/"
test_roles_url = "http://localhost:8000/api/view-roles/"

def test_login():
    print("Testing login...")
    try:
        response = requests.post(login_url, json={
            'username': test_username,
            'password': test_password
        })

        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            refresh_token = data.get('refresh')

            print(f"Access token: {access_token[:50]}...")
            print(f"Refresh token: {refresh_token[:50]}...")

            # Test authenticated request
            headers = {'Authorization': f'Bearer {access_token}'}
            roles_response = requests.get(test_roles_url, headers=headers)

            print(f"Roles response status: {roles_response.status_code}")
            print(f"Roles response: {roles_response.text}")

            return access_token
        else:
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_login()