"""
PHP configuration management functionality.

This module provides functions for managing PHP configuration files,
including editing, backing up, and restoring configurations.
"""

import os
import shutil
import tempfile
from typing import Optional, Dict, Any, List
import configparser
from pathlib import Path

from src.common.logging import log_call, debug, error, info, warn
from src.common.utils.environment import env
from src.features.php.client import init_php_client
from src.features.php.utils import get_php_container_name


# Default PHP configuration values
DEFAULT_PHP_INI = {
    'memory_limit': '512M',
    'post_max_size': '128M',
    'upload_max_filesize': '128M',
    'max_execution_time': '300',
    'max_input_time': '300',
    'display_errors': 'Off',
    'log_errors': 'On',
    'error_log': '/var/www/logs/php_error.log',
    'date.timezone': 'UTC',
    'opcache.enable': '1',
    'opcache.memory_consumption': '256',
    'opcache.max_accelerated_files': '10000',
    'opcache.validate_timestamps': '1',
    'opcache.revalidate_freq': '60'
}

# Default PHP-FPM configuration values
DEFAULT_PHP_FPM = {
    'user': 'www-data',
    'group': 'www-data',
    'listen': '9000',
    'pm': 'dynamic',
    'pm.max_children': '50',
    'pm.start_servers': '5',
    'pm.min_spare_servers': '5',
    'pm.max_spare_servers': '35',
    'pm.process_idle_timeout': '10s',
    'pm.max_requests': '1000',
    'slowlog': '/var/www/logs/php_slow.log',
    'request_slowlog_timeout': '10',
    'request_terminate_timeout': '60'
}


def validate_php_ini(config: Dict[str, str]) -> bool:
    """
    Validate PHP INI configuration values.
    
    Args:
        config: Dictionary of PHP INI settings
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Validate memory values
        memory_settings = ['memory_limit', 'post_max_size', 'upload_max_filesize']
        for setting in memory_settings:
            if setting in config:
                value = config[setting].upper()
                if not value.endswith(('K', 'M', 'G')):
                    error(f"Invalid memory value for {setting}: {value}")
                    return False
                    
        # Validate numeric values
        numeric_settings = [
            'max_execution_time', 'max_input_time',
            'opcache.memory_consumption', 'opcache.max_accelerated_files',
            'opcache.revalidate_freq'
        ]
        for setting in numeric_settings:
            if setting in config:
                try:
                    int(config[setting])
                except ValueError:
                    error(f"Invalid numeric value for {setting}: {config[setting]}")
                    return False
                    
        # Validate boolean values
        boolean_settings = ['display_errors', 'log_errors', 'opcache.enable', 'opcache.validate_timestamps']
        for setting in boolean_settings:
            if setting in config:
                value = config[setting].lower()
                if value not in ('on', 'off', '1', '0', 'true', 'false'):
                    error(f"Invalid boolean value for {setting}: {value}")
                    return False
                    
        return True
    except Exception as e:
        error(f"Error validating PHP INI configuration: {e}")
        return False


def validate_php_fpm(config: Dict[str, str]) -> bool:
    """
    Validate PHP-FPM configuration values.
    
    Args:
        config: Dictionary of PHP-FPM settings
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Validate process manager settings
        if 'pm' in config and config['pm'] not in ('static', 'dynamic', 'ondemand'):
            error(f"Invalid process manager: {config['pm']}")
            return False
            
        # Validate numeric values
        numeric_settings = [
            'pm.max_children', 'pm.start_servers',
            'pm.min_spare_servers', 'pm.max_spare_servers',
            'pm.max_requests', 'request_slowlog_timeout',
            'request_terminate_timeout'
        ]
        for setting in numeric_settings:
            if setting in config:
                try:
                    int(config[setting])
                except ValueError:
                    error(f"Invalid numeric value for {setting}: {config[setting]}")
                    return False
                    
        # Validate time values
        time_settings = ['pm.process_idle_timeout']
        for setting in time_settings:
            if setting in config:
                value = config[setting].lower()
                if not value.endswith(('s', 'm', 'h')):
                    error(f"Invalid time value for {setting}: {value}")
                    return False
                    
        return True
    except Exception as e:
        error(f"Error validating PHP-FPM configuration: {e}")
        return False


