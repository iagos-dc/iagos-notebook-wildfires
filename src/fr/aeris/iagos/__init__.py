"""IAGOS data services package."""
__version__ = "0.1.0"

# Import auth functions for easier access
from .auth import (
    get_token,
    prompt_api_key,
    prompt_token,
    build_auth_header,
    jasypt_encrypt,
    jasypt_decrypt,
    encrypt_credentials,
)

__all__ = [
    "get_token",
    "prompt_api_key",
    "prompt_token",
    "build_auth_header",
    "jasypt_encrypt",
    "jasypt_decrypt",
    "encrypt_credentials",
]
