"""
NGINX restart CLI module.

This module provides functions for restarting the NGINX container via CLI
and interactive prompts.
"""

import click
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.nginx.manager import restart


def cli_restart(interactive: bool = True) -> bool:
    """
    Restart the NGINX container.
    
    Args:
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)
    
    Returns:
        bool: True if restart was successful, False otherwise
    """
    try:
        info("🔁 Restarting NGINX container...")
        result = restart()
        
        if result:
            success("✅ NGINX container restarted successfully")
        else:
            error("❌ Failed to restart NGINX container")
            
        return result
    except Exception as e:
        error(f"❌ Error restarting NGINX container: {str(e)}")
        return False


@click.command(name="restart")
def restart_cli():
    """Restart the NGINX container."""
    result = cli_restart(interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)