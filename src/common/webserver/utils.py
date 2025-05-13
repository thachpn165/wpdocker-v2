"""
Web server utilities.

This module provides functionality for working with the configured web server,
including retrieving the current web server type, loading the appropriate
module, and performing common operations.
"""

import importlib
from typing import Any, Optional

from src.common.logging import log_call
from src.common.config.manager import ConfigManager


@log_call
def get_current_webserver() -> str:
    """
    Get the name of the currently configured web server.

    Returns:
        The web server name (e.g., 'nginx')
    """
    config = ConfigManager()
    webserver = config.get("core.webserver", "nginx")  # Đặt nginx là mặc định

    # Validate và đảm bảo luôn trả về một giá trị hợp lệ
    if not webserver or webserver not in ["nginx", "apache"]:
        from src.common.logging import debug
        debug(f"Webserver không được cấu hình chính xác hoặc giá trị không hợp lệ: {webserver}, sử dụng nginx làm mặc định")
        return "nginx"

    return webserver


@log_call
def get_webserver_module() -> Any:
    """
    Get the module for the currently configured web server.
    
    Returns:
        The imported web server module
        
    Raises:
        ImportError: If the web server module cannot be imported
    """
    webserver = get_current_webserver()
    try:
        return importlib.import_module(f"src.features.webserver.{webserver}")
    except ImportError:
        # Fall back to old path structure during transition
        return importlib.import_module(f"core.backend.modules.{webserver}")


@log_call
def reload_webserver() -> None:
    """
    Reload the web server configuration.
    
    This function calls the reload method of the web server module
    if it exists.
    """
    mod = get_webserver_module()
    if hasattr(mod, "reload"):
        mod.reload()


@log_call
def apply_webserver_config() -> None:
    """
    Apply the current web server configuration.
    
    This function calls the apply_config method of the web server module
    if it exists.
    """
    mod = get_webserver_module()
    if hasattr(mod, "apply_config"):
        mod.apply_config()