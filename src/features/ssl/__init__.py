"""
SSL certificate management functionality.

This package provides functionality for managing SSL certificates,
including installation, checking, and editing.
"""

# Models
from src.features.ssl.models.ssl_config import SSLConfig, SSLType

# Core functionality
from src.features.ssl.core.installer import (
    install_selfsigned_ssl,
    install_manual_ssl,
    install_letsencrypt_ssl
)
from src.features.ssl.core.checker import check_ssl, get_ssl_status
from src.features.ssl.core.editor import edit_ssl, read_ssl_files

# Utilities
from src.features.ssl.utils.ssl_utils import (
    get_ssl_paths,
    ensure_ssl_dir,
    has_ssl_certificate,
    backup_ssl_files,
    restore_ssl_backup
)

# CLI interface
from src.features.ssl.cli.main import main as cli_main

__all__ = [
    # Models
    'SSLConfig',
    'SSLType',
    
    # Core functionality
    'install_selfsigned_ssl',
    'install_manual_ssl',
    'install_letsencrypt_ssl',
    'check_ssl',
    'get_ssl_status',
    'edit_ssl',
    'read_ssl_files',
    
    # Utilities
    'get_ssl_paths',
    'ensure_ssl_dir',
    'has_ssl_certificate',
    'backup_ssl_files',
    'restore_ssl_backup',
    
    # CLI interface
    'cli_main'
]