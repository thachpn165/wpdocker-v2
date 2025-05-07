"""
CLI commands cho remote operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style

from src.common.logging import info, error, debug, success
from src.features.rclone.utils.remote_utils import (
    get_remote_type_choices,
    prompt_remote_params,
    create_remote_choices,
    ensure_remotes_available
)

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

def add_remote() -> bool:
    """
    Thêm remote mới.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Chọn loại remote
        remote_type = questionary.select(
            "Select remote type",
            choices=get_remote_type_choices(),
            style=custom_style
        ).ask()
        
        if not remote_type:
            return False
            
        # Nhập tên remote
        name = questionary.text(
            "Enter remote name",
            style=custom_style
        ).ask()
        
        if not name:
            return False
            
        # Nhập tham số
        params = prompt_remote_params(remote_type)
        if not params:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Add remote '{name}' of type '{remote_type}'?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.add_remote(name, remote_type, params)
        
        success("Remote added successfully")
        return True
        
    except Exception as e:
        error(f"Failed to add remote: {str(e)}")
        return False

def remove_remote() -> bool:
    """
    Xóa remote.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra remote có sẵn
        if not ensure_remotes_available():
            return False
            
        # Chọn remote
        remote = questionary.select(
            "Select remote to remove",
            choices=create_remote_choices(),
            style=custom_style
        ).ask()
        
        if not remote:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Remove remote '{remote}'?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.remove_remote(remote)
        
        success("Remote removed successfully")
        return True
        
    except Exception as e:
        error(f"Failed to remove remote: {str(e)}")
        return False

def list_remotes() -> bool:
    """
    Liệt kê các remote.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        remotes = rclone_manager.list_remotes()
        
        if not remotes:
            info("No remotes found")
            return True
            
        # Hiển thị kết quả
        for remote in remotes:
            info(f"{remote['name']} ({remote['type']})")
            
        return True
        
    except Exception as e:
        error(f"Failed to list remotes: {str(e)}")
        return False

def show_remote_info() -> bool:
    """
    Hiển thị thông tin remote.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra remote có sẵn
        if not ensure_remotes_available():
            return False
            
        # Chọn remote
        remote = questionary.select(
            "Select remote",
            choices=create_remote_choices(),
            style=custom_style
        ).ask()
        
        if not remote:
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        info = rclone_manager.get_remote_info(remote)
        
        if not info:
            error("Failed to get remote info")
            return False
            
        # Hiển thị kết quả
        info(f"\nRemote: {info['name']}")
        info(f"Type: {info['type']}")
        info("Parameters:")
        for key, value in info['params'].items():
            info(f"  {key}: {value}")
            
        return True
        
    except Exception as e:
        error(f"Failed to show remote info: {str(e)}")
        return False 