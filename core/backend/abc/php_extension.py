# File: core/backend/abc/php_extension.py

from abc import ABC, abstractmethod

class PHPBaseExtension(ABC):
    @abstractmethod
    def get_id(self) -> str:
        """ID định danh extension, ví dụ: 'ioncube_loader'"""
        pass

    @abstractmethod
    def get_title(self) -> str:
        """Tên hiển thị thân thiện"""
        pass

    @abstractmethod
    def install(self, domain: str):
        """Cài đặt extension cho một domain cụ thể"""
        pass
    
    @abstractmethod
    def update_config(self, domain: str):
        """Cập nhật cấu hình cho extension"""
        pass

    def post_install(self, domain: str):
        """Hàm gọi sau khi cài đặt thành công"""
        pass