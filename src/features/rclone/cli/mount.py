"""
CLI commands cho mount operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style
import signal
import sys

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

def mount_remote() -> bool:
    """
    Mount remote vào local path.
    
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
            
        # Nhập đường dẫn remote
        remote_path = questionary.text(
            "Enter remote path",
            style=custom_style
        ).ask()
        
        if not remote_path:
            return False
            
        # Nhập đường dẫn local
        local_path = questionary.text(
            "Enter local path",
            style=custom_style
        ).ask()
        
        if not local_path:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Mount {remote}:{remote_path} to {local_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        # Xử lý signal để unmount khi thoát
        def signal_handler(sig, frame):
            info("\nUnmounting...")
            rclone_manager.unmount_remote(local_path)
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Mount
        rclone_manager.mount_remote(remote, remote_path, local_path)
        
        success("Remote mounted successfully")
        return True
        
    except Exception as e:
        error(f"Failed to mount remote: {str(e)}")
        return False

def unmount_remote() -> bool:
    """
    Unmount remote từ local path.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Nhập đường dẫn local
        local_path = questionary.text(
            "Enter local path",
            style=custom_style
        ).ask()
        
        if not local_path:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Unmount {local_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.unmount_remote(local_path)
        
        success("Remote unmounted successfully")
        return True
        
    except Exception as e:
        error(f"Failed to unmount remote: {str(e)}")
        return False

def list_mounts() -> bool:
    """
    Liệt kê các mount points.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        mounts = rclone_manager.list_mounts()
        
        if not mounts:
            info("No mounts found")
            return True
            
        # Hiển thị kết quả
        for mount in mounts:
            info(f"{mount['remote']}:{mount['remote_path']} -> {mount['local_path']}")
            
        return True
        
    except Exception as e:
        error(f"Failed to list mounts: {str(e)}")
        return False 