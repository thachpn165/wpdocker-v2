"""
SSL utility functions.

This package provides utility functions for working with SSL certificates.
"""

import os
from typing import Optional, List, Tuple

from src.common.logging import log_call
from src.common.utils.environment import env


@log_call
def get_ssl_paths(domain: str) -> Tuple[str, str, str]:
    """
    Get paths to SSL certificate directories and files.
    
    Args:
        domain: Website domain name
        
    Returns:
        Tuple[str, str, str]: SSL directory, certificate path, and key path
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")
    
    return ssl_dir, cert_path, key_path


@log_call
def ensure_ssl_dir(domain: str) -> str:
    """
    Ensure SSL directory exists for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        str: SSL directory path
    """
    ssl_dir, _, _ = get_ssl_paths(domain)
    os.makedirs(ssl_dir, exist_ok=True)
    return ssl_dir


@log_call
def has_ssl_certificate(domain: str) -> bool:
    """
    Check if a domain has SSL certificate files.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if certificate files exist, False otherwise
    """
    _, cert_path, key_path = get_ssl_paths(domain)
    return os.path.isfile(cert_path) and os.path.isfile(key_path)