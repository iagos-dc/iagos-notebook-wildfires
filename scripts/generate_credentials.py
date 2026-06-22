#!/usr/bin/env python3
"""
Script to generate encrypted credentials for IAGOS authentication.

Usage:
    python scripts/generate_credentials.py

The script will prompt for:
1. Your IAGOS/AERIS email
2. Your IAGOS/AERIS password
3. A master password for encryption

The output should be copied into src/fr/aeris/iagos/auth/authentication.py
"""

from fr.aeris.iagos.auth import encrypt_credentials
import getpass

def main():
    print("=" * 60)
    print("IAGOS Authentication - Generate Encrypted Credentials")
    print("=" * 60)
    print()
    print("This script will encrypt your IAGOS/AERIS credentials.")
    print("The encrypted values can be safely stored in the code.")
    print()

    # Get credentials
    user_email = input("Enter your IAGOS/AERIS email: ").strip()
    user_password = getpass.getpass("Enter your IAGOS/AERIS password: ")
    master_password = getpass.getpass("Enter a master password for encryption: ")
    master_password_confirm = getpass.getpass("Confirm master password: ")

    if master_password != master_password_confirm:
        print("\n❌ Error: Master passwords do not match!")
        return 1

    print("\n🔒 Encrypting credentials...")

    try:
        encrypted_email, encrypted_password = encrypt_credentials(
            user_email, user_password, master_password
        )

        print("\n✅ Credentials encrypted successfully!")
        print("\n" + "=" * 60)
        print("Copy these lines into:")
        print("src/fr/aeris/iagos/auth/authentication.py")
        print("(around lines 25-26)")
        print("=" * 60)
        print()
        print(f'ENCRYPTED_USER_EMAIL = "{encrypted_email}"')
        print(f'ENCRYPTED_USER_PASSWORD = "{encrypted_password}"')
        print()
        print("=" * 60)
        print("IMPORTANT: Save your master password securely!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
