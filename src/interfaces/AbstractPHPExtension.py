#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Định nghĩa lớp trừu tượng AbstractPHPExtension cho các extensions PHP.
"""
from abc import ABC, abstractmethod

class AbstractPHPExtension(ABC):
    """
    Lớp trừu tượng cho các extensions PHP.
    
    Định nghĩa giao diện chuẩn để triển khai các PHP extensions.
    """
    
    @abstractmethod
    def get_id(self) -> str:
        """
        Trả về ID định danh extension.
        
        Returns:
            str: ID định danh extension, ví dụ: 'ioncube_loader'
        """
        pass

    @abstractmethod
    def get_title(self) -> str:
        """
        Trả về tên hiển thị thân thiện của extension.
        
        Returns:
            str: Tên hiển thị thân thiện
        """
        pass

    @abstractmethod
    def install(self, domain: str):
        """
        Cài đặt extension cho một domain cụ thể.
        
        Args:
            domain (str): Tên miền cần cài đặt extension
        
        Returns:
            bool: True nếu cài đặt thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def update_config(self, domain: str):
        """
        Cập nhật cấu hình cho extension.
        
        Args:
            domain (str): Tên miền cần cập nhật cấu hình
            
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        pass

    def post_install(self, domain: str):
        """
        Hàm gọi sau khi cài đặt thành công.
        
        Phương thức này có thể được ghi đè bởi các lớp con để thực hiện
        các hành động bổ sung sau khi cài đặt.
        
        Args:
            domain (str): Tên miền đã cài đặt extension
            
        Returns:
            bool: True nếu các hành động sau cài đặt thành công, False nếu thất bại
        """
        return True