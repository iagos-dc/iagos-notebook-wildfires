#!/usr/bin/env python3
"""
Script to generate encrypted credentials for IAGOS authentication.

Usage:
    python src/fr/aeris/auth/generate_credentials.py

The script will prompt for your AERIS credentials and a master password,
then print the encrypted values to copy into the .env file at the project root.
"""

import getpass
from fr.aeris.auth import encrypt_credentials


def main():
    print("=" * 60)
    print("IAGOS Authentication - Generate Encrypted Credentials")
    print("=" * 60)
    print()
    print("This script will encrypt your IAGOS/AERIS credentials.")
    print("The encrypted values must be stored in the .env file.")
    print()

    user_email = input("Enter your IAGOS/AERIS email: ").strip()
    user_password = getpass.getpass("Enter your IAGOS/AERIS password: ")
    master_password = getpass.getpass("Enter a master password for encryption: ")
    master_password_confirm = getpass.getpass("Confirm master password: ")

    if master_password != master_password_confirm:
        print("\nError: Master passwords do not match!")
        return 1

    print("\nEncrypting credentials...")

    try:
        encrypted_email, encrypted_password = encrypt_credentials(
            user_email, user_password, master_password
        )

        print("\nCredentials encrypted successfully!")
        print("\n" + "=" * 60)
        print("Copy these lines into your .env file (project root):")
        print("=" * 60)
        print()
        print(f'AERIS_ENCRYPTED_EMAIL="{encrypted_email}"')
        print(f'AERIS_ENCRYPTED_PASSWORD="{encrypted_password}"')
        print(f'AERIS_MASTER_PASSWORD="{master_password}"')
        print()
        print("=" * 60)
        print("WARNING: Keep your .env file secret — never commit it to git!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
