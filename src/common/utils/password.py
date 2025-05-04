"""
Password generation utilities.

This module provides secure password generation functionality
for creating strong, random passwords.
"""

from password_generator import PasswordGenerator
from src.common.logging import log_call


# Configure password generator with secure defaults
pwo = PasswordGenerator()
pwo.minlen = 16       # Minimum length
pwo.maxlen = 26       # Maximum length
pwo.minnumbers = 2    # Minimum number of digits
pwo.minschars = 3     # Minimum number of special characters
pwo.excludeschars = "!$%^&*()_+<>?:{}[]|.,;~`#@'"  # Exclude problematic special chars


@log_call
def strong_password() -> str:
    """
    Generate a secure, random password.
    
    Returns:
        A strong random password string
    """
    return pwo.generate()