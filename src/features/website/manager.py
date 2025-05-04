"""
Website manager provides high-level operations for website management.

This module offers functionality to create, delete, restart, and get information
about websites in the system.
"""

import inspect
from typing import List, Dict, Any, Optional, Tuple, Callable

from src.common.logging import log_call, info, warn, error, success, debug
from src.features.website.utils import is_website_exists
from src.features.website.actions import (
    WEBSITE_SETUP_ACTIONS,
    WEBSITE_CLEANUP_ACTIONS
)


@log_call
def create_website(domain: str, php_version: str) -> bool:
    """
    Create a new website with the specified domain and PHP version.
    
    This function orchestrates all the steps needed to create a fully functional
    website, including directory structure, PHP container, database, and NGINX configuration.
    
    Args:
        domain: Website domain name
        php_version: PHP version to use for the website
        
    Returns:
        bool: True if website creation was successful, False otherwise
    """
    if is_website_exists(domain):
        warn(f"⚠️ Website {domain} already exists.")
        return False

    completed_steps = []
    try:
        for setup_func, cleanup_func in WEBSITE_SETUP_ACTIONS:
            sig = inspect.signature(setup_func)
            if len(sig.parameters) == 2:
                setup_func(domain, php_version)
            elif len(sig.parameters) == 1:
                setup_func(domain)
            else:
                raise ValueError(f"Unexpected number of parameters for {setup_func.__name__}")
            completed_steps.append((setup_func, cleanup_func))
        success(f"✅ Website {domain} has been created successfully.")
        return True
    except (KeyboardInterrupt, EOFError):
        error("❌ Website creation cancelled (Ctrl+C or Ctrl+Z).")
        cleanup_website_partial(domain, completed_steps)
        return False
    except Exception as e:
        error(f"❌ Error creating website: {e}")
        cleanup_website_partial(domain, completed_steps)
        return False


def cleanup_website_partial(domain: str, 
                             completed_steps: List[Tuple[Callable, Optional[Callable]]]) -> None:
    """
    Roll back completed setup steps for a website.
    
    This function is called when website creation fails to clean up any partial setup.
    
    Args:
        domain: Website domain name
        completed_steps: List of (setup_func, cleanup_func) pairs that were completed
    """
    warn(f"⚠️ Rolling back completed steps for website {domain}...")
    for setup_func, cleanup_func in reversed(completed_steps):
        if cleanup_func is not None:
            try:
                cleanup_func(domain)
                info(f"↩️ Rolled back step {cleanup_func.__name__} for website {domain}.")
            except Exception as e:
                error(f"❌ Error rolling back step {cleanup_func.__name__}: {e}")


@log_call
def delete_website(domain: str) -> bool:
    """
    Delete a website completely, removing all associated resources.
    
    This function removes all website components including files, database,
    containers, and configuration.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if website deletion was successful, False otherwise
    """
    if not is_website_exists(domain):
        warn(f"⚠️ Website {domain} does not exist.")
        return False

    try:
        for cleanup_func in WEBSITE_CLEANUP_ACTIONS:
            try:
                cleanup_func(domain)
            except Exception as e:
                error(f"❌ Error in {cleanup_func.__name__}: {e}")
                # Continue with other cleanup operations even if one fails

        success(f"✅ Website {domain} has been completely removed.")
        return True
    except Exception as e:
        error(f"❌ Error deleting website: {e}")
        return False


@log_call
def restart_website(domain: str) -> bool:
    """
    Restart a website by restarting its PHP container.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if website restart was successful, False otherwise
    """
    from src.features.website.utils import get_site_config
    from src.common.containers.container import Container
    
    if not is_website_exists(domain):
        warn(f"⚠️ Website {domain} does not exist.")
        return False
    
    site_config = get_site_config(domain)
    if not site_config or not site_config.php or not site_config.php.php_container:
        error(f"❌ No PHP container found for website {domain}.")
        return False
    
    try:
        container = Container(name=site_config.php.php_container)
        container.restart()
        success(f"✅ Website {domain} has been restarted.")
        return True
    except Exception as e:
        error(f"❌ Error restarting website {domain}: {e}")
        return False