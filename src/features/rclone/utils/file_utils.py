"""
Các hàm tiện ích cho file operations.
"""
from typing import List, Dict, Any, Optional, Tuple
import os
import re
from pathlib import Path

from src.common.logging import info, error, debug
from src.common.utils.environment import env

def parse_remote_path(path: str) -> Tuple[str, str]:
    """
    Parse đường dẫn remote thành tên remote và path.
    
    Args:
        path (str): Đường dẫn remote (ví dụ: remote:path/to/file)
        
    Returns:
        Tuple[str, str]: (tên remote, path)
    """
    if ':' not in path:
        return '', path
        
    remote, remote_path = path.split(':', 1)
    return remote, remote_path

def format_file_size(size: int) -> str:
    """
    Format kích thước file thành chuỗi dễ đọc.
    
    Args:
        size (int): Kích thước file tính bằng bytes
        
    Returns:
        str: Chuỗi kích thước đã format
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def format_file_info(file_info: Dict[str, Any]) -> str:
    """
    Format thông tin file thành chuỗi hiển thị.
    
    Args:
        file_info (Dict[str, Any]): Thông tin file
        
    Returns:
        str: Chuỗi thông tin đã format
    """
    name = file_info.get('Name', '')
    size = format_file_size(file_info.get('Size', 0))
    mod_time = file_info.get('ModTime', '')
    
    if file_info.get('IsDir', False):
        return f"📁 {name}/"
    return f"📄 {name} ({size})"

def get_local_path(path: str) -> str:
    """
    Lấy đường dẫn local từ đường dẫn tương đối.
    
    Args:
        path (str): Đường dẫn tương đối
        
    Returns:
        str: Đường dẫn local đầy đủ
    """
    base_dir = env.get('WPDOCKER_BASE_DIR', os.getcwd())
    return os.path.join(base_dir, path)

def ensure_local_dir(path: str) -> bool:
    """
    Đảm bảo thư mục local tồn tại.
    
    Args:
        path (str): Đường dẫn thư mục
        
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        error(f"Failed to create directory {path}: {str(e)}")
        return False

def sanitize_path(path: str) -> str:
    """
    Làm sạch đường dẫn, loại bỏ các ký tự không hợp lệ.
    
    Args:
        path (str): Đường dẫn cần làm sạch
        
    Returns:
        str: Đường dẫn đã làm sạch
    """
    # Loại bỏ các ký tự không hợp lệ
    path = re.sub(r'[<>:"|?*]', '', path)
    # Loại bỏ các dấu / ở đầu và cuối
    path = path.strip('/')
    return path

def get_relative_path(path: str, base_dir: str) -> str:
    """
    Lấy đường dẫn tương đối từ đường dẫn đầy đủ.
    
    Args:
        path (str): Đường dẫn đầy đủ
        base_dir (str): Thư mục gốc
        
    Returns:
        str: Đường dẫn tương đối
    """
    try:
        return os.path.relpath(path, base_dir)
    except ValueError:
        return path 