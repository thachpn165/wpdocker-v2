"""
CLI interface for NGINX module.

This module exports CLI functions and the main command group.
"""
from src.features.nginx.cli.main import nginx_cli
from src.features.nginx.cli.config import cli_test_config
from src.features.nginx.cli.reload import cli_reload
from src.features.nginx.cli.restart import cli_restart
from src.features.nginx.cli.cache import cli_manage_cache

__all__ = [
    "nginx_cli",
    "cli_test_config",
    "cli_reload",
    "cli_restart",
    "cli_manage_cache"
]