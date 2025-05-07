"""
CLI commands cho sync operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style

from src.common.logging import info, error, debug, success
from src.common.utils.environment import env
from src.features.rclone.manager import RcloneManager
from src.features.rclone.config.manager import RcloneConfigManager
from src.features.rclone.utils.remote_utils import (
    get_remote_type_choices,
    prompt_remote_params,
    create_remote_choices,
    ensure_remotes_available
)
from src.features.rclone.utils.file_utils import (
    parse_remote_path,
    get_local_path,
    ensure_local_dir,
    sanitize_path
)
from src.features.rclone.utils.prompt_utils import (
    prompt_remote_path,
    prompt_local_path,
    prompt_confirm,
    prompt_select_remote
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

def sync_to_remote() -> bool:
    """
    Sync từ local đến remote.
    
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
            
        # Nhập đường dẫn local
        local_path = questionary.text(
            "Enter local path",
            style=custom_style
        ).ask()
        
        if not local_path:
            return False
            
        # Nhập đường dẫn remote
        remote_path = questionary.text(
            "Enter remote path",
            style=custom_style
        ).ask()
        
        if not remote_path:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Sync {local_path} to {remote}:{remote_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.sync_to_remote(local_path, remote, remote_path)
        
        success("Sync completed successfully")
        return True
        
    except Exception as e:
        error(f"Failed to sync to remote: {str(e)}")
        return False

def sync_from_remote() -> bool:
    """
    Sync từ remote đến local.
    
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
            f"Sync {remote}:{remote_path} to {local_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.sync_from_remote(remote, remote_path, local_path)
        
        success("Sync completed successfully")
        return True
        
    except Exception as e:
        error(f"Failed to sync from remote: {str(e)}")
        return False

def sync_between_remotes() -> bool:
    """
    Sync giữa các remote.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra remote có sẵn
        if not ensure_remotes_available():
            return False
            
        # Chọn remote nguồn
        source_remote = questionary.select(
            "Select source remote",
            choices=create_remote_choices(),
            style=custom_style
        ).ask()
        
        if not source_remote:
            return False
            
        # Nhập đường dẫn nguồn
        source_path = questionary.text(
            "Enter source path",
            style=custom_style
        ).ask()
        
        if not source_path:
            return False
            
        # Chọn remote đích
        dest_remote = questionary.select(
            "Select destination remote",
            choices=create_remote_choices(),
            style=custom_style
        ).ask()
        
        if not dest_remote:
            return False
            
        # Nhập đường dẫn đích
        dest_path = questionary.text(
            "Enter destination path",
            style=custom_style
        ).ask()
        
        if not dest_path:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Sync {source_remote}:{source_path} to {dest_remote}:{dest_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        rclone_manager.sync_between_remotes(source_remote, source_path, dest_remote, dest_path)
        
        success("Sync completed successfully")
        return True
        
    except Exception as e:
        error(f"Failed to sync between remotes: {str(e)}")
        return False 