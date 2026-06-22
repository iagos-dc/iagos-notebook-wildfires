"""
Authentication module for IAGOS data services.

This module provides authentication methods for accessing IAGOS data services
using either API keys or SSO tokens via AERIS Keycloak.
"""

import os
from keycloak import KeycloakOpenID

# Support both package import and direct script execution
try:
    from .encryption import jasypt_decrypt
except ImportError:
    from fr.aeris.iagos.auth.encryption import jasypt_decrypt


# Plain text credentials (for development only - use None for production)
USER_EMAIL = None  # Set to your email or None to use encrypted credentials
USER_PASSWORD = None  # Set to your password or None to use encrypted credentials

# Encrypted credentials (use jasypt_encrypt to generate these)
# To encrypt: from fr.aeris.iagos.auth import encrypt_credentials
# encrypted_email, encrypted_password = encrypt_credentials("your_email@example.com", "your_password", "master_password")
ENCRYPTED_USER_EMAIL = "R46Nsep7kb5CgKjY0p4JyYdU3Lp/9GWx/ZtBzySkEOKy1hCY9Acr8A=="  # Replace with encrypted email after generation
ENCRYPTED_USER_PASSWORD = "+irIiIzUnhEgz2Q6h3AjsqopQBeLJle7R0jZ6TklW9o=" # Replace with encrypted password after generation


def get_token():
    """
    Retrieve token using Keycloak SSO authentication for IAGOS.

    This method uses the AERIS Keycloak SSO for authentication.

    If USER_EMAIL and USER_PASSWORD are set (not None), they will be used directly.
    Otherwise, encrypted credentials will be decrypted using a master password.
    The master password is obtained from (in order of priority):
    1. Environment variable IAGOS_MASTER_PASSWORD
    2. Interactive prompt

    Returns:
        dict: Token dictionary from Keycloak containing access_token, expires_in, etc.

    Examples:
        >>> token = get_token()
        Please enter master password for decryption: ***
        >>> access_token = token['access_token']
    """
    # Check if plain text credentials are provided
    if USER_EMAIL is not None and USER_PASSWORD is not None:
        user_email = USER_EMAIL
        user_password = USER_PASSWORD
    else:
        # Use encrypted credentials
        from getpass import getpass

        # Try to get master password from environment variable first
        master_password = os.environ.get('IAGOS_MASTER_PASSWORD')

        # If not in environment, prompt for it
        if master_password is None:
            master_password = getpass("Please enter master password for decryption: ")

        # Decrypt credentials
        if ENCRYPTED_USER_EMAIL is None or ENCRYPTED_USER_PASSWORD is None:
            raise ValueError(
                "Encrypted credentials not configured. Please set ENCRYPTED_USER_EMAIL and "
                "ENCRYPTED_USER_PASSWORD in authentication.py, or set USER_EMAIL and USER_PASSWORD "
                "for development use."
            )

        user_email = jasypt_decrypt(ENCRYPTED_USER_EMAIL, master_password)
        user_password = jasypt_decrypt(ENCRYPTED_USER_PASSWORD, master_password)

    keycloak_openid = KeycloakOpenID(
        server_url="https://sso.aeris-data.fr/auth/",
        client_id="aeris-public",
        realm_name="aeris",
        verify=True
    )
    token = keycloak_openid.token(user_email, user_password)
    return token


def prompt_api_key() -> str:
    """
    Prompt user to enter their IAGOS/AERIS API key.

    API keys can be obtained at: https://www.sedoo.fr/aeris-key-manager/

    Returns:
        str: The API key entered by the user.
    """
    key = input("Please enter your IAGOS/AERIS API Key (get one at https://www.sedoo.fr/aeris-key-manager/): ")
    return key


def prompt_token() -> str:
    """
    Prompt user to enter their IAGOS/AERIS SSO token.

    Returns:
        str: The SSO token entered by the user.
    """
    token = input("Please enter your IAGOS/AERIS SSO token: ")
    return token


def build_auth_header(method: str, credential: str) -> dict:
    """
    Build authentication header for IAGOS API requests.

    Args:
        method: Authentication method, either 'key' or 'token'.
        credential: The API key or token credential.

    Returns:
        dict: HTTP headers dictionary with authorization and accept headers.

    Raises:
        ValueError: If method is not 'key' or 'token'.

    Examples:
        >>> api_key = "my-api-key-123"
        >>> headers = build_auth_header('key', api_key)
        >>> headers
        {'Authorization': 'X-API-Key my-api-key-123', 'Accept': '*/*'}

        >>> token = "eyJhbGciOiJSUzI1NiIsInR5cCI..."
        >>> headers = build_auth_header('token', token)
        >>> headers
        {'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI...', 'Accept': '*/*'}
    """
    if method == 'key':
        auth_value = f'X-API-Key {credential}'
    elif method == 'token':
        auth_value = f'Bearer {credential}'
    else:
        raise ValueError(f"Invalid authentication method: '{method}'. Must be 'key' or 'token'.")

    return {
        'Authorization': auth_value,
        'Accept': '*/*'
    }
