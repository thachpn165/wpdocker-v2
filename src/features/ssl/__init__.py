"""
SSL certificate management functionality.

This package provides functionality for managing SSL certificates,
including installation, checking, and editing.
"""

# Core installation functionality
from src.features.ssl.installer import (
    install_selfsigned_ssl,
    install_manual_ssl,
    install_letsencrypt_ssl,
    edit_ssl_cert
)

# Certificate checking
from src.features.ssl.checker import check_ssl, get_ssl_status

# Certificate editing
from src.features.ssl.editor import (
    edit_ssl,
    read_ssl_files,
    backup_ssl_files,
    restore_ssl_backup
)

# Utilities
from src.features.ssl.utils import (
    get_ssl_paths,
    ensure_ssl_dir,
    has_ssl_certificate
)

# CLI interfaces
from src.features.ssl.cli import (
    cli_install_ssl,
    cli_check_ssl,
    cli_edit_ssl
)

__all__ = [
    # Core installation functionality
    'install_selfsigned_ssl',
    'install_manual_ssl',
    'install_letsencrypt_ssl',
    'edit_ssl_cert',
    
    # Certificate checking
    'check_ssl',
    'get_ssl_status',
    
    # Certificate editing
    'edit_ssl',
    'read_ssl_files',
    'backup_ssl_files',
    'restore_ssl_backup',
    
    # Utilities
    'get_ssl_paths',
    'ensure_ssl_dir',
    'has_ssl_certificate',
    
    # CLI interfaces
    'cli_install_ssl',
    'cli_check_ssl',
    'cli_edit_ssl'
]