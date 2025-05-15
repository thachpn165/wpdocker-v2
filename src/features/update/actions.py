"""
Action functions for update operations.

This module provides high-level action functions that interact with
the VersionUpdater to perform update-related tasks.
"""

from typing import Dict, Any

from src.common.logging import log_call
from src.common.utils.version_helper import get_version, get_channel, get_version_info
from src.features.update.core.version_updater import check_for_updates, download_and_install


@log_call
def check_version_action() -> Dict[str, Any]:
    """
    Check the current version and available updates.

    Returns:
        Dict containing version information and update status
    """
    # Lấy thông tin phiên bản từ helper
    version_info = get_version_info()
    
    result = {
        "current_version": version_info["version"],
        "channel": version_info["channel"],
        "display_name": version_info["display_name"],
        "update_available": False,
        "update_info": None
    }

    update_info = check_for_updates()
    if update_info:
        result["update_available"] = True
        result["update_info"] = update_info

    return result


@log_call
def update_action() -> Dict[str, Any]:
    """
    Update to the latest version.

    Returns:
        Dict containing success status and result message
    """
    # Check for updates
    update_info = check_for_updates()
    if not update_info:
        return {
            "success": False,
            "message": "Bạn đã sử dụng phiên bản mới nhất"
        }

    # Apply the update
    success = download_and_install(update_info)

    return {
        "success": success,
        "message": "Cập nhật thành công" if success else "Cập nhật thất bại"
    }