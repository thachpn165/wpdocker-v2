"""
CLI commands cho system operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style
import platform
import subprocess
import os
import sys

from src.common.logging import info, error, debug, success

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

def check_installation() -> bool:
    """
    Kiểm tra cài đặt rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Thực hiện lệnh
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        version = rclone_manager.get_version()
        
        if not version:
            error("Rclone is not installed")
            return False
            
        # Hiển thị kết quả
        info(f"\nRclone version: {version}")
        info(f"Platform: {platform.system()} {platform.release()}")
        info(f"Python version: {sys.version}")
        
        return True
        
    except Exception as e:
        error(f"Failed to check installation: {str(e)}")
        return False

def install_rclone() -> bool:
    """
    Cài đặt rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra rclone đã cài đặt chưa
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        if rclone_manager.get_version():
            error("Rclone is already installed")
            return False
            
        # Xác nhận
        if not questionary.confirm(
            "Install rclone?",
            style=custom_style
        ).ask():
            return False
            
        # Cài đặt theo hệ điều hành
        system = platform.system().lower()
        
        if system == "linux":
            # Tải rclone
            subprocess.run([
                "curl", "-O", "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
            ], check=True)
            
            # Giải nén
            subprocess.run([
                "unzip", "rclone-current-linux-amd64.zip"
            ], check=True)
            
            # Di chuyển binary
            subprocess.run([
                "sudo", "mv", "rclone-*-linux-amd64/rclone", "/usr/local/bin/"
            ], check=True)
            
            # Cấp quyền thực thi
            subprocess.run([
                "sudo", "chmod", "+x", "/usr/local/bin/rclone"
            ], check=True)
            
            # Xóa file tạm
            subprocess.run([
                "rm", "-rf", "rclone-current-linux-amd64.zip", "rclone-*-linux-amd64"
            ], check=True)
            
        elif system == "darwin":
            # Cài đặt bằng Homebrew
            subprocess.run([
                "brew", "install", "rclone"
            ], check=True)
            
        elif system == "windows":
            # Tải rclone
            subprocess.run([
                "curl", "-O", "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
            ], check=True)
            
            # Giải nén
            subprocess.run([
                "powershell", "Expand-Archive", "rclone-current-windows-amd64.zip", "."
            ], check=True)
            
            # Di chuyển binary
            subprocess.run([
                "move", "rclone-*-windows-amd64\\rclone.exe", "%USERPROFILE%\\AppData\\Local\\Microsoft\\WindowsApps"
            ], check=True)
            
            # Xóa file tạm
            subprocess.run([
                "del", "rclone-current-windows-amd64.zip"
            ], check=True)
            subprocess.run([
                "rmdir", "/s", "/q", "rclone-*-windows-amd64"
            ], check=True)
            
        else:
            error(f"Unsupported platform: {system}")
            return False
            
        success("Rclone installed successfully")
        return True
        
    except Exception as e:
        error(f"Failed to install rclone: {str(e)}")
        return False

def update_rclone() -> bool:
    """
    Cập nhật rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra rclone đã cài đặt chưa
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        if not rclone_manager.get_version():
            error("Rclone is not installed")
            return False
            
        # Xác nhận
        if not questionary.confirm(
            "Update rclone?",
            style=custom_style
        ).ask():
            return False
            
        # Cập nhật theo hệ điều hành
        system = platform.system().lower()
        
        if system == "linux":
            # Tải rclone
            subprocess.run([
                "curl", "-O", "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
            ], check=True)
            
            # Giải nén
            subprocess.run([
                "unzip", "rclone-current-linux-amd64.zip"
            ], check=True)
            
            # Di chuyển binary
            subprocess.run([
                "sudo", "mv", "rclone-*-linux-amd64/rclone", "/usr/local/bin/"
            ], check=True)
            
            # Cấp quyền thực thi
            subprocess.run([
                "sudo", "chmod", "+x", "/usr/local/bin/rclone"
            ], check=True)
            
            # Xóa file tạm
            subprocess.run([
                "rm", "-rf", "rclone-current-linux-amd64.zip", "rclone-*-linux-amd64"
            ], check=True)
            
        elif system == "darwin":
            # Cập nhật bằng Homebrew
            subprocess.run([
                "brew", "upgrade", "rclone"
            ], check=True)
            
        elif system == "windows":
            # Tải rclone
            subprocess.run([
                "curl", "-O", "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
            ], check=True)
            
            # Giải nén
            subprocess.run([
                "powershell", "Expand-Archive", "rclone-current-windows-amd64.zip", "."
            ], check=True)
            
            # Di chuyển binary
            subprocess.run([
                "move", "rclone-*-windows-amd64\\rclone.exe", "%USERPROFILE%\\AppData\\Local\\Microsoft\\WindowsApps"
            ], check=True)
            
            # Xóa file tạm
            subprocess.run([
                "del", "rclone-current-windows-amd64.zip"
            ], check=True)
            subprocess.run([
                "rmdir", "/s", "/q", "rclone-*-windows-amd64"
            ], check=True)
            
        else:
            error(f"Unsupported platform: {system}")
            return False
            
        success("Rclone updated successfully")
        return True
        
    except Exception as e:
        error(f"Failed to update rclone: {str(e)}")
        return False

def uninstall_rclone() -> bool:
    """
    Gỡ cài đặt rclone.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra rclone đã cài đặt chưa
        from src.features.rclone.managers import RcloneManager
        rclone_manager = RcloneManager()
        
        if not rclone_manager.get_version():
            error("Rclone is not installed")
            return False
            
        # Xác nhận
        if not questionary.confirm(
            "Uninstall rclone?",
            style=custom_style
        ).ask():
            return False
            
        # Gỡ cài đặt theo hệ điều hành
        system = platform.system().lower()
        
        if system == "linux":
            # Xóa binary
            subprocess.run([
                "sudo", "rm", "/usr/local/bin/rclone"
            ], check=True)
            
        elif system == "darwin":
            # Gỡ cài đặt bằng Homebrew
            subprocess.run([
                "brew", "uninstall", "rclone"
            ], check=True)
            
        elif system == "windows":
            # Xóa binary
            subprocess.run([
                "del", "%USERPROFILE%\\AppData\\Local\\Microsoft\\WindowsApps\\rclone.exe"
            ], check=True)
            
        else:
            error(f"Unsupported platform: {system}")
            return False
            
        success("Rclone uninstalled successfully")
        return True
        
    except Exception as e:
        error(f"Failed to uninstall rclone: {str(e)}")
        return False 