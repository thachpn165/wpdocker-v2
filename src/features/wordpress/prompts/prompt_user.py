"""
WordPress user management prompt module.

This module provides the user interface for managing WordPress users,
including resetting admin passwords and user roles.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.utils import select_website
from src.features.wordpress.cli.main import cli_reset_admin_password, cli_reset_user_role


@with_pause
def prompt_reset_admin_password() -> None:
    """
    Display admin password reset prompt and handle the password reset.
    
    This function displays a user-friendly menu for resetting WordPress admin passwords,
    calling the CLI implementation to perform the actual reset.
    """
    try:
        domain = select_website("Chọn website cần reset mật khẩu admin:")
        if not domain:
            info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
            return False
            
        result = cli_reset_admin_password(domain)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in admin password reset prompt: {e}")
        input("Press Enter to continue...")
        return False


@with_pause
def prompt_reset_user_role() -> None:
    """
    Display user role reset prompt and handle the role reset.
    
    This function displays a user-friendly menu for resetting WordPress user roles,
    calling the CLI implementation to perform the actual reset.
    """
    try:
        domain = select_website("Chọn website cần reset user role:")
        if not domain:
            info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
            return False
            
        result = cli_reset_user_role(domain)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in user role reset prompt: {e}")
        input("Press Enter to continue...")
        return False