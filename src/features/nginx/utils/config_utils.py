"""
NGINX configuration utilities.

This module provides functions for managing NGINX configuration files,
including parsing, generating, and validating configs.
"""
import os
import re
from typing import Dict, List, Optional, Tuple

from src.common.logging import debug, info, warn, error, log_call
from src.common.utils.environment import env


@log_call
def get_config_path(config_type: str, name: Optional[str] = None) -> str:
    """
    Get the path to a configuration file based on type and name.
    
    Args:
        config_type: Type of configuration ('cache', 'globals', 'waf', 'main')
        name: Name of the specific configuration file (without extension)
        
    Returns:
        str: Path to the configuration file
    """
    nginx_dir = os.path.dirname(os.path.dirname(__file__))
    configs_dir = os.path.join(nginx_dir, "configs")
    
    if config_type == "main":
        return os.path.join(configs_dir, "nginx.conf")
    elif config_type in ["cache", "globals", "waf"]:
        if not name:
            return os.path.join(configs_dir, config_type)
        
        if config_type == "waf" and not name.endswith(".conf"):
            # Special case for WAF rules
            if name.startswith("rules/"):
                return os.path.join(configs_dir, config_type, "lua", name)
            else:
                return os.path.join(configs_dir, config_type, name)
        
        return os.path.join(configs_dir, config_type, f"{name}.conf")
    
    raise ValueError(f"Unknown config type: {config_type}")


@log_call
def read_config_file(config_type: str, name: Optional[str] = None) -> str:
    """
    Read the contents of a configuration file.
    
    Args:
        config_type: Type of configuration ('cache', 'globals', 'waf', 'main')
        name: Name of the specific configuration file (without extension)
        
    Returns:
        str: Contents of the configuration file
    """
    config_path = get_config_path(config_type, name)
    
    try:
        with open(config_path, 'r') as f:
            return f.read()
    except Exception as e:
        error(f"Failed to read NGINX config file {config_path}: {e}")
        return ""


@log_call
def write_config_file(config_type: str, name: Optional[str], content: str) -> bool:
    """
    Write content to a configuration file.
    
    Args:
        config_type: Type of configuration ('cache', 'globals', 'waf', 'main')
        name: Name of the specific configuration file (without extension)
        content: Content to write to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    config_path = get_config_path(config_type, name)
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        info(f"✅ NGINX configuration file written: {config_path}")
        return True
    except Exception as e:
        error(f"Failed to write NGINX config file {config_path}: {e}")
        return False


@log_call
def get_available_cache_configs() -> List[str]:
    """
    Get a list of available cache configuration files.
    
    Returns:
        List[str]: List of cache configuration names (without .conf extension)
    """
    cache_dir = get_config_path("cache")
    
    try:
        files = os.listdir(cache_dir)
        return [f.replace(".conf", "") for f in files if f.endswith(".conf")]
    except Exception as e:
        error(f"Failed to list cache configurations: {e}")
        return []