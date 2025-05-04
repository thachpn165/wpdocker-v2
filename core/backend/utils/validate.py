# File: core/backend/utils/validate.py
from core.backend.utils.debug import debug

def _is_valid_domain(domain: str) -> bool:
    import re
    """
    Kiểm tra tính hợp lệ của tên miền:
    - Không trống
    - Tối đa 254 ký tự
    - Không có khoảng trắng
    - Không bắt đầu hoặc kết thúc bằng dấu chấm
    - Có định dạng hợp lệ dạng sub.example.com
    """
    if not domain:
        return False
    if len(domain) > 254:
        return False
    if domain.startswith('.') or domain.endswith('.'):
        return False
    if domain.startswith('www.'):
        return False
    if ' ' in domain:
        return False

    domain_regex = re.compile(
        r"^(?!-)([a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,}$"
    )
    return bool(domain_regex.match(domain))

# Check if the system is ARM
def _is_arm() -> bool:
    """
    Kiểm tra xem hệ thống có phải là ARM hay không.
    """
    import platform
    arch = platform.machine()
    arm = arch.startswith('arm') or arch.startswith('aarch64')
    if arm:
        debug(f"⚠️ Hệ thống ARM phát hiện: {arch}")
        return True
    return False

def validate_directory(directory_path: str) -> bool:
    """
    Kiểm tra và tạo thư mục nếu chưa tồn tại.
    
    Args:
        directory_path: Đường dẫn đến thư mục cần kiểm tra và tạo
        
    Returns:
        True nếu thư mục đã tồn tại hoặc được tạo thành công
    """
    import os
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
            debug(f"✅ Đã tạo thư mục: {directory_path}")
            return True
        except Exception as e:
            debug(f"❌ Không thể tạo thư mục {directory_path}: {e}")
            return False
    return True