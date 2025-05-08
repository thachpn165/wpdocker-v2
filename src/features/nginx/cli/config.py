"""
NGINX configuration testing CLI module.

This module provides functions for testing NGINX configurations via CLI
and interactive prompts.
"""

import click
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.nginx.manager import test_config


def cli_test_config(interactive: bool = True) -> bool:
    """
    Test NGINX configuration for syntax errors.
    
    Args:
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        info("🔍 Testing NGINX configuration...")
        result = test_config()
        
        if result:
            success("✅ NGINX configuration is valid")
        else:
            error("❌ NGINX configuration contains errors")
            
        return result
    except Exception as e:
        error(f"❌ Error testing NGINX configuration: {str(e)}")
        return False


@click.command(name="test-config")
def test_config_cli():
    """Test NGINX configuration for syntax errors."""
    result = cli_test_config(interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)