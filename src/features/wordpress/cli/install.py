"""
CLI interface for WordPress installation.

This module provides a command-line interface for installing WordPress,
handling user input validation and parameter collection.
"""

import sys
import re
from questionary import text, select, confirm, password
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import is_website_exists, select_website
from src.features.wordpress.installer import install_wordpress


@log_call
def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email format is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


@log_call
def validate_password(password: str) -> bool:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        bool: True if password is strong enough, False otherwise
    """
    if len(password) < 8:
        return False
    return True


@log_call
def prompt_wordpress_install() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for WordPress installation parameters.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with installation parameters if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website for WordPress installation:")
        if not domain:
            warn("No website selected or no websites available.")
            return None
        
        # Site URL
        default_url = f"https://{domain}"
        site_url = text(
            "Website URL:",
            default=default_url
        ).ask()
        
        # Site title
        default_title = domain.split('.')[0].title()
        title = text(
            "Website title:",
            default=default_title
        ).ask()
        
        # Admin username
        admin_user = text(
            "Admin username:",
            default="admin"
        ).ask()
        
        # Admin password
        while True:
            admin_pass = password(
                "Admin password (min 8 characters):"
            ).ask()
            
            if validate_password(admin_pass):
                break
            error("❌ Password must be at least 8 characters long.")
        
        # Admin email
        while True:
            admin_email = text(
                "Admin email address:"
            ).ask()
            
            if validate_email(admin_email):
                break
            error("❌ Invalid email format.")
        
        # Confirmation
        confirm_install = confirm(
            f"Install WordPress on {domain} with these settings?"
        ).ask()
        
        if not confirm_install:
            warn("WordPress installation cancelled.")
            return None
        
        return {
            "domain": domain,
            "site_url": site_url,
            "title": title,
            "admin_user": admin_user,
            "admin_pass": admin_pass,
            "admin_email": admin_email
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_install_wordpress() -> bool:
    """
    CLI entry point for WordPress installation.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    params = prompt_wordpress_install()
    if not params:
        return False
    
    return install_wordpress(
        params["domain"],
        params["site_url"],
        params["title"],
        params["admin_user"],
        params["admin_pass"],
        params["admin_email"]
    )


if __name__ == "__main__":
    success = cli_install_wordpress()
    sys.exit(0 if success else 1)