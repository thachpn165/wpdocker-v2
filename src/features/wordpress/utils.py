"""
WordPress utility functions.

This module provides utility functions for WordPress operations,
including WP-CLI command execution.
"""

from typing import List, Optional

from src.common.logging import log_call, debug, info, error
from src.common.containers.container import Container


@log_call
def get_php_container_name(domain: str) -> str:
    """
    Get the PHP container name for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        PHP container name
    """
    return f"{domain}-php"


@log_call
def run_wp_cli(domain: str, args: List[str]) -> Optional[str]:
    """
    Execute WP-CLI command inside the PHP container for the domain.
    
    Args:
        domain: Website domain name
        args: List of WP-CLI command arguments, e.g. ['core', 'install', '--url=...', '--title=...']
        
    Returns:
        WP-CLI command output or None if error
    """
    container_name = get_php_container_name(domain)
    container = Container(name=container_name)

    if not container.running():
        error(f"❌ PHP container {container_name} is not running.")
        return None

    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir="/var/www/html")
        debug(f"WP CLI Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Error executing WP-CLI: {e}")
        return None