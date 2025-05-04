"""
CLI interface for website creation.

This module provides a command-line interface for creating new websites, 
handling user input validation and parameter collection.
"""

import re
import sys
from questionary import text, select, confirm
from typing import Optional, Dict, Any, Tuple

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import is_website_exists
from src.features.website.manager import create_website


@log_call
def validate_domain(domain: str) -> bool:
    """
    Validate that a domain name is properly formatted.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        bool: True if domain is valid, False otherwise
    """
    # Basic domain validation with regex
    pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    is_valid = bool(re.match(pattern, domain))
    
    if not is_valid:
        error(f"❌ Invalid domain format: {domain}")
        return False
        
    # Check if website already exists
    if is_website_exists(domain):
        warn(f"⚠️ Website {domain} already exists.")
        return False
        
    return True


@log_call
def prompt_website_create() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for website creation parameters.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and php_version if successful,
                                 None if cancelled
    """
    try:
        domain = text(
            "Enter domain name (e.g., example.com):",
            validate=validate_domain
        ).ask()
        
        if not domain:
            warn("Website creation cancelled.")
            return None
            
        php_versions = ["8.2", "8.1", "8.0", "7.4"]
        php_version = select(
            "Select PHP version:",
            choices=php_versions,
            default="8.2"
        ).ask()
        
        confirm_create = confirm(
            f"Create website {domain} with PHP {php_version}?"
        ).ask()
        
        if not confirm_create:
            warn("Website creation cancelled.")
            return None
            
        return {
            "domain": domain,
            "php_version": php_version
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_create_website() -> bool:
    """
    CLI entry point for website creation.
    
    This function handles the interactive prompts for creating a new website
    and calls the creation function with the provided parameters.
    
    Returns:
        bool: True if website creation was successful, False otherwise
    """
    params = prompt_website_create()
    if not params:
        return False
        
    return create_website(params["domain"], params["php_version"])


if __name__ == "__main__":
    success = cli_create_website()
    sys.exit(0 if success else 1)