@log_call
def edit_php_ini(domain: str) -> bool:
    """
    Edit PHP INI configuration file.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if edit was successful, False otherwise
    """
    try:
        php_dir = os.path.join(env["SITES_DIR"], domain, "php")
        php_ini_path = os.path.join(php_dir, "php.ini")
        
        if not os.path.isfile(php_ini_path):
            error(f"❌ PHP INI file not found: {php_ini_path}")
            return False
            
        # Create backup
        backup_path = backup_php_config(domain)
        if not backup_path:
            return False
            
        # Create temporary file for editing
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            with open(php_ini_path, 'r') as f:
                temp_file.write(f.read())
            temp_path = temp_file.name
            
        # Open editor
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {temp_path}")
        
        # Validate and apply changes
        config = configparser.ConfigParser()
        config.read(temp_path)
        
        # Convert to dictionary for validation
        config_dict = {}
        for section in config.sections():
            for key, value in config.items(section):
                config_dict[key] = value
                
        if not validate_php_ini(config_dict):
            warn("⚠️ Configuration validation failed. Restoring backup...")
            restore_php_config_backup(domain)
            return False
            
        # Apply changes
        shutil.move(temp_path, php_ini_path)
        
        # Restart PHP container
        container = init_php_client(domain)
        container.restart()
        
        info(f"✅ PHP INI configuration updated for {domain}")
        return True
        
    except Exception as e:
        error(f"❌ Error editing PHP INI: {e}")
        return False


@log_call
def edit_php_fpm_pool(domain: str) -> bool:
    """
    Edit PHP-FPM pool configuration file.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if edit was successful, False otherwise
    """
    try:
        php_dir = os.path.join(env["SITES_DIR"], domain, "php")
        fpm_conf_path = os.path.join(php_dir, "php-fpm.conf")
        
        if not os.path.isfile(fpm_conf_path):
            error(f"❌ PHP-FPM configuration file not found: {fpm_conf_path}")
            return False
            
        # Create backup
        backup_path = backup_php_config(domain)
        if not backup_path:
            return False
            
        # Create temporary file for editing
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            with open(fpm_conf_path, 'r') as f:
                temp_file.write(f.read())
            temp_path = temp_file.name
            
        # Open editor
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {temp_path}")
        
        # Validate and apply changes
        config = configparser.ConfigParser()
        config.read(temp_path)
        
        # Convert to dictionary for validation
        config_dict = {}
        for section in config.sections():
            for key, value in config.items(section):
                config_dict[key] = value
                
        if not validate_php_fpm(config_dict):
            warn("⚠️ Configuration validation failed. Restoring backup...")
            restore_php_config_backup(domain)
            return False
            
        # Apply changes
        shutil.move(temp_path, fpm_conf_path)
        
        # Restart PHP container
        container = init_php_client(domain)
        container.restart()
        
        info(f"✅ PHP-FPM configuration updated for {domain}")
        return True
        
    except Exception as e:
        error(f"❌ Error editing PHP-FPM configuration: {e}")
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


@log_call
def create_default_php_config(domain: str, php_version: str) -> bool:
    """
    Create default PHP configuration files for a website.
    
    Args:
        domain: Website domain name
        php_version: PHP version to use
        
    Returns:
        bool: True if creation was successful, False otherwise
    """
    try:
        php_dir = os.path.join(env["SITES_DIR"], domain, "php")
        os.makedirs(php_dir, exist_ok=True)
        
        # Create php.ini
        php_ini_path = os.path.join(php_dir, "php.ini")
        with open(php_ini_path, "w") as f:
            f.write("[PHP]\n")
            for key, value in DEFAULT_PHP_INI.items():
                f.write(f"{key} = {value}\n")
                
        # Create php-fpm.conf
        fpm_conf_path = os.path.join(php_dir, "php-fpm.conf")
        with open(fpm_conf_path, "w") as f:
            f.write("[www]\n")
            for key, value in DEFAULT_PHP_FPM.items():
                f.write(f"{key} = {value}\n")
                
        info(f"✅ Created default PHP configuration for {domain}")
        return True
        
    except Exception as e:
        error(f"❌ Error creating default PHP configuration: {e}")
        return False