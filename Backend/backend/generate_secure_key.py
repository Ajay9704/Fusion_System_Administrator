#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate Secure SECRET_KEY for Django
Creates a cryptographically secure secret key for production use
"""
import secrets
import sys

def generate_secret_key(length=50):
    """Generate a secure Django SECRET_KEY"""
    # Generate a longer, more secure key
    return secrets.token_urlsafe(length)

def main():
    print("Django SECRET_KEY Generator")
    print("=" * 40)

    # Generate key
    secret_key = generate_secret_key(50)

    print(f"\nGenerated SECRET_KEY (50 characters):")
    print(f"{secret_key}")
    print(f"\nLength: {len(secret_key)} characters")

    # Test key strength
    has_upper = any(c.isupper() for c in secret_key)
    has_lower = any(c.islower() for c in secret_key)
    has_digit = any(c.isdigit() for c in secret_key)
    has_special = any(c in '-._~' for c in secret_key)

    print(f"\nKey Strength Analysis:")
    print(f"- Uppercase letters: {'✓' if has_upper else '✗'}")
    print(f"- Lowercase letters: {'✓' if has_lower else '✗'}")
    print(f"- Digits: {'✓' if has_digit else '✗'}")
    print(f"- Special characters: {'✓' if has_special else '✗'}")

    if all([has_upper, has_lower, has_digit, has_special]):
        print(f"\n✓ Strong key generated")
    else:
        print(f"\n✗ Key could be stronger")

    print(f"\nAdd this to your .env file:")
    print(f"SECRET_KEY={secret_key}")

    return 0

if __name__ == "__main__":
    sys.exit(main())