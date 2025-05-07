"""
SSL certificate checking functionality.

This module provides functions for checking SSL certificate status and validity.
"""

import os
import ssl
import socket
from typing import Dict, Any, Optional
from datetime import datetime

from src.common.logging import log_call, debug, error, info, warn
from src.features.website.utils import get_site_config
from src.features.ssl.utils.ssl_utils import get_ssl_paths, has_ssl_certificate


@log_call
def check_ssl(domain: str) -> Dict[str, Any]:
    """
    Check SSL certificate status for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        Dict[str, Any]: Certificate status information
    """
    try:
        # Check if certificate exists
        if not has_ssl_certificate(domain):
            return {
                "status": "error",
                "message": "No SSL certificate found"
            }
            
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Connect to domain
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
        # Get certificate information
        subject = dict(x[0] for x in cert['subject'])
        issuer = dict(x[0] for x in cert['issuer'])
        
        # Check expiration
        not_before = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y %Z")
        not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        now = datetime.now()
        
        is_expired = now > not_after
        days_remaining = (not_after - now).days
        
        # Get site config
        site_config = get_site_config(domain)
        ssl_config = site_config.ssl if site_config and hasattr(site_config, "ssl") else None
        
        return {
            "status": "success",
            "is_valid": not is_expired,
            "is_expired": is_expired,
            "days_remaining": days_remaining,
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "subject": {
                "common_name": subject.get('commonName', ''),
                "organization": subject.get('organizationName', ''),
                "country": subject.get('countryName', '')
            },
            "issuer": {
                "common_name": issuer.get('commonName', ''),
                "organization": issuer.get('organizationName', ''),
                "country": issuer.get('countryName', '')
            },
            "type": ssl_config.type.value if ssl_config else None,
            "auto_renew": ssl_config.auto_renew if ssl_config else False
        }
        
    except Exception as e:
        error(f"Error checking SSL certificate: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@log_call
def get_ssl_status(domain: str) -> str:
    """
    Get simplified SSL status for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        str: Status message
    """
    result = check_ssl(domain)
    if result["status"] == "error":
        return "❌ " + result["message"]
        
    if not result["is_valid"]:
        if result["is_expired"]:
            return f"❌ Certificate expired {abs(result['days_remaining'])} days ago"
            
    return f"✅ Valid certificate ({result['days_remaining']} days remaining)" 