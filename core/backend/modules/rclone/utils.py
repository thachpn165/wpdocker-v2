#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, List, Optional, Union
from datetime import datetime

from core.backend.utils.env_utils import get_env_value
from core.backend.utils.debug import Debug


def get_backup_filename(prefix: str = "backup", extension: str = "tar.gz") -> str:
    """Generate a backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


# This function has been moved to core/backend/utils/container_utils.py
# Import it from there instead of using this function
from core.backend.utils.container_utils import convert_host_path_to_container as _convert_path

def convert_host_path_to_container(host_path: str) -> str:
    """Convert host path to container path for Rclone.
    
    This is a wrapper around the function in container_utils.py
    for backward compatibility.
    
    Args:
        host_path: Path on the host system
        
    Returns:
        Path as it would be seen inside the Rclone container
    """
    return _convert_path(host_path, 'rclone')


def validate_remote_type(remote_type: str) -> bool:
    """Validate if the remote type is supported by Rclone."""
    # Common remote types supported by Rclone
    supported_types = [
        "s3", "b2", "drive", "dropbox", "onedrive", "box", "sftp", 
        "ftp", "http", "webdav", "azureblob", "swift", "hubic", "local"
    ]
    return remote_type.lower() in supported_types


def parse_backup_list(output: str) -> List[Dict[str, Union[str, int]]]:
    """Parse the output of rclone lsjson command to get backup files information."""
    try:
        files = json.loads(output)
        # Filter out directories and sort by time (most recent first)
        backup_files = [f for f in files if not f.get("IsDir", False)]
        backup_files.sort(key=lambda x: x.get("ModTime", ""), reverse=True)
        return backup_files
    except json.JSONDecodeError:
        Debug("RcloneUtils").error(f"Failed to parse JSON output: {output}")
        return []


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_backup_directory() -> str:
    """Get the configured backup directory."""
    backup_dir = get_env_value("BACKUP_DIR")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def validate_remote_params(remote_type: str, params: Dict[str, str]) -> bool:
    """Validate parameters for a specific remote type."""
    # Basic validation for common remote types
    required_params = {
        "s3": ["provider", "access_key_id", "secret_access_key", "region"],
        "b2": ["account", "key"],
        "drive": ["client_id", "client_secret"],
        "dropbox": ["client_id", "client_secret"],
        "onedrive": ["client_id", "client_secret"],
        "sftp": ["host", "user"],
        "ftp": ["host", "user"],
    }
    
    # Nếu có token, điều này có nghĩa là người dùng đã nhập cấu hình thủ công
    # cho một OAuth provider và chúng ta không cần kiểm tra các tham số khác
    if "token" in params and remote_type.lower() in ["drive", "dropbox", "onedrive", "box", "mega", "pcloud"]:
        return True
    
    if remote_type.lower() in required_params:
        for param in required_params[remote_type.lower()]:
            if param not in params:
                return False
    
    return True


def get_remote_type_display_name(remote_type: str) -> str:
    """Return a friendly display name for the remote type.
    
    Args:
        remote_type: The technical name of the remote type
        
    Returns:
        str: The friendly display name for the remote type
    """
    remote_type_display = {
        "s3": "Amazon S3 / Tương thích S3",
        "b2": "Backblaze B2",
        "drive": "Google Drive",
        "dropbox": "Dropbox",
        "onedrive": "Microsoft OneDrive",
        "box": "Box",
        "sftp": "SFTP",
        "ftp": "FTP",
        "webdav": "WebDAV",
        "azureblob": "Azure Blob Storage",
        "mega": "Mega.nz",
        "pcloud": "pCloud",
        "swift": "OpenStack Swift",
        "yandex": "Yandex Disk",
        "alias": "Alias",
        "local": "Local Disk"
    }
    return remote_type_display.get(remote_type, remote_type.upper())


def validate_raw_config(raw_config: str, remote_type: str) -> bool:
    """Validate raw rclone config format.
    
    Args:
        raw_config: The raw configuration text
        remote_type: The type of remote to validate
        
    Returns:
        bool: True if the config is valid
    """
    debug = Debug("RcloneUtils")
    
    # Kiểm tra định dạng cơ bản
    if not raw_config or "=" not in raw_config:
        debug.error("Invalid config format: missing key-value pairs")
        return False
        
    # Kiểm tra các thông số bắt buộc
    required_params = []
    if remote_type in ["drive", "dropbox", "onedrive", "box", "mega", "pcloud"]:
        required_params = ["token"]
        
    # Phân tích cấu hình thành các cặp key-value
    config_params = {}
    for line in raw_config.split("\n"):
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            config_params[key.strip()] = value.strip()
    
    # Kiểm tra các thông số bắt buộc
    for param in required_params:
        if param not in config_params:
            debug.error(f"Missing required parameter: {param}")
            return False
    
    # Kiểm tra định dạng token nếu có
    if "token" in config_params:
        token_value = config_params["token"]
        
        # Nếu token chứa *** (giá trị được che đi), không cần kiểm tra định dạng JSON
        if "***" in token_value:
            debug.info("Token contains masked values (***), skipping JSON validation")
        else:
            try:
                # Thử phân tích token dưới dạng JSON
                json.loads(token_value)
            except json.JSONDecodeError:
                debug.error("Invalid token format: not valid JSON")
                return False
    
    return True