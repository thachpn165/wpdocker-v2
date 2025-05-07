"""
Các hàm tiện ích cho prompts.
"""
from typing import List, Dict, Any, Optional, Callable
import questionary
from questionary import Style
from src.features.rclone.config.manager import RemoteConfig

from src.features.rclone.utils.file_utils import format_file_size
# Custom style cho questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),     # token in front of the question
    ('question', 'bold'),             # question text
    ('answer', 'fg:#f44336 bold'),    # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),   # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'),  # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),       # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),      # separator in lists
    ('instruction', ''),              # user instructions for select, rawselect, checkbox
    ('text', ''),                     # plain text
    ('disabled', 'fg:#858585 italic'), # disabled choices for select and checkbox prompts
])

def prompt_remote_name() -> Optional[str]:
    """
    Prompt người dùng nhập tên remote.
    
    Returns:
        Optional[str]: Tên remote hoặc None nếu hủy
    """
    return questionary.text(
        "Enter remote name:",
        validate=lambda text: True if text else "Remote name is required",
        style=custom_style
    ).ask()

def prompt_remote_type() -> Optional[str]:
    """
    Prompt người dùng chọn loại remote.
    
    Returns:
        Optional[str]: Loại remote hoặc None nếu hủy
    """
    choices = [
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
    
    return questionary.select(
        "Select remote type:",
        choices=choices,
        style=custom_style
    ).ask()

def prompt_remote_path(remote: str) -> Optional[str]:
    """
    Prompt người dùng nhập đường dẫn remote.
    
    Args:
        remote (str): Tên remote
        
    Returns:
        Optional[str]: Đường dẫn remote hoặc None nếu hủy
    """
    return questionary.text(
        f"Enter path on {remote}:",
        default="/",
        style=custom_style
    ).ask()

def prompt_local_path() -> Optional[str]:
    """
    Prompt người dùng nhập đường dẫn local.
    
    Returns:
        Optional[str]: Đường dẫn local hoặc None nếu hủy
    """
    return questionary.text(
        "Enter local path:",
        default=".",
        style=custom_style
    ).ask()

def prompt_confirm(message: str, default: bool = True) -> bool:
    """
    Prompt người dùng xác nhận.
    
    Args:
        message (str): Message cần xác nhận
        default (bool): Giá trị mặc định
        
    Returns:
        bool: True nếu xác nhận, False nếu không
    """
    return questionary.confirm(
        message,
        default=default,
        style=custom_style
    ).ask()

def prompt_select_remote(remotes: List[str], config_manager: Any) -> Optional[str]:
    """
    Prompt người dùng chọn remote.
    
    Args:
        remotes (List[str]): Danh sách tên remote
        config_manager: Manager để lấy thông tin remote
        
    Returns:
        Optional[str]: Tên remote được chọn hoặc None nếu hủy
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
    
    choices.append({"name": "Cancel", "value": "cancel"})
    
    return questionary.select(
        "Select remote:",
        choices=choices,
        style=custom_style
    ).ask()

def prompt_select_file(files: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Prompt người dùng chọn file.
    
    Args:
        files (List[Dict[str, Any]]): Danh sách thông tin file
        
    Returns:
        Optional[Dict[str, Any]]: Thông tin file được chọn hoặc None nếu hủy
    """
    choices = []
    for file_info in files:
        name = file_info.get('Name', '')
        size = format_file_size(file_info.get('Size', 0))
        
        if file_info.get('IsDir', False):
            choices.append({
                "name": f"📁 {name}/",
                "value": file_info
            })
        else:
            choices.append({
                "name": f"📄 {name} ({size})",
                "value": file_info
            })
    
    choices.append({"name": "Cancel", "value": None})
    
    return questionary.select(
        "Select file:",
        choices=choices,
        style=custom_style
    ).ask() 