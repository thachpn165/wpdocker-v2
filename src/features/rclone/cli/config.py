"""
CLI commands cho config operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style
import os
import tempfile

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

def show_config() -> bool:
    """
    Hiển thị cấu hình rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        config = rclone_manager.get_config()
        
        if not config:
            error("Failed to get config")
            return False
            
        # Hiển thị kết quả
        info("\nRclone Configuration:")
        for key, value in config.items():
            info(f"{key}: {value}")
            
        return True
        
    except Exception as e:
        error(f"Failed to show config: {str(e)}")
        return False

def show_remote_config() -> bool:
    """
    Hiển thị cấu hình của remote.
    
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
        
        config = rclone_manager.get_remote_config(remote)
        
        if not config:
            error("Failed to get remote config")
            return False
            
        # Hiển thị kết quả
        info(f"\nRemote: {remote}")
        info("Configuration:")
        for key, value in config.items():
            info(f"  {key}: {value}")
            
        return True
        
    except Exception as e:
        error(f"Failed to show remote config: {str(e)}")
        return False

def edit_config() -> bool:
    """
    Chỉnh sửa cấu hình rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        config_path = rclone_manager.get_config_path()
        
        if not config_path:
            error("Failed to get config path")
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Edit config file at {config_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Mở file trong editor
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {config_path}")
        
        success("Config edited successfully")
        return True
        
    except Exception as e:
        error(f"Failed to edit config: {str(e)}")
        return False

def edit_remote_config() -> bool:
    """
    Chỉnh sửa cấu hình của remote.
    
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
        
        config = rclone_manager.get_remote_config(remote)
        
        if not config:
            error("Failed to get remote config")
            return False
            
        # Tạo file tạm
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".conf", delete=False) as f:
            for key, value in config.items():
                f.write(f"{key} = {value}\n")
            temp_path = f.name
            
        # Xác nhận
        if not questionary.confirm(
            f"Edit config for remote '{remote}'?",
            style=custom_style
        ).ask():
            os.unlink(temp_path)
            return False
            
        # Mở file trong editor
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {temp_path}")
        
        # Đọc file đã chỉnh sửa
        new_config = {}
        with open(temp_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    new_config[key.strip()] = value.strip()
                    
        # Xóa file tạm
        os.unlink(temp_path)
        
        # Cập nhật cấu hình
        rclone_manager.update_remote_config(remote, new_config)
        
        success("Remote config edited successfully")
        return True
        
    except Exception as e:
        error(f"Failed to edit remote config: {str(e)}")
        return False 