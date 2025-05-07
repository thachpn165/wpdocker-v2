"""
CLI commands cho file operations.
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
    format_file_size,
    ensure_local_dir
)
from src.features.rclone.utils.prompt_utils import (
    prompt_remote_path,
    prompt_local_path,
    prompt_confirm,
    prompt_select_remote,
    prompt_select_file
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

def list_files() -> bool:
    """
    Liệt kê các file trong remote.
    
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
            
        # Nhập đường dẫn
        path = questionary.text(
            "Enter path (leave empty for root)",
            style=custom_style
        ).ask()
        
        if path is None:
            return False
            
        # Thực hiện lệnh
        rclone_manager = RcloneManager()
        
        files = rclone_manager.list_files(remote, path)
        
        if not files:
            info("No files found")
            return True
            
        # Hiển thị kết quả
        for file in files:
            size = format_file_size(file["Size"])
            info(f"{file['Path']} ({size})")
            
        return True
        
    except Exception as e:
        error(f"Failed to list files: {str(e)}")
        return False

def copy_file() -> bool:
    """
    Sao chép file giữa các remote.
    
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
            f"Copy {source_remote}:{source_path} to {dest_remote}:{dest_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        rclone_manager = RcloneManager()
        
        rclone_manager.copy_file(source_remote, source_path, dest_remote, dest_path)
        
        success("File copied successfully")
        return True
        
    except Exception as e:
        error(f"Failed to copy file: {str(e)}")
        return False

def move_file() -> bool:
    """
    Di chuyển file giữa các remote.
    
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
            f"Move {source_remote}:{source_path} to {dest_remote}:{dest_path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        rclone_manager = RcloneManager()
        
        rclone_manager.move_file(source_remote, source_path, dest_remote, dest_path)
        
        success("File moved successfully")
        return True
        
    except Exception as e:
        error(f"Failed to move file: {str(e)}")
        return False

def delete_file() -> bool:
    """
    Xóa file trong remote.
    
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
            
        # Nhập đường dẫn
        path = questionary.text(
            "Enter path",
            style=custom_style
        ).ask()
        
        if not path:
            return False
            
        # Xác nhận
        if not questionary.confirm(
            f"Delete {remote}:{path}?",
            style=custom_style
        ).ask():
            return False
            
        # Thực hiện lệnh
        rclone_manager = RcloneManager()
        
        rclone_manager.delete_file(remote, path)
        
        success("File deleted successfully")
        return True
        
    except Exception as e:
        error(f"Failed to delete file: {str(e)}")
        return False 