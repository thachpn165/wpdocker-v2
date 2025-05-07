"""
SSL certificate installation functionality.

This module provides functions for installing different types of SSL certificates.
"""

import os
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.common.logging import log_call, debug, error, info, warn
from src.common.utils.environment import env
from src.features.website.utils import get_site_config, set_site_config
from src.features.ssl.utils.ssl_utils import (
    get_ssl_paths,
    ensure_ssl_dir,
    backup_ssl_files
)
from src.features.ssl.models.ssl_config import SSLConfig, SSLType


@log_call
def install_selfsigned_ssl(domain: str, email: Optional[str] = None) -> bool:
    """
    Install self-signed SSL certificate.
    
    Args:
        domain: Domain name
        email: Email address for certificate
        
    Returns:
        bool: True if installation was successful
    """
    try:
        # Ensure SSL directory exists
        if not ensure_ssl_dir(domain):
            return False
            
        # Create backup if certificate exists
        if has_ssl_certificate(domain):
            backup_ssl_files(domain)
            
        # Generate self-signed certificate
        paths = get_ssl_paths(domain)
        subject = f"/CN={domain}"
        if email:
            subject += f"/emailAddress={email}"
            
        cmd = [
            "openssl", "req", "-x509", "-nodes",
            "-days", "365",
            "-newkey", "rsa:2048",
            "-keyout", paths["key"],
            "-out", paths["cert"],
            "-subj", subject
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error(f"Error generating self-signed certificate: {result.stderr}")
            return False
            
        # Update site config
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
            
        ssl_config = SSLConfig(
            type=SSLType.SELFSIGNED,
            domain=domain,
            cert_path=paths["cert"],
            key_path=paths["key"],
            email=email,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=365)).isoformat()
        )
        
        site_config.ssl = ssl_config
        set_site_config(domain, site_config)
        
        info(f"✅ Successfully installed self-signed SSL certificate for {domain}")
        return True
        
    except Exception as e:
        error(f"Error installing self-signed SSL: {e}")
        return False


@log_call
def install_manual_ssl(
    domain: str,
    cert_path: str,
    key_path: str,
    chain_path: Optional[str] = None
) -> bool:
    """
    Install manual SSL certificate.
    
    Args:
        domain: Domain name
        cert_path: Path to certificate file
        key_path: Path to private key file
        chain_path: Path to certificate chain file
        
    Returns:
        bool: True if installation was successful
    """
    try:
        # Ensure SSL directory exists
        if not ensure_ssl_dir(domain):
            return False
            
        # Create backup if certificate exists
        if has_ssl_certificate(domain):
            backup_ssl_files(domain)
            
        # Copy certificate files
        paths = get_ssl_paths(domain)
        shutil.copy2(cert_path, paths["cert"])
        shutil.copy2(key_path, paths["key"])
        
        if chain_path:
            shutil.copy2(chain_path, paths["chain"])
            
        # Update site config
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
            
        ssl_config = SSLConfig(
            type=SSLType.MANUAL,
            domain=domain,
            cert_path=paths["cert"],
            key_path=paths["key"],
            chain_path=paths["chain"] if chain_path else None,
            created_at=datetime.now().isoformat()
        )
        
        site_config.ssl = ssl_config
        set_site_config(domain, site_config)
        
        info(f"✅ Successfully installed manual SSL certificate for {domain}")
        return True
        
    except Exception as e:
        error(f"Error installing manual SSL: {e}")
        return False


@log_call
def install_letsencrypt_ssl(
    domain: str,
    email: str,
    auto_renew: bool = True
) -> bool:
    """
    Install Let's Encrypt SSL certificate.
    
    Args:
        domain: Domain name
        email: Email address for Let's Encrypt
        auto_renew: Whether to enable auto-renewal
        
    Returns:
        bool: True if installation was successful
    """
    try:
        # Ensure SSL directory exists
        if not ensure_ssl_dir(domain):
            return False
            
        # Create backup if certificate exists
        if has_ssl_certificate(domain):
            backup_ssl_files(domain)
            
        # Install certbot if not installed
        if not os.path.exists("/usr/bin/certbot"):
            cmd = ["apt-get", "update"]
            subprocess.run(cmd, check=True)
            
            cmd = ["apt-get", "install", "-y", "certbot"]
            subprocess.run(cmd, check=True)
            
        # Obtain certificate
        cmd = [
            "certbot", "certonly", "--standalone",
            "--agree-tos", "--non-interactive",
            "--email", email,
            "-d", domain
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error(f"Error obtaining Let's Encrypt certificate: {result.stderr}")
            return False
            
        # Copy certificate files
        paths = get_ssl_paths(domain)
        certbot_path = f"/etc/letsencrypt/live/{domain}"
        
        shutil.copy2(f"{certbot_path}/cert.pem", paths["cert"])
        shutil.copy2(f"{certbot_path}/privkey.pem", paths["key"])
        shutil.copy2(f"{certbot_path}/chain.pem", paths["chain"])
        shutil.copy2(f"{certbot_path}/fullchain.pem", paths["fullchain"])
        
        # Update site config
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
            
        ssl_config = SSLConfig(
            type=SSLType.LETSENCRYPT,
            domain=domain,
            cert_path=paths["cert"],
            key_path=paths["key"],
            chain_path=paths["chain"],
            auto_renew=auto_renew,
            email=email,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=90)).isoformat()
        )
        
        site_config.ssl = ssl_config
        set_site_config(domain, site_config)
        
        # Setup auto-renewal if enabled
        if auto_renew:
            cron_cmd = f"0 0 * * * certbot renew --quiet --post-hook 'docker restart nginx'"
            with open("/etc/cron.d/certbot-renew", "w") as f:
                f.write(cron_cmd)
                
        info(f"✅ Successfully installed Let's Encrypt SSL certificate for {domain}")
        return True
        
    except Exception as e:
        error(f"Error installing Let's Encrypt SSL: {e}")
        return False 