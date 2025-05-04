#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Định nghĩa giao diện IStorageProvider cho các nhà cung cấp lưu trữ sao lưu.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple


class IStorageProvider(ABC):
    """
    Giao diện cho các nhà cung cấp lưu trữ sao lưu.
    
    Định nghĩa các phương thức chuẩn mà tất cả các nhà cung cấp lưu trữ
    phải triển khai để đảm bảo tính nhất quán trong việc lưu trữ và
    truy xuất các bản sao lưu.
    """
    
    @abstractmethod
    def store_backup(self, website_name: str, backup_file_path: str) -> Tuple[bool, str]:
        """
        Lưu trữ tệp sao lưu.
        
        Args:
            website_name (str): Tên trang web
            backup_file_path (str): Đường dẫn đến tệp sao lưu
        
        Returns:
            Tuple[bool, str]: Tuple gồm (thành công, đường dẫn đích hoặc thông báo lỗi)
        """
        pass
    
    @abstractmethod
    def retrieve_backup(self, website_name: str, backup_name: str, destination_path: str) -> Tuple[bool, str]:
        """
        Truy xuất tệp sao lưu.
        
        Args:
            website_name (str): Tên trang web
            backup_name (str): Tên bản sao lưu cần truy xuất
            destination_path (str): Đường dẫn lưu trữ bản sao lưu truy xuất
        
        Returns:
            Tuple[bool, str]: Tuple gồm (thành công, đường dẫn tệp hoặc thông báo lỗi)
        """
        pass
    
    @abstractmethod
    def list_backups(self, website_name: Optional[str] = None) -> List[Dict]:
        """
        Liệt kê các bản sao lưu có sẵn.
        
        Args:
            website_name (Optional[str], optional): Lọc theo tên trang web. Mặc định là None.
        
        Returns:
            List[Dict]: Danh sách thông tin các bản sao lưu
        """
        pass
    
    @abstractmethod
    def delete_backup(self, website_name: str, backup_name: str) -> Tuple[bool, str]:
        """
        Xóa bản sao lưu.
        
        Args:
            website_name (str): Tên trang web
            backup_name (str): Tên bản sao lưu cần xóa
        
        Returns:
            Tuple[bool, str]: Tuple gồm (thành công, thông báo)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Lấy tên của nhà cung cấp lưu trữ này.
        
        Returns:
            str: Tên nhà cung cấp
        """
        pass