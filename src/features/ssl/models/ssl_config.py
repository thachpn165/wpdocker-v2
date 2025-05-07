"""
SSL configuration model.

This module defines the data structures for SSL configuration.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class SSLType(Enum):
    """SSL certificate types."""
    SELFSIGNED = "selfsigned"
    MANUAL = "manual"
    LETSENCRYPT = "letsencrypt"


@dataclass
class SSLConfig:
    """SSL configuration data structure."""
    type: SSLType
    domain: str
    cert_path: str
    key_path: str
    chain_path: Optional[str] = None
    auto_renew: bool = False
    email: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None 