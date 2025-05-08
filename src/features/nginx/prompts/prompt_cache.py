"""
NGINX cache management prompt module.

This module provides the user interface for managing NGINX cache configuration.
"""

import questionary
from typing import Optional, List

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import pause_after_action
from src.features.nginx.cache import get_available_cache_types
from src.features.website.utils import select_website

def prompt_manage_cache() -> None:
    """Prompt for managing NGINX cache configuration."""
    try:
        info("\n📋 Manage Website Cache Configuration")
        
        # Step 1: Select website
        website = select_website("Select website to configure cache:")
        
        if not website:
            info("Operation cancelled.")
            input("\nPress Enter to continue...")
            return
        
        # Step 2: Get available cache types and create choices
        cache_types = get_available_cache_types()
        
        if not cache_types:
            error("❌ No cache configurations found")
            input("\nPress Enter to continue...")
            return
            
        # Create choices for cache types
        cache_choices = []
        
        # Add descriptive names for each cache type
        for cache_type in cache_types:
            if cache_type == "no-cache":
                cache_choices.append({"name": "No Cache (Disable caching)", "value": cache_type})
            elif cache_type == "fastcgi-cache":
                cache_choices.append({"name": "FastCGI Cache (Best performance, no plugin needed)", "value": cache_type})
            elif cache_type == "wp-super-cache":
                cache_choices.append({"name": "WP Super Cache (Requires plugin)", "value": cache_type})
            elif cache_type == "w3-total-cache":
                cache_choices.append({"name": "W3 Total Cache (Requires plugin)", "value": cache_type})
            elif cache_type == "wp-fastest-cache":
                cache_choices.append({"name": "WP Fastest Cache (Requires plugin)", "value": cache_type})
            else:
                cache_choices.append({"name": cache_type, "value": cache_type})
        
        # Step 3: Ask user to select cache type
        cache_type = questionary.select(
            f"Select cache configuration for {website}:",
            choices=cache_choices
        ).ask()
        
        if not cache_type:
            info("Operation cancelled.")
            input("\nPress Enter to continue...")
            return
        
        # Add confirmation step
        confirm_message = (f"Are you sure you want to apply {cache_type} to {website}?")
        
        # Add warning for no-cache
        if cache_type == "no-cache":
            confirm_message = f"⚠️ This will disable all caching for {website}. Are you sure?"
        
        confirmed = questionary.confirm(confirm_message, default=True).ask()
        
        if not confirmed:
            info("Operation cancelled.")
            input("\nPress Enter to continue...")
            return
        
        # Step 4: Apply the selected cache configuration using CLI function
        from src.features.nginx.cli.cache import cli_manage_cache
        cli_manage_cache(website, cache_type, interactive=True)
        
        # Pause to let the user read the output
        pause_after_action()
    except Exception as e:
        error(f"Error managing NGINX cache: {e}")
        input("\nPress Enter to continue...")