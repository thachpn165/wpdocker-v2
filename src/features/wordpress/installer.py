"""
WordPress installer functionality.

This module provides high-level functionality for installing WordPress on a website,
orchestrating the various installation steps and handling errors.
"""

from typing import Dict, Any, Optional, List, Tuple

from src.common.logging import debug, info, error, success, log_call
from src.features.wordpress import actions


@log_call
def install_wordpress(domain: str, site_url: str, title: str, 
                     admin_user: str, admin_pass: str, admin_email: str) -> bool:
    """
    Install WordPress on a website with the given parameters.
    
    This function orchestrates all the steps needed for a complete WordPress installation
    and handles failures with appropriate cleanup.
    
    Args:
        domain: Website domain name
        site_url: Website URL
        title: Website title
        admin_user: Admin username
        admin_pass: Admin password
        admin_email: Admin email
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    debug(f"▶️ Starting WordPress installation for {domain}")

    # Track completed steps for rollback if needed
    steps_done = []

    if not actions.check_containers(domain):
        return False

    if not actions.download_core(domain):
        return False
    steps_done.append("download_core")

    if not actions.generate_config(domain):
        actions.delete_core(domain)
        return False
    steps_done.append("generate_config")

    if not actions.configure_db(domain):
        actions.delete_config(domain)
        actions.delete_core(domain)
        return False
    steps_done.append("configure_db")

    if not actions.check_database(domain):
        actions.delete_config(domain)
        actions.delete_core(domain)
        return False
    steps_done.append("check_database")

    if not actions.core_install(domain, site_url, title, admin_user, admin_pass, admin_email):
        actions.uninstall(domain)
        return False
    steps_done.append("core_install")

    if not actions.fix_permissions(domain):
        error("⚠️ Warning: Unable to fix permissions, but installation continues.")

    if not actions.verify_installation(domain):
        error(f"❌ WordPress installation verification failed. Rolling back...")
        actions.uninstall(domain)
        return False

    if not actions.save_post_install_config(domain):
        error("❌ Failed to save post-installation configuration. Rolling back...")
        actions.delete_post_install_config(domain)
        return False
    
    # ✅ Success
    success(f"🎉 WordPress website {domain} has been installed successfully!")
    info(f"🔑 Login information:")
    info(f"🌐 URL: {site_url}/wp-admin")
    info(f"👤 Admin User: {admin_user}")
    info(f"🔒 Admin Password: {admin_pass}")

    return True


@log_call
def uninstall_wordpress(domain: str) -> bool:
    """
    Completely remove WordPress installation from a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if uninstallation was successful, False otherwise
    """
    try:
        actions.uninstall(domain)
        actions.delete_post_install_config(domain)
        success(f"✅ WordPress has been completely removed from {domain}.")
        return True
    except Exception as e:
        error(f"❌ Error removing WordPress from {domain}: {e}")
        return False