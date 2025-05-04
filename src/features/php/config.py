"""
PHP configuration editing functionality.

This module provides functions for editing PHP configuration files,
including php.ini and php-fpm.conf.
"""

import os
import subprocess
from typing import Optional, Dict, Any, List, Tuple

from src.common.logging import log_call, error, info
from src.common.utils.environment import env
from src.common.utils.editor import choose_editor
from src.features.php.client import init_php_client


@log_call
def edit_php_ini(domain: str) -> bool:
    """
    Open and edit the php.ini file for a website, then restart the PHP container.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if edit was successful, False otherwise
    """
    try:
        php_ini_path = os.path.join(env["SITES_DIR"], domain, "php", "php.ini")
        if not os.path.isfile(php_ini_path):
            error(f"❌ php.ini file not found for website {domain} at {php_ini_path}")
            return False

        editor = choose_editor()
        if not editor:
            error("❌ No text editor selected.")
            return False

        subprocess.run([editor, php_ini_path], check=True)

        container = init_php_client(domain)
        container.restart()
        info(f"✅ Restarted PHP container after editing php.ini for {domain}.")
        return True

    except Exception as e:
        error(f"❌ Error editing php.ini for website {domain}: {e}")
        return False


@log_call
def edit_php_fpm_pool(domain: str) -> bool:
    """
    Open and edit the php-fpm.conf file for a website, then restart the PHP container.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if edit was successful, False otherwise
    """
    try:
        fpm_conf_path = os.path.join(env["SITES_DIR"], domain, "php", "php-fpm.conf")
        if not os.path.isfile(fpm_conf_path):
            error(f"❌ php-fpm.conf file not found for website {domain} at {fpm_conf_path}")
            return False

        editor = choose_editor()
        if not editor:
            error("❌ No text editor selected.")
            return False

        subprocess.run([editor, fpm_conf_path], check=True)

        container = init_php_client(domain)
        container.restart()
        info(f"✅ Restarted PHP container after editing php-fpm.conf for {domain}.")
        return True

    except Exception as e:
        error(f"❌ Error editing php-fpm.conf for website {domain}: {e}")
        return False


@log_call
def backup_php_config(domain: str) -> Optional[str]:
    """
    Create a backup of PHP configuration files.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[str]: Backup directory path if successful, None otherwise
    """
    php_dir = os.path.join(env["SITES_DIR"], domain, "php")
    php_ini_path = os.path.join(php_dir, "php.ini")
    fpm_conf_path = os.path.join(php_dir, "php-fpm.conf")
    
    if not os.path.isfile(php_ini_path) or not os.path.isfile(fpm_conf_path):
        error(f"❌ PHP configuration files not found for website {domain}")
        return None
    
    backup_dir = os.path.join(php_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        with open(php_ini_path, "r") as src:
            with open(os.path.join(backup_dir, "php.ini.bak"), "w") as dst:
                dst.write(src.read())
                
        with open(fpm_conf_path, "r") as src:
            with open(os.path.join(backup_dir, "php-fpm.conf.bak"), "w") as dst:
                dst.write(src.read())
                
        info(f"✅ PHP configuration files backed up to: {backup_dir}")
        return backup_dir
    except Exception as e:
        error(f"❌ Error backing up PHP configuration: {e}")
        return None


@log_call
def restore_php_config_backup(domain: str) -> bool:
    """
    Restore PHP configuration files from backup.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    php_dir = os.path.join(env["SITES_DIR"], domain, "php")
    backup_dir = os.path.join(php_dir, "backup")
    php_ini_bak = os.path.join(backup_dir, "php.ini.bak")
    fpm_conf_bak = os.path.join(backup_dir, "php-fpm.conf.bak")
    
    if not os.path.isfile(php_ini_bak) or not os.path.isfile(fpm_conf_bak):
        error(f"❌ PHP configuration backups not found for website {domain}")
        return False
    
    php_ini_path = os.path.join(php_dir, "php.ini")
    fpm_conf_path = os.path.join(php_dir, "php-fpm.conf")
    
    try:
        with open(php_ini_bak, "r") as src:
            with open(php_ini_path, "w") as dst:
                dst.write(src.read())
                
        with open(fpm_conf_bak, "r") as src:
            with open(fpm_conf_path, "w") as dst:
                dst.write(src.read())
                
        # Restart PHP container to apply changes
        container = init_php_client(domain)
        container.restart()
        
        info(f"✅ PHP configuration restored from backup and container restarted")
        return True
    except Exception as e:
        error(f"❌ Error restoring PHP configuration: {e}")
        return False