"""
Validation utilities for checking input values.

This module provides validation functions for domains, system
architecture, file paths, and other common validation needs.
"""

import os
import re
import platform
from typing import Optional

from src.common.logging import debug


def is_valid_domain(domain: str) -> bool:
    """
    Validate a domain name.
    
    Checks:
    - Not empty
    - Maximum 254 characters
    - No whitespace
    - Doesn't start or end with a period
    - Doesn't start with www.
    - Has valid format like sub.example.com
    
    Args:
        domain: The domain name to validate
        
    Returns:
        True if domain is valid, False otherwise
    """
    if not domain:
        return False
    if len(domain) > 254:
        return False
    if domain.startswith('.') or domain.endswith('.'):
        return False
    if domain.startswith('www.'):
        return False
    if ' ' in domain:
        return False

    domain_regex = re.compile(
        r"^(?!-)([a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,}$"
    )
    return bool(domain_regex.match(domain))


def is_arm() -> bool:
    """
    Check if the system architecture is ARM.
    
    Returns:
        True if system is ARM-based, False otherwise
    """
    arch = platform.machine()
    arm = arch.startswith('arm') or arch.startswith('aarch64')
    if arm:
        debug(f"⚠️ ARM system detected: {arch}")
        return True
    return False


def validate_directory(directory_path: str) -> bool:
    """
    Validate a directory exists and create it if it doesn't.
    
    Args:
        directory_path: Path to the directory to check/create
        
    Returns:
        True if directory exists or was created successfully
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
            debug(f"✅ Created directory: {directory_path}")
            return True
        except Exception as e:
            debug(f"❌ Cannot create directory {directory_path}: {e}")
            return False
    return True


def validate_file_path(file_path: str, create_parent: bool = True) -> bool:
    """
    Validate a file path and optionally create parent directories.
    
    Args:
        file_path: Path to the file
        create_parent: Whether to create parent directories if they don't exist
        
    Returns:
        True if the file exists or parent directories were created successfully
    """
    if os.path.exists(file_path):
        return True
        
    if create_parent:
        parent_dir = os.path.dirname(file_path)
        return validate_directory(parent_dir)
    
    return False