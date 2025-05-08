"""
SSL certificate installation functionality.

This module provides functions for installing SSL certificates 
on websites, including self-signed, Let's Encrypt, and manual certificates.
"""

import os
import subprocess
from typing import Optional, Dict, Any, Tuple, List, Union

from src.common.logging import log_call, info, warn, error, success
from src.common.utils.environment import env
from src.common.utils.validation import is_valid_domain, validate_directory
from src.features.webserver.webserver_reload import WebserverReload


@log_call
def install_selfsigned_ssl(domain: str) -> bool:
    """
    Install a self-signed SSL certificate for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    if not is_valid_domain(domain):
        error(f"❌ Invalid domain name: {domain}")
        return False

    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    validate_directory(ssl_dir, create=True)

    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048",
        "-keyout", key_path,
        "-out", cert_path,
        "-subj", f"/C=US/ST=CA/L=SF/O=WP-Docker/OU=Dev/CN={domain}"
    ]

    try:
        subprocess.run(cmd, check=True)
        success(f"✅ Self-signed SSL certificate created for {domain}")
        WebserverReload.webserver_reload()
        return True
    except subprocess.CalledProcessError as e:
        error(f"❌ Error creating self-signed SSL for {domain}: {e}")
        return False


@log_call
def install_manual_ssl(domain: str, cert_content: str, key_content: str) -> bool:
    """
    Install a manually provided SSL certificate and key for a domain.
    
    Args:
        domain: Website domain name
        cert_content: Certificate content (PEM format)
        key_content: Private key content (PEM format)
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    validate_directory(ssl_dir, create=True)

    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    try:
        with open(cert_path, "w") as f:
            f.write(cert_content.strip())

        with open(key_path, "w") as f:
            f.write(key_content.strip())

        success(f"✅ Manual SSL certificate installed for {domain}")
        WebserverReload.webserver_reload()
        return True
    except Exception as e:
        error(f"❌ Cannot write manual SSL certificate: {e}")
        return False


@log_call
def edit_ssl_cert(domain: str, new_cert: str, new_key: str) -> bool:
    """
    Update an existing SSL certificate and key for a domain.
    
    Args:
        domain: Website domain name
        new_cert: New certificate content (PEM format)
        new_key: New private key content (PEM format)
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    validate_directory(ssl_dir, create=True)
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
        error(f"❌ Existing SSL files not found for {domain}")
        return False

    try:
        with open(cert_path, "w") as f:
            f.write(new_cert.strip())
        with open(key_path, "w") as f:
            f.write(new_key.strip())

        success(f"✅ SSL certificate updated for {domain}")
        WebserverReload.webserver_reload()
        return True
    except Exception as e:
        error(f"❌ Error updating SSL certificate: {e}")
        return False
    
    
@log_call
def install_letsencrypt_ssl(domain: str, email: str, staging: bool = False) -> bool:
    """
    Install a Let's Encrypt SSL certificate for a domain.
    
    Args:
        domain: Website domain name
        email: Email address for Let's Encrypt notifications
        staging: Whether to use Let's Encrypt staging environment
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    if not is_valid_domain(domain):
        error(f"❌ Invalid domain name: {domain}")
        return False

    if not email or "@" not in email:
        error(f"❌ Invalid email address: {email}")
        return False

    webroot = os.path.join(env["SITES_DIR"], domain, "wordpress")
    certbot_data = os.path.join(env["INSTALL_DIR"], ".certbot")
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    validate_directory(certbot_data, create=True)
    validate_directory(ssl_dir, create=True)

    certbot_args = [
        "certonly",
        "--webroot", "-w", "/var/www/html",
        "-d", domain,
        "--non-interactive",
        "--agree-tos",
        "-m", email
    ]

    if staging:
        certbot_args.append("--staging")

    try:
        # Dynamic import to avoid dependency issues
        from python_on_whales import docker

        docker.run(
            image="certbot/certbot",
            remove=True,
            volumes=[
                f"{webroot}:/var/www/html",
                f"{certbot_data}:/etc/letsencrypt"
            ],
            command=certbot_args
        )

        cert_path = os.path.join(certbot_data, "live", domain, "fullchain.pem")
        key_path = os.path.join(certbot_data, "live", domain, "privkey.pem")

        if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
            error(f"❌ Let's Encrypt certificates not found for {domain}")
            return False

        # Copy certificates to website directory
        with open(cert_path, "r") as f:
            cert_content = f.read()
        with open(key_path, "r") as f:
            key_content = f.read()

        with open(os.path.join(ssl_dir, "cert.crt"), "w") as f:
            f.write(cert_content)
        with open(os.path.join(ssl_dir, "priv.key"), "w") as f:
            f.write(key_content)

        success(f"✅ Let's Encrypt SSL certificate installed successfully for {domain}")
        WebserverReload.webserver_reload()
        return True

    except Exception as e:
        error(f"❌ Error installing Let's Encrypt SSL for {domain}: {e}")
        return False