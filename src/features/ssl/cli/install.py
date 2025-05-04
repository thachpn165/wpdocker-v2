"""
CLI interface for installing SSL certificates.

This module provides a command-line interface for installing various types
of SSL certificates on websites.
"""

import sys
import re
from questionary import text, select, confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.ssl.installer import (
    install_selfsigned_ssl,
    install_manual_ssl,
    install_letsencrypt_ssl
)


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
    if not re.match(pattern, email):
        return False
    return True


@log_call
def prompt_ssl_install() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for SSL installation parameters.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with installation parameters if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website to install SSL certificate:")
        
        if not domain:
            warn("No website selected or no websites available.")
            return None
        
        # Select certificate type
        cert_type = select(
            "Select SSL certificate type:",
            choices=[
                "Self-signed (for development)",
                "Let's Encrypt (requires public domain)",
                "Manual (paste certificate and key)"
            ]
        ).ask()
        
        if not cert_type:
            return None
        
        params = {
            "domain": domain,
            "cert_type": cert_type
        }
        
        # Additional parameters based on certificate type
        if cert_type == "Let's Encrypt (requires public domain)":
            email = text(
                "Email address for Let's Encrypt notifications:",
                validate=validate_email
            ).ask()
            
            if not email:
                return None
                
            staging = confirm(
                "Use Let's Encrypt staging environment? "
                "(Recommended for testing, doesn't count against rate limits)"
            ).ask()
            
            params["email"] = email
            params["staging"] = staging
            
        elif cert_type == "Manual (paste certificate and key)":
            info("Paste your certificate (including BEGIN/END lines):")
            cert_content = ""
            print("Enter certificate (end with a line containing only 'END'):")
            while True:
                line = input()
                if line == "END":
                    break
                cert_content += line + "\n"
            
            info("Paste your private key (including BEGIN/END lines):")
            key_content = ""
            print("Enter private key (end with a line containing only 'END'):")
            while True:
                line = input()
                if line == "END":
                    break
                key_content += line + "\n"
            
            params["cert_content"] = cert_content
            params["key_content"] = key_content
        
        # Confirm installation
        confirm_install = confirm(
            f"Install {cert_type.split(' ')[0]} SSL certificate for {domain}?"
        ).ask()
        
        if not confirm_install:
            warn("SSL installation cancelled.")
            return None
            
        return params
            
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_install_ssl() -> bool:
    """
    CLI entry point for installing SSL certificates.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    params = prompt_ssl_install()
    if not params:
        return False
    
    domain = params["domain"]
    cert_type = params["cert_type"]
    
    if cert_type == "Self-signed (for development)":
        return install_selfsigned_ssl(domain)
        
    elif cert_type == "Let's Encrypt (requires public domain)":
        return install_letsencrypt_ssl(
            domain,
            params["email"],
            params["staging"]
        )
        
    elif cert_type == "Manual (paste certificate and key)":
        return install_manual_ssl(
            domain,
            params["cert_content"],
            params["key_content"]
        )
    
    return False


if __name__ == "__main__":
    success = cli_install_ssl()
    sys.exit(0 if success else 1)