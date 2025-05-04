"""
SSL certificate checking functionality.

This module provides functions for checking and displaying information
about SSL certificates installed on websites.
"""

import os
import ssl
from datetime import datetime
from typing import Optional, Dict, Any

from rich.console import Console
from rich.table import Table

from src.common.logging import log_call, error
from src.common.utils.environment import env
from src.features.website.utils import get_site_config


# Create a console instance for rich output
console = Console()


@log_call
def check_ssl(domain: str) -> Optional[Dict[str, Any]]:
    """
    Check and display SSL certificate information for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[Dict[str, Any]]: Certificate information if successful, None otherwise
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"No configuration found for website {domain}.")
        return None

    cert_path = os.path.join(env["SITES_DIR"], domain, "ssl", "cert.crt")
    if not os.path.isfile(cert_path):
        error(f"Certificate file not found: {cert_path}")
        return None

    try:
        cert_dict = ssl._ssl._test_decode_cert(cert_path)

        subject = dict(x[0] for x in cert_dict.get("subject", []))
        issuer = dict(x[0] for x in cert_dict.get("issuer", []))
        not_before = cert_dict.get("notBefore")
        not_after = cert_dict.get("notAfter")

        issued_at = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
        expired_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        now = datetime.utcnow()

        days_left = (expired_at - now).days
        if days_left >= 0:
            status = f"Active ({days_left} days remaining)"
        else:
            status = f"❌ Expired ({-days_left} days ago)"

        issuer_str = ", ".join(f"{k}={v}" for (k, v) in issuer.items())

        # Build a nice table for display
        table = Table(title=f"🔒 SSL Certificate Information for: {domain}", header_style="bold cyan")
        table.add_column("Attribute", style="bold green")
        table.add_column("Value", style="white")

        table.add_row("Status", f"[blue]{status}[/]" if days_left >= 0 else f"[bold red]{status}[/]")
        table.add_row("Domain (CN)", subject.get("commonName", "-"))
        table.add_row("Organization (O)", subject.get("organizationName", "-"))
        table.add_row("Issuer", issuer.get("organizationName", "-"))
        table.add_row("Issued on", issued_at.strftime("%Y-%m-%d"))
        table.add_row("Expires on", expired_at.strftime("%Y-%m-%d"))
        table.add_row("Issuer chain", issuer_str)

        # Print the table to console
        console.print(table)

        # Return certificate information for programmatic use
        return {
            "domain": domain,
            "status": "valid" if days_left >= 0 else "expired",
            "days_left": days_left,
            "subject": subject,
            "issuer": issuer,
            "issued_at": issued_at.isoformat(),
            "expired_at": expired_at.isoformat(),
            "issuer_chain": issuer_str
        }

    except Exception as e:
        error(f"Error analyzing certificate: {e}")
        return None


@log_call
def get_ssl_status(domain: str) -> str:
    """
    Get a simple status string for an SSL certificate.
    
    Args:
        domain: Website domain name
        
    Returns:
        str: Status string ("valid", "expired", "not found", or "error")
    """
    cert_path = os.path.join(env["SITES_DIR"], domain, "ssl", "cert.crt")
    if not os.path.isfile(cert_path):
        return "not found"

    try:
        cert_dict = ssl._ssl._test_decode_cert(cert_path)
        not_after = cert_dict.get("notAfter")
        expired_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        now = datetime.utcnow()
        
        return "valid" if expired_at > now else "expired"
    except Exception:
        return "error"