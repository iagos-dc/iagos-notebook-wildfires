"""Authentication and encryption utilities for IAGOS services."""

__version__ = "0.1.0"

from .authentication import (
    get_token,
    prompt_api_key,
    prompt_token,
    build_auth_header,
)
from .encryption import (
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
