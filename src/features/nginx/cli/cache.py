"""
NGINX cache management CLI module.

This module provides functions for managing NGINX caching configurations
via CLI and interactive prompts.
"""

import click
import os
from typing import Optional, List, Dict, Any, Tuple

from src.common.logging import info, error, debug, success, warn
from src.features.nginx.cache import (
    install_cache,
    get_available_cache_types
)


def cli_manage_cache(website: Optional[str] = None, 
                     cache_type: Optional[str] = None,
                     interactive: bool = True) -> bool:
    """
    Manage NGINX cache configuration for a website.
    
    Args:
        website: Domain/website to configure cache for (optional in interactive mode)
        cache_type: Type of cache to enable (optional in interactive mode)
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get available cache configurations
        available_cache_types = get_available_cache_types()
        
        if not available_cache_types:
            error("❌ No cache configurations found")
            return False
            
        # If in interactive mode and no cache_type specified, collect from user
        if interactive and not cache_type:
            from questionary import select
            
            # Create options list
            options = [{"name": f"{cache_type_name}", "value": cache_type_name} 
                      for cache_type_name in available_cache_types]
            
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
            
        if not interactive and cache_type not in available_cache_types:
            error(f"❌ Invalid cache type. Available types: {', '.join(available_cache_types)}")
            return False
        
        # Install selected cache
        success_result, message = install_cache(website, cache_type)
        
        if success_result:
            success(message)
            return True
        else:
            error(message)
            return False
    except Exception as e:
        error(f"❌ Error managing NGINX cache: {str(e)}")
        return False


@click.command(name="cache")
@click.option("--website", required=False, help="Website domain to configure cache for")
@click.option("--type", "cache_type", required=False, help="Cache type to enable")
@click.option("--list", "list_configs", is_flag=True, help="List available cache configurations")
def cache_cli(website: Optional[str], cache_type: Optional[str], list_configs: bool):
    """Manage NGINX cache configuration."""
    if list_configs:
        available_configs = get_available_cache_types()
        info("Available cache configurations:")
        for config in available_configs:
            info(f"- {config}")
        return
        
    if not website:
        error("❌ Website domain is required (use --website)")
        ctx = click.get_current_context()
        ctx.exit(1)
        
    if not cache_type:
        error("❌ Cache type is required (use --type or --list to see available types)")
        ctx = click.get_current_context()
        ctx.exit(1)
        
    result = cli_manage_cache(website, cache_type, interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)