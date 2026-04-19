#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Fix Script for Common Production Issues
Automatically fixes common deployment problems
"""
import os
import sys
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    return secrets.token_urlsafe(50)

def fix_env_file():
    """Fix or create .env file with proper values"""
    print("[INFO] Fixing environment configuration...")

    env_file = Path('.env')
    env_content = {}

    # Read existing .env if it exists
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key.strip()] = value.strip()

    # Update with secure defaults
    env_content.update({
        'SECRET_KEY': generate_secret_key(),
        'DEBUG': 'True',
        'ENVIRONMENT': 'development',
        'DB_NAME': 'fusion_db',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'postgres',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'REDIS_URL': 'redis://127.0.0.1:6379/1',
        'ALLOWED_HOSTS': 'localhost,127.0.0.1',
        'CORS_ALLOWED_ORIGINS': 'http://localhost:5173,http://localhost:3000',
        'DJANGO_LOG_LEVEL': 'INFO',
    })

    # Write back to .env
    with open(env_file, 'w') as f:
        f.write("# Fusion System Administrator - Environment Configuration\n")
        f.write("# Generated automatically - update with your actual values\n\n")
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

    print("[OK] Environment configuration updated")

def install_missing_packages():
    """Install missing Python packages"""
    print("[INFO] Installing missing packages...")

    missing_packages = [
        'djangorestframework',
        'redis',
        'django-environ',
        'python-dotenv'
    ]

    for package in missing_packages:
        try:
            import subprocess
            print(f"[INFO] Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"[OK] {package} installed")
        except Exception as e:
            print(f"[ERROR] Failed to install {package}: {str(e)}")

def create_directories():
    """Create required directories"""
    print("[INFO] Creating required directories...")

    directories = ['logs', 'media', 'staticfiles']

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created {directory} directory")
        else:
            print(f"[OK] {directory} directory exists")

def main():
    """Main function"""
    print("\n=== Fusion System Administrator - Quick Fix ===\n")

    try:
        create_directories()
        fix_env_file()
        install_missing_packages()

        print("\n[SUCCESS] Common issues fixed!")
        print("\nNext steps:")
        print("1. Update .env with your actual database credentials")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py createsuperuser")
        print("4. Run: python manage.py runserver")
        print("\nFor production deployment, see DEPLOYMENT.md\n")

    except Exception as e:
        print(f"\n[ERROR] Fix failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()