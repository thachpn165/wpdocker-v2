"""
Remote utility functions for the rclone feature.

This module provides helper functions for working with Rclone remotes,
reducing code duplication and improving maintainability.
"""

import os
import questionary
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import tempfile
import subprocess

from src.common.logging import info, error, debug, success
from src.common.utils.environment import env
from src.common.ui.prompt_helpers import wait_for_enter, custom_style, prompt_with_cancel
from src.features.rclone.manager import RcloneManager
from src.features.rclone.config.manager import RcloneConfigManager
from src.features.rclone.models.remote import RemoteConfig
from src.common.utils.editor import choose_editor


def format_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.2f} MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f} GB"


def get_remote_type_display_name(remote_type: str) -> str:
    """
    Get a user-friendly display name for a remote type.
    
    Args:
        remote_type: The internal type name used by rclone
        
    Returns:
        str: A user-friendly display name
    """
    display_names = {
        "s3": "Amazon S3 / Wasabi / DO Spaces",
        "drive": "Google Drive",
        "dropbox": "Dropbox",
        "onedrive": "Microsoft OneDrive",
        "b2": "Backblaze B2",
        "box": "Box",
        "sftp": "SFTP",
        "ftp": "FTP",
        "webdav": "WebDAV",
        "azureblob": "Azure Blob Storage",
        "mega": "Mega.nz",
        "pcloud": "pCloud",
        "swift": "OpenStack Swift",
        "yandex": "Yandex Disk",
        "local": "Local Disk"
    }
    return display_names.get(remote_type, remote_type.capitalize())


def get_remote_type_choices() -> List[Dict[str, str]]:
    """Lấy danh sách các loại remote có sẵn."""
    return [
        {"name": "S3 (Amazon S3, Wasabi, etc.)", "value": "s3"},
        {"name": "Google Drive", "value": "drive"},
        {"name": "Dropbox", "value": "dropbox"},
        {"name": "Microsoft OneDrive", "value": "onedrive"},
        {"name": "SFTP", "value": "sftp"},
        {"name": "FTP", "value": "ftp"},
        {"name": "WebDAV / Nextcloud", "value": "webdav"},
        {"name": "Backblaze B2", "value": "b2"},
        {"name": "Box", "value": "box"},
        {"name": "Azure Blob Storage", "value": "azureblob"},
        {"name": "Cancel", "value": "cancel"}
    ]


def prompt_remote_params(remote_type: str) -> Dict[str, str]:
    """
    Lấy thông tin cấu hình cho remote.
    
    Args:
        remote_type (str): Loại remote
        
    Returns:
        Dict[str, str]: Thông tin cấu hình
    """
    params = {}
    
    # Hỏi người dùng có muốn nhập cấu hình thủ công không
    use_manual_config = questionary.confirm(
        "Do you have a configuration from your local machine to paste?",
        style=custom_style,
        default=True
    ).ask()
    
    if use_manual_config:
        # Tạo file tạm để người dùng nhập cấu hình
        with tempfile.NamedTemporaryFile(suffix='.conf', delete=False, mode='w+') as temp_file:
            temp_path = temp_file.name
            # Tạo template cho người dùng
            temp_file.write(f"# Paste your {remote_type} configuration below, do not include the remote name [xxx]\n")
            temp_file.write(f"# Example for {remote_type}:\n")
            temp_file.write(f"type = {remote_type}\n")
            temp_file.write('token = {"access_token":"xxxxxx","token_type":"Bearer","refresh_token":"xxxxxx","expiry":"2025-12-31T12:00:00Z"}\n')
            temp_file.write("client_id = xxxxxx\n")
            temp_file.write("client_secret = xxxxxx\n")
            temp_file.write("# Delete these lines and paste your actual configuration here\n")
        
        info("\nAfter the editor opens:")
        info("- Paste your Rclone configuration")
        info("- Delete the guide lines (starting with #)")
        info("- Save and close the editor to continue")
        
        # Chọn và mở editor
        default_editor = env.get("EDITOR")
        editor = choose_editor(default_editor)
        
        # Hủy nếu người dùng không chọn editor
        if not editor:
            os.unlink(temp_path)
            info("\n❌ Configuration entry canceled.")
            return {}
        
        # Mở editor
        subprocess.run([editor, temp_path])
        
        # Đọc cấu hình từ file
        with open(temp_path, 'r') as f:
            config_content = f.read()
        
        # Xóa file tạm
        os.unlink(temp_path)
        
        # Parse cấu hình
        for line in config_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    params[key.strip()] = value.strip()
    else:
        # TODO: Implement interactive parameter collection for each remote type
        error("🚧 Interactive parameter collection not implemented yet")
        return {}
    
    return params


