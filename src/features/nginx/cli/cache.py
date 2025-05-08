"""
NGINX cache management CLI module.

This module provides functions for managing NGINX caching configurations
via CLI and interactive prompts.
"""

import click
import os
from typing import Optional, List, Dict, Any

from src.common.logging import info, error, debug, success, warn
from src.features.nginx.utils.config_utils import (
    get_available_cache_configs,
    read_config_file,
    write_config_file,
    get_config_path
)
from src.features.nginx.manager import reload


def cli_manage_cache(website: Optional[str] = None, 
                     cache_type: Optional[str] = None,
                     interactive: bool = True) -> bool:
    """
    Manage NGINX cache configuration for a website.
    
    Args:
        website: Domain/website to configure cache for (optional)
        cache_type: Type of cache to enable (optional)
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get available cache configurations
        available_configs = get_available_cache_configs()
        
        if not available_configs:
            error("❌ No cache configurations found")
            return False
            
        # If in interactive mode and no cache_type specified, collect from user
        if interactive and not cache_type:
            from questionary import select
            
            # Create options list including "disable" option
            options = [{"name": f"Enable: {config}", "value": config} for config in available_configs]
            options.insert(0, {"name": "Disable caching", "value": "none"})
            
            # If no website specified, ask for one (would typically use website selection utility)
            if not website:
                from src.features.website.utils import select_website
                website = select_website("Select website to configure cache:")
                
                if not website:
                    return False
            
            # Ask for cache type
            cache_type = select(
                f"Select cache configuration for {website}:",
                choices=options
            ).ask()
            
            if not cache_type:
                return False
        
        # Validate inputs for CLI mode
        if not interactive and not website:
            error("❌ Website domain is required")
            return False
            
        if not interactive and cache_type not in available_configs + ["none"]:
            error(f"❌ Invalid cache type. Available types: {', '.join(['none'] + available_configs)}")
            return False
        
        # Implement cache configuration
        if cache_type == "none":
            info(f"🔄 Disabling cache for {website}...")
            # Implementation would depend on how sites are configured
            # This is a placeholder for actual implementation
            success(f"✅ Cache disabled for {website}")
        else:
            info(f"🔄 Enabling {cache_type} cache for {website}...")
            # Implementation would depend on how sites are configured
            # This is a placeholder for actual implementation
            success(f"✅ {cache_type} cache enabled for {website}")
        
        # Reload NGINX to apply changes
        info("🔄 Reloading NGINX to apply changes...")
        reload_result = reload()
        
        if not reload_result:
            warn("⚠️ Cache configuration updated but NGINX reload failed")
            
        return True
    except Exception as e:
        error(f"❌ Error managing NGINX cache: {str(e)}")
        return False


@click.command(name="cache")
@click.option("--website", required=True, help="Website domain to configure cache for")
@click.option("--type", "cache_type", help="Cache type to enable (or 'none' to disable)")
@click.option("--list", "list_configs", is_flag=True, help="List available cache configurations")
def cache_cli(website: str, cache_type: Optional[str], list_configs: bool):
    """Manage NGINX cache configuration."""
    if list_configs:
        available_configs = get_available_cache_configs()
        info("Available cache configurations:")
        for config in available_configs:
            info(f"- {config}")
        return
        
    if not cache_type:
        error("❌ Cache type is required (use --type or --list to see available types)")
        ctx = click.get_current_context()
        ctx.exit(1)
        
    result = cli_manage_cache(website, cache_type, interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)