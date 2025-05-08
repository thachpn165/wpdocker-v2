"""
NGINX reload CLI module.

This module provides functions for reloading NGINX configuration via CLI
and interactive prompts.
"""

import click
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.nginx.manager import reload


def cli_reload(interactive: bool = True) -> bool:
    """
    Reload NGINX configuration without restarting the service.
    
    Args:
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)
    
    Returns:
        bool: True if reload was successful, False otherwise
    """
    try:
        info("🔄 Reloading NGINX configuration...")
        result = reload()
        
        if result:
            success("✅ NGINX configuration reloaded successfully")
        else:
            error("❌ Failed to reload NGINX configuration")
            
        return result
    except Exception as e:
        error(f"❌ Error reloading NGINX configuration: {str(e)}")
        return False


@click.command(name="reload")
def reload_cli():
    """Reload NGINX configuration without restarting the service."""
    result = cli_reload(interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)