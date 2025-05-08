"""
SSL certificate editing functionality.

This module provides functions for editing SSL certificates installed on websites.
"""

import os
import subprocess
from typing import Optional, Tuple

from src.common.logging import log_call, info, error
from src.common.utils.environment import env
from src.common.utils.editor import choose_editor
from src.features.website.utils import get_site_config
from src.features.webserver.webserver_reload import WebserverReload


@log_call
def edit_ssl(domain: str) -> bool:
    """
    Open SSL certificate and key files in an editor for manual editing.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if files were opened successfully, False otherwise
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"No configuration found for website {domain}.")
        return False

    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.exists(cert_path):
        error(f"Certificate file cert.crt not found at {cert_path}")
        return False
    if not os.path.exists(key_path):
        error(f"Private key file priv.key not found at {key_path}")
        return False

    editor = choose_editor()
    if not editor:
        error("No text editor selected.")
        return False

    try:
        info("Opening certificate and private key files for editing...")
        subprocess.call([editor, cert_path])
        subprocess.call([editor, key_path])
        
        info("Files have been edited. Reloading NGINX configuration...")
        WebserverReload.webserver_reload()
        return True
    except Exception as e:
        error(f"Error editing SSL files: {e}")
        return False


@log_call
def read_ssl_files(domain: str) -> Optional[Tuple[str, str]]:
    """
    Read the contents of SSL certificate and key files.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[Tuple[str, str]]: (certificate, key) content if successful, None otherwise
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        error(f"SSL files not found for domain {domain}")
        return None

    try:
        with open(cert_path, "r") as f:
            cert_content = f.read()
        with open(key_path, "r") as f:
            key_content = f.read()
        
        return (cert_content, key_content)
    except Exception as e:
        error(f"Error reading SSL files: {e}")
        return None


@log_call
def backup_ssl_files(domain: str) -> Optional[str]:
    """
    Create a backup of SSL certificate and key files.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[str]: Backup directory path if successful, None otherwise
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        error(f"SSL files not found for domain {domain}")
        return None

    backup_dir = os.path.join(ssl_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    backup_cert_path = os.path.join(backup_dir, "cert.crt.bak")
    backup_key_path = os.path.join(backup_dir, "priv.key.bak")

    try:
        with open(cert_path, "r") as src:
            with open(backup_cert_path, "w") as dst:
                dst.write(src.read())

        with open(key_path, "r") as src:
            with open(backup_key_path, "w") as dst:
                dst.write(src.read())

        info(f"SSL files backed up to: {backup_dir}")
        return backup_dir
    except Exception as e:
        error(f"Error backing up SSL files: {e}")
        return None


@log_call
def restore_ssl_backup(domain: str) -> bool:
    """
    Restore SSL certificate and key files from backup.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    backup_dir = os.path.join(ssl_dir, "backup")
    backup_cert_path = os.path.join(backup_dir, "cert.crt.bak")
    backup_key_path = os.path.join(backup_dir, "priv.key.bak")

    if not os.path.exists(backup_cert_path) or not os.path.exists(backup_key_path):
        error(f"SSL backup files not found for domain {domain}")
        return False

    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    try:
        with open(backup_cert_path, "r") as src:
            with open(cert_path, "w") as dst:
                dst.write(src.read())

        with open(backup_key_path, "r") as src:
            with open(key_path, "w") as dst:
                dst.write(src.read())

        info(f"SSL files restored from backup")
        WebserverReload.webserver_reload()
        return True
    except Exception as e:
        error(f"Error restoring SSL files: {e}")
        return False