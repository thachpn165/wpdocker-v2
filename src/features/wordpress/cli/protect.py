"""
CLI commands for WordPress login protection.

This module provides CLI commands for enabling and disabling wp-login.php protection
using HTTP Basic Authentication.
"""

import click
from typing import Optional
from src.common.logging import success, error, info
from src.features.website.utils import select_website
from src.features.wordpress.actions import toggle_wp_login_protection


def cli_toggle_wp_login_protection(domain: Optional[str] = None, interactive: bool = True) -> bool:
    """
    Bật/tắt tính năng bảo vệ wp-login.php cho một website.
    
    Args:
        domain: Tên miền website, None để chọn từ danh sách
        interactive: True nếu đang chạy trong chế độ tương tác
        
    Returns:
        True nếu thành công, False nếu có lỗi
    """
    if domain is None:
        domain = select_website("Chọn website cần thay đổi bảo vệ wp-login.php:")
        if not domain:
            if interactive:
                info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
            return False
    
    # Gọi hàm toggle và lấy kết quả
    success_flag, new_status, login_info = toggle_wp_login_protection(domain)
    
    if success_flag:
        if new_status:
            # Nếu bật bảo vệ, hiển thị thông tin đăng nhập
            username, password = login_info
            success(f"✅ Đã bật bảo vệ wp-login.php cho {domain}")
            info("ℹ️ Thông tin đăng nhập:")
            info(f"   Tên đăng nhập: {username}")
            info(f"   Mật khẩu: {password}")
            info("🔐 Hãy lưu thông tin này ở nơi an toàn!")
        else:
            success(f"✅ Đã tắt bảo vệ wp-login.php cho {domain}")
    else:
        error(f"❌ Không thể thay đổi trạng thái bảo vệ wp-login.php cho {domain}")
    
    return success_flag


@click.command()
@click.argument("domain", required=False)
def protect_command(domain: Optional[str] = None):
    """Bật/tắt tính năng bảo vệ wp-login.php cho một website."""
    cli_toggle_wp_login_protection(domain)