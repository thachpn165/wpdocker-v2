"""
Cryptographic utilities for data security.

This module provides functions for securely encrypting and decrypting
sensitive data using a secret key stored in a file.
"""

import base64
import os
from pathlib import Path
from typing import Optional

from src.common.logging import log_call
from src.common.utils.environment import env_required


@log_call
def get_secret_file_path() -> str:
    """
    Get the path to the secret key file.
    
    Returns:
        Path to the secret key file
    """
    env = env_required(["INSTALL_DIR"])
    return os.path.join(env["INSTALL_DIR"], ".secret_key")


@log_call
def get_secret_key() -> str:
    """
    Get the secret key, creating it if it doesn't exist.
    
    Returns:
        Secret key as a string
    """
    secret_file = get_secret_file_path()
    if not os.path.exists(secret_file):
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        with open(secret_file, "w") as f:
            f.write(key)
        print("🔐 Created new .secret_key")
    else:
        key = Path(secret_file).read_text().strip()
    return key


@log_call
def encrypt(plain_text: str) -> str:
    """
    Encrypt a plaintext string.
    
    Args:
        plain_text: The text to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    key = get_secret_key()
    combined = f"{key}:{plain_text}"
    return base64.b64encode(combined.encode()).decode()


@log_call
def decrypt(encoded_text: str) -> str:
    """
    Decrypt an encrypted string.
    
    Args:
        encoded_text: The encrypted text to decrypt
        
    Returns:
        The decrypted plaintext
        
    Raises:
        ValueError: If decryption fails or key doesn't match
    """
    key = get_secret_key()
    try:
        decoded = base64.b64decode(encoded_text.encode()).decode()
    except Exception as e:
        raise ValueError(f"Base64 decode error: {str(e)}")

    if ":" not in decoded:
        raise ValueError("Invalid decryption string format.")

    try:
        stored_key, plain = decoded.split(":", 1)
    except ValueError:
        raise ValueError("Cannot separate key and data from decryption string.")

    if stored_key != key:
        raise ValueError("Decryption key doesn't match current .secret_key.")

    return plain