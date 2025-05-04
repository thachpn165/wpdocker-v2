"""
CLI interface for checking SSL certificates.

This module provides a command-line interface for checking and displaying
information about SSL certificates installed on websites.
"""

import sys
import json
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error
from src.features.website.utils import select_website
from src.features.ssl.checker import check_ssl


@log_call
def cli_check_ssl(json_output: bool = False) -> bool:
    """
    CLI entry point for checking SSL certificates.
    
    Args:
        json_output: Whether to output in JSON format
        
    Returns:
        bool: True if certificate check was successful, False otherwise
    """
    domain = select_website("Select website to check SSL certificate:")
    
    if not domain:
        warn("No website selected or no websites available.")
        return False
    
    cert_info = check_ssl(domain)
    
    if cert_info and json_output:
        print(json.dumps(cert_info, indent=2))
    
    return cert_info is not None


if __name__ == "__main__":
    # Check if --json flag is provided
    json_output = "--json" in sys.argv
    success = cli_check_ssl(json_output)
    sys.exit(0 if success else 1)