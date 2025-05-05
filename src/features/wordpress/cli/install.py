"""
CLI interface for WordPress installation.

This module provides a command-line interface for installing WordPress,
handling user input validation and parameter collection.
"""

import sys
import re
import random
import string
from questionary import text, select, confirm, password
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import is_website_exists, select_website
from src.features.wordpress.installer import install_wordpress
from src.common.utils.password import strong_password


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
def prompt_wordpress_install(domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Prompt the user for WordPress installation parameters.
    With option to generate random user credentials.
    
    Args:
        domain: Optional domain name. If provided, skips the website selection step.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with installation parameters if successful,
                                 None if cancelled
    """
    try:
        # If domain is not provided, select website
        if not domain:
            domain = select_website("Select website for WordPress installation:")
            if not domain:
                warn("No website selected or no websites available.")
                return None
        
        # Verify that the website exists
        if not is_website_exists(domain):
            warn(f"⚠️ Website {domain} does not exist.")
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
        
        # Ask if user wants random credentials
        use_random_credentials = confirm(
            "Would you like to generate random admin credentials?"
        ).ask()
        
        if use_random_credentials:
            # Generate random admin username and password
            admin_user = ''.join(random.choices(string.ascii_lowercase, k=8))
            admin_pass = strong_password()
            
            # Display generated credentials
            info(f"🔑 Generated admin username: {admin_user}")
            info(f"🔒 Generated admin password: {admin_pass}")
        else:
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
                
                # Confirm password
                confirm_pass = password(
                    "Confirm admin password:"
                ).ask()
                
                if admin_pass != confirm_pass:
                    error("❌ Passwords do not match. Please try again.")
                    continue
                
                if validate_password(admin_pass):
                    break
                error("❌ Password must be at least 8 characters long.")
        
        # Default email based on domain
        default_email = f"contact@{domain}"
        
        # Admin email
        while True:
            admin_email = text(
                "Admin email address:",
                default=default_email
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
def cli_install_wordpress(domain: Optional[str] = None) -> bool:
    """
    CLI entry point for WordPress installation.
    
    Args:
        domain: Optional domain name. If provided, skips the website selection step.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    params = prompt_wordpress_install(domain)
    if not params:
        return False
    
    # Actually install WordPress using the parameters
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