def ensure_remotes_available(rclone_manager: RcloneManager) -> List[str]:
    """
    Kiểm tra và lấy danh sách remote có sẵn.
    
    Args:
        rclone_manager: Manager để quản lý remote
        
    Returns:
        List[str]: Danh sách tên remote
    """
    remotes = rclone_manager.list_remotes()
    if not remotes:
        error("❌ No remotes configured. Please add a remote first.")
        return []
    return remotes


def create_remote_choices(remotes: List[str], config_manager: Any) -> List[Dict[str, str]]:
    """
    Tạo danh sách lựa chọn cho remote.
    
    Args:
        remotes (List[str]): Danh sách tên remote
        config_manager: Manager để lấy thông tin remote
        
    Returns:
        List[Dict[str, str]]: Danh sách lựa chọn
    """
    choices = []
    for remote in remotes:
        config = config_manager.get_remote_config(remote)
        if config:
            remote_type = config.get("type", "unknown")
            display_type = RemoteConfig.get_display_type(remote_type)
            choices.append({
                "name": f"{remote} ({display_type})",
                "value": remote
            })
    return choices


def select_remote(remotes: List[str], prompt_text: str = "Select remote:", 
                 config_manager=None) -> Optional[str]:
    """
    Prompt the user to select a remote from a list.
    
    Args:
        remotes: List of remote names
        prompt_text: Text to display in the prompt
        config_manager: Optional RcloneConfigManager instance for detailed display
        
    Returns:
        Selected remote name or None if canceled
    """
    remote_choices = create_remote_choices(remotes, config_manager)
    return prompt_with_cancel(remote_choices, prompt_text)


def select_website(prompt_text: str = "Select website:") -> Optional[str]:
    """
    Prompt the user to select a website from available domains.
    
    Args:
        prompt_text: Text to display in the prompt
        
    Returns:
        Selected website name or None if canceled
    """
    available_domains = get_available_websites()
    
    if not available_domains:
        # No domains found, ask for manual entry
        website_name = questionary.text(
            "Enter website name (no websites found):",
            style=custom_style
        ).ask()
        return website_name
    
    # Create choices including a custom option
    domain_choices = [{"name": domain, "value": domain} for domain in available_domains]
    domain_choices.append({"name": "Enter custom domain name", "value": "custom"})
    domain_choices.append({"name": "Cancel", "value": "cancel"})
    
    domain_selection = questionary.select(
        prompt_text,
        choices=domain_choices,
        style=custom_style
    ).ask()
    
    if domain_selection == "cancel":
        return None
    
    if domain_selection == "custom":
        website_name = questionary.text(
            "Enter website name:",
            style=custom_style
        ).ask()
        return website_name
    
    return domain_selection


