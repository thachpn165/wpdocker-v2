"""
Các hàm tiện ích cho CLI commands.
"""
from typing import List, Dict, Any, Optional, Tuple
import subprocess
import json
import os

from src.common.logging import info, error, debug
from src.common.utils.environment import env

def run_rclone_command(args: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """
    Chạy lệnh rclone và trả về kết quả.
    
    Args:
        args (List[str]): Danh sách tham số cho lệnh rclone
        capture_output (bool): Có capture output hay không
        
    Returns:
        Tuple[int, str, str]: (exit code, stdout, stderr)
    """
    try:
        # Thêm --progress=false để tránh hiển thị progress bar
        if '--progress' not in args:
            args.append('--progress=false')
            
        # Thêm --config nếu có
        config_path = env.get('RCLONE_CONFIG')
        if config_path and '--config' not in args:
            args.extend(['--config', config_path])
            
        # Chạy lệnh
        result = subprocess.run(
            ['rclone'] + args,
            capture_output=capture_output,
            text=True,
            check=False
        )
        
        return result.returncode, result.stdout, result.stderr
        
    except Exception as e:
        error(f"Failed to run rclone command: {str(e)}")
        return 1, '', str(e)

def parse_json_output(output: str) -> Optional[Dict[str, Any]]:
    """
    Parse output dạng JSON từ rclone.
    
    Args:
        output (str): Output từ lệnh rclone
        
    Returns:
        Optional[Dict[str, Any]]: Dữ liệu đã parse hoặc None nếu lỗi
    """
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None

def format_transfer_stats(stats: Dict[str, Any]) -> str:
    """
    Format thống kê transfer thành chuỗi hiển thị.
    
    Args:
        stats (Dict[str, Any]): Thống kê transfer
        
    Returns:
        str: Chuỗi thống kê đã format
    """
    transferred = stats.get('transferred', 0)
    total = stats.get('total', 0)
    speed = stats.get('speed', 0)
    eta = stats.get('eta', 0)
    
    # Format kích thước
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    # Format tốc độ
    def format_speed(speed):
        return f"{format_size(speed)}/s"
    
    # Format thời gian
    def format_time(seconds):
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    return (
        f"Transferred: {format_size(transferred)} / {format_size(total)} "
        f"({(transferred/total*100):.1f}%) "
        f"Speed: {format_speed(speed)} "
        f"ETA: {format_time(eta)}"
    )

def get_rclone_version() -> Optional[str]:
    """
    Lấy phiên bản rclone.
    
    Returns:
        Optional[str]: Phiên bản rclone hoặc None nếu lỗi
    """
    code, stdout, stderr = run_rclone_command(['version'])
    if code == 0:
        # Parse version từ output
        for line in stdout.split('\n'):
            if line.startswith('rclone v'):
                return line.split()[1]
    return None

def check_rclone_installed() -> bool:
    """
    Kiểm tra rclone đã được cài đặt chưa.
    
    Returns:
        bool: True nếu đã cài đặt, False nếu chưa
    """
    try:
        subprocess.run(['rclone', 'version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False 