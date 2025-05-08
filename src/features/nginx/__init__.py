"""
NGINX web server management functionality.

This package provides functionality for managing NGINX configuration,
including virtual host management, caching, and security.
"""
# Re-export core functions for backward compatibility
from src.features.nginx.manager import test_config, reload, restart, apply_config

# Export CLI functions for usage by other modules
from src.features.nginx.cli import (
    nginx_cli,
    cli_test_config,
    cli_reload,
    cli_restart,
    cli_manage_cache
)

# Export prompt functions
from src.features.nginx.prompts.prompt_menu import prompt_nginx_menu

__all__ = [
    # Core functions
    'test_config',
    'reload',
    'restart',
    'apply_config',  # Required for webserver compatibility
    
    # CLI functions
    'nginx_cli',
    'cli_test_config',
    'cli_reload',
    'cli_restart',
    'cli_manage_cache',
    
    # Prompt functions
    'prompt_nginx_menu'
]