def create_directory_structure(rclone_manager: RcloneManager, 
                               remote_name: str, 
                               remote_path: str) -> bool:
    """
    Create a directory structure in a remote.
    
    Args:
        rclone_manager: An instance of RcloneManager
        remote_name: Name of the remote
        remote_path: Path to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Break path into components
    remote_components = remote_path.split('/')
    current_path = ""
    
    for component in remote_components:
        if component:
            current_path = f"{current_path}/{component}" if current_path else component
            mkdir_success, mkdir_message = rclone_manager.execute_command(
                ["mkdir", f"{remote_name}:{current_path}"]
            )
            # Don't show a warning if the directory already exists
            if not mkdir_success and "already exists" not in mkdir_message.lower():
                debug(f"Unable to create directory '{current_path}': {mkdir_message}")
                return False
    
    return True


def get_available_websites() -> List[str]:
    """
    Get a list of available website directories.
    
    Returns:
        List of website directory names
    """
    available_domains = []
    sites_dir = env.get("SITES_DIR")
    
    if sites_dir and os.path.exists(sites_dir):
        available_domains = [d for d in os.listdir(sites_dir) 
                             if os.path.isdir(os.path.join(sites_dir, d))]
    
    return available_domains


def get_backup_files_for_website(website_name: str) -> List[Dict]:
    """
    Get a list of backup files for a specific website.
    
    Args:
        website_name: Name of the website
        
    Returns:
        List of dictionaries containing file information
    """
    backup_files = []
    sites_dir = env.get("SITES_DIR")
    
    if sites_dir and os.path.exists(os.path.join(sites_dir, website_name)):
        site_backups_dir = os.path.join(sites_dir, website_name, "backups")
        if os.path.exists(site_backups_dir):
            # List backup files in the backups directory
            backup_files_list = [f for f in os.listdir(site_backups_dir) 
                                 if os.path.isfile(os.path.join(site_backups_dir, f)) and 
                                 (f.endswith('.zip') or f.endswith('.tar.gz') or f.endswith('.sql'))]
            
            if backup_files_list:
                # Sort by modification time, newest first
                backup_files_list.sort(key=lambda x: os.path.getmtime(os.path.join(site_backups_dir, x)), 
                                       reverse=True)
                
                # Create list of files with dates
                for f in backup_files_list:
                    file_path = os.path.join(site_backups_dir, f)
                    mtime = os.path.getmtime(file_path)
                    date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    size = os.path.getsize(file_path)
                    size_str = format_size(size)
                    
                    backup_files.append({
                        "name": f"{f} ({size_str}, {date_str})",
                        "value": file_path,
                        "file_name": f,
                        "size": size,
                        "date": date_str
                    })
    
    return backup_files


def select_backup_file(website_name: str, prompt_text: str = "Select backup file:") -> Optional[str]:
    """
    Prompt the user to select a backup file for a website.
    
    Args:
        website_name: Name of the website
        prompt_text: Text to display in the prompt
        
    Returns:
        Path to the selected backup file or None if canceled
    """
    backup_files = get_backup_files_for_website(website_name)
    
    if not backup_files:
        # No backup files found, ask for manual entry
        sites_dir = env.get("SITES_DIR")
        default_path = ""
        
        if sites_dir and os.path.exists(os.path.join(sites_dir, website_name)):
            site_backups_dir = os.path.join(sites_dir, website_name, "backups")
            if os.path.exists(site_backups_dir):
                default_path = site_backups_dir
        
        backup_path = questionary.text(
            "Enter local backup file path (absolute path):",
            default=default_path,
            style=custom_style
        ).ask()
        
        return backup_path
    
    # Create choices for backup files
    backup_choices = [{"name": file["name"], "value": file["value"]} for file in backup_files]
    backup_choices.append({"name": "Enter path manually", "value": "manual"})
    backup_choices.append({"name": "Cancel", "value": "cancel"})
    
    backup_selection = questionary.select(
        prompt_text,
        choices=backup_choices,
        style=custom_style
    ).ask()
    
    if backup_selection == "cancel":
        return None
    
    if backup_selection == "manual":
        backup_path = questionary.text(
            "Enter local backup file path (absolute path):",
            style=custom_style
        ).ask()
        return backup_path
    
    return backup_selection


def process_backup_files(files: List[Dict], path: str, rclone_manager: RcloneManager, 
                       remote_name: str, level: int = 0) -> List[Dict]:
    """
    Process backup files and build a structured list of choices with metadata.
    
    Args:
        files: List of file information dictionaries
        path: Current path
        rclone_manager: RcloneManager instance for listing subdirectories
        remote_name: Name of the remote
        level: Current indentation level for nested displays
        
    Returns:
        List of formatted choice dictionaries
    """
    choices = []
    
    # Add direct files
    for file_info in [f for f in files if not f.get("IsDir", False)]:
        file_name = file_info.get("Name", "Unknown")
        file_size = file_info.get("Size", 0)
        size_str = format_size(file_size)
        mod_time = file_info.get("ModTime", "Unknown")
        
        indent = "  " * level
        choices.append({
            "name": f"{indent}📄 {file_name} ({size_str}) - {mod_time}",
            "value": f"{path}/{file_name}"
        })
    
    # Process subdirectories
    for file_info in [f for f in files if f.get("IsDir", False)]:
        dir_name = file_info.get("Name", "Unknown")
        subdir_path = f"{path}/{dir_name}"
        
        # Add directory as a choice
        indent = "  " * level
        choices.append({
            "name": f"{indent}📁 {dir_name}/",
            "value": f"dir:{subdir_path}"
        })
        
        # Get files in subdirectory
        subdir_files = rclone_manager.list_files(remote_name, subdir_path)
        
        # If directory not empty, process top few items
        if subdir_files:
            # Limit to first few files to avoid overwhelming the menu
            for subfile in subdir_files[:3]:
                if not subfile.get("IsDir", False):
                    subfile_name = subfile.get("Name", "Unknown")
                    subfile_size = subfile.get("Size", 0)
                    subsize_str = format_size(subfile_size)
                    subfile_mod_time = subfile.get("ModTime", "Unknown")
                    
                    choices.append({
                        "name": f"{indent}  └─ 📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                        "value": f"{subdir_path}/{subfile_name}"
                    })
            
            # If there are more files, show a count
            if len(subdir_files) > 3:
                choices.append({
                    "name": f"{indent}  └─ ... {len(subdir_files) - 3} more items",
                    "value": f"more:{subdir_path}"
                })
    
    return choices


def validate_backup_path(path: str, must_exist: bool = True) -> bool:
    """
    Validate a backup file path.
    
    Args:
        path: Path to validate
        must_exist: Whether the file must exist on disk
        
    Returns:
        bool: True if path is valid, False otherwise
    """
    if not path:
        error("❌ Backup path cannot be empty")
        return False
    
    if must_exist and not os.path.exists(path):
        error(f"❌ Backup file does not exist: {path}")
        return False
    
    # Check that it's not a directory if it exists
    if must_exist and os.path.isdir(path):
        error(f"❌ Path is a directory, not a file: {path}")
        return False
    
    # Check if it has a valid backup extension
    valid_extensions = ['.zip', '.tar.gz', '.tgz', '.sql', '.gz']
    if not any(path.endswith(ext) for ext in valid_extensions):
        error(f"❌ File does not have a valid backup extension: {path}")
        error("   Valid extensions are: .zip, .tar.gz, .tgz, .sql, .gz")
        return False
    
    return True


def execute_rclone_operation(
    operation: Callable[[], Tuple[bool, str]], 
    success_msg: str, 
    error_prefix: str
) -> bool:
    """
    Execute an Rclone operation with consistent success/error handling.
    
    Args:
        operation: Function to execute that returns (success, message)
        success_msg: Message to show on success
        error_prefix: Prefix for error message
        
    Returns:
        bool: True if operation succeeded, False otherwise
    """
    try:
        success_result, message = operation()
        
        if success_result:
            success(f"✅ {success_msg}")
            if message:
                info(message)
            return True
        else:
            error(f"❌ {error_prefix}: {message}")
            return False
    except Exception as e:
        error(f"❌ {error_prefix}: {str(e)}")
        debug(f"Exception details: {type(e).__name__}: {str(e)}")
